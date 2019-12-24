#!/usr/bin/env python3

import json
import configparser
import urllib.request
import os
import sys
import argparse
import traceback
import re
import logging

from subprocess import run, PIPE
from shlex import quote
from collections import namedtuple


API_URL_TEMPLATE = "https://api.github.com/repos/{0}/{1}/releases"
VER_FILE_NAME_TEMPLATE_SUBDIR = "{0}/{1}.json"
VER_FILE_NAME_TEMPLATE_NO_SUBDIR = ".{0}.{1}.json"

DEFAULT_OPTIONS = {
    "version_file_dir": None,
    "download_dir": ".",
    "use_subdir": False,
    "max_retry": 5,
    "verbose": False
}

OPTION_TYPES = {
    "version_file_dir": str,
    "download_dir": str,
    "use_subdir": bool,
    "regex_filter": str,
    "prerelease": bool,
    "post_download": str,
    "post_remove": str,
    "force": bool,
    "max_retry": int,
    "verbose": bool
}


AssetFile = namedtuple("AssetFile", "filename updated_at length")


class DownloadRepoRelease:

    def __call__(
            self, owner, repo,
            version_file_dir=DEFAULT_OPTIONS["version_file_dir"],
            download_dir=DEFAULT_OPTIONS["download_dir"],
            use_subdir=DEFAULT_OPTIONS["use_subdir"],
            regex_filter=None,
            prerelease=None,
            post_download=None,
            post_remove=None,
            force=False,
            max_retry=DEFAULT_OPTIONS["max_retry"],
            logger=logging.getLogger("github_release_dl")):

        self.owner = owner
        self.repo = repo
        self.version_file_dir = version_file_dir
        self.regex_filter = regex_filter
        self.prerelease = prerelease
        self.post_download = post_download
        self.post_remove = post_remove
        self.max_retry = max_retry
        self.logger = logger

        if use_subdir:
            ver_file_name_template = VER_FILE_NAME_TEMPLATE_SUBDIR
            self.download_dir = os.path.join(download_dir, repo[0], repo[1])
        else:
            ver_file_name_template = VER_FILE_NAME_TEMPLATE_NO_SUBDIR
            self.download_dir = download_dir
        os.makedirs(self.download_dir, 0o755, True)

        self.latest_version, self.release_files = self.get_release_files_list()
        self.files_needed = self.release_files.copy()
        logger.info(f"当前最新Release版本：{self.latest_version}")
        logger.debug(f"Release文件：{self.release_files}")

        if not version_file_dir:
            logger.debug("没有指定版本文件路径，将只下载文件。")
            self.download_files()
            return

        version_file_name = ver_file_name_template.format(owner, repo)
        self.version_file_path = os.path.join(version_file_dir,
                                              version_file_name)

        if force == True:
            logger.debug(f"已指定force，不读入本地版本文件。")
            local_files = []
            local_version = ""
        else:
            local_version, local_files = self.get_local_files_list()
            logger.info(f"当前本地版本：{local_version}")
            logger.debug(f"本地文件：{local_files}")
        

        self.files_to_remove = []
        need_update_version_file = False

        for url in list(self.files_needed.keys()):
            if self.files_needed[url] in local_files:
                filename = self.files_needed[url].filename
                filepath = os.path.join(self.download_dir, filename)
                length = self.files_needed[url].length
                logger.debug(f"本地版本文件中已有最新的{filename}的记录。")
                if not os.path.isfile(filepath):
                    logger.debug(f"> 本地实际不存在{filename}，需要下载。")
                elif os.path.getsize(filepath) != length:
                    logger.debug(f"> 本地实际{filename}长度不匹配，需要重新下载。")
                else:
                    logger.debug(f"> 本地文件{filename}看起来没有问题，无需下载。")
                    del self.files_needed[url]

        if self.files_needed:
            self.download_files()
            need_update_version_file = True
        else:
            logger.info("没有新的Release文件需要下载。")

        release_filenames = []
        for file in self.release_files.values():
            release_filenames.append(file.filename)

        for file in local_files:
            if file.filename not in release_filenames:
                self.files_to_remove.append(file)
                need_update_version_file = True

        if self.files_to_remove:
            self.remove_old_files()

        if need_update_version_file:
            self.update_version_file()

    def get_release_files_list(self):
        api_url = API_URL_TEMPLATE.format(self.owner, self.repo)
        response = self.try_function(urllib.request.urlopen, [api_url])
        if response.getcode() == 200:
            releases = json.loads(response.read())
        else:
            raise(f"API请求失败，返回：{response.getcode()}。")

        release = None
        for item in releases:
            if item["prerelease"] == self.prerelease or self.prerelease is None:
                release = item
                break
        if not release:
            raise Exception("没有找到符合要求的Release。")
        if "assets" not in release or not release["assets"]:
            raise Exception("Release中没有找到assets。")

        if self.regex_filter:
            pattern = re.compile(self.regex_filter)
        assets = {}
        for asset in release["assets"]:
            url = asset["browser_download_url"]
            filename = asset["name"]
            if self.regex_filter and not pattern.findall(filename):
                self.logger.debug(f"> 已排除：{filename}")
                continue
            asset_obj = AssetFile(
                filename=filename,
                updated_at=asset["updated_at"],
                length=asset["size"]
            )
            assets[url] = asset_obj
            self.logger.debug(f"> 已加入：{filename}")
        if not assets:
            raise Exception("没有任何符合过滤条件的文件。")
        return release["tag_name"], assets

    def get_local_files_list(self):
        local_version = None
        current_files = []
        if os.path.isfile(self.version_file_path):
            with open(self.version_file_path) as ver_file:
                local_version_json = json.load(ver_file)
            local_version = local_version_json["version"]
            for file in local_version_json["files"]:
                current_files.append(AssetFile(**file))
        return local_version, current_files

    def download_files(self):
        for url, file in self.files_needed.items():
            self.logger.info(f"下载：{url}")
            file_path = os.path.join(self.download_dir, file.filename)
            self.try_function(urllib.request.urlretrieve, [url, file_path])
            if self.post_download:
                self.exec_commands(self.post_download, file)

    def remove_old_files(self):
        for file in self.files_to_remove:
            file_pathname = os.path.join(self.download_dir, file.filename)
            self.logger.info(f"删除旧文件：{file_pathname}")
            if os.path.isfile(file_pathname):
                os.remove(file_pathname)
                if self.post_remove:
                    self.exec_commands(self.post_remove, file)
            else:
                self.logger.warning(f"未找到旧文件：{file_pathname}")

    def update_version_file(self):
        os.makedirs(os.path.dirname(self.version_file_path), 0o755, True)
        files = self.release_files.values()
        files_output = []
        for f in files:
            files_output.append(f._asdict())
        with open(self.version_file_path, "w") as ver_file:
            ver_file_data = {
                "version": self.latest_version,
                "files": files_output}
            json.dump(ver_file_data, ver_file)

    def try_function(self, function, params):
        for i in range(self.max_retry):
            try:
                return function(*params)
            except Exception as e:
                self.logger.warning(f"发生了错误：{e}。即将重试。")
                if i == self.max_retry - 1:
                    self.logger.error(f"达到最大重试次数（{max_retry}次）。")
                    raise e

    def exec_commands(self, cmd_template, file):
        cmd = cmd_template.format(
            filename=quote(file.filename),
            filedir=quote(self.download_dir),
            filepath=quote(os.path.join(self.download_dir, file.filename)),
            owner=quote(self.owner),
            repo=quote(self.repo),
            version=quote(self.latest_version))
        self.logger.debug(f"执行命令：{cmd}")
        result = run(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        if result.returncode != 0:
            self.logger.error(f"命令`{cmd}`返回{result.returncode}")
            self.logger.error(result.stderr.decode(sys.stdout.encoding))
            self.logger.debug(result.stdout.decode(sys.stdout.encoding))


download_repo_release = DownloadRepoRelease()


def get_arg_parser(no_additional_help=False):
    prerel_desp = \
        "\n&#9;- 默认不管是否是Prerelease，直接下载列表中最新的"
    cmd_desp = \
        "\n&#9;- 可插入的变量：`{filename}`、`{filedir}`、`{filepath}`、" \
        "`{owner}`、`{repo}`、`{version}`，分别代表文件名、文件所在目录、" \
        "文件路径、仓库所有者、仓库名、当前版本；路径均用相对于工作目录的相对路径表示"

    if no_additional_help:
        prerel_desp = cmd_desp = ""

    parser = argparse.ArgumentParser(description="获取GitHub仓库的Release的工具")
    parser.add_argument("repo", metavar="OWNER/REPO", nargs="?",
                        help="`所有者/仓库`的形式的仓库名（如果指定此参数，配置文件指定"
                        "的仓库列表及选项会被覆盖）")
    parser.add_argument("-r", "--regex-filter", metavar="REGEX",
                        help=f"用regex过滤文件名")
    parser.add_argument("--prerelease", action="store_true",
                        help=f"下载最新的Prerelease{prerel_desp}")
    parser.add_argument("--no-prerelease", action="store_true",
                        help=f"下载最新的非Prerelease{prerel_desp}")
    parser.add_argument("--post-download", metavar="COMMAND",
                        help=f"下载完成后执行的命令{cmd_desp}")
    parser.add_argument("--post-remove", metavar="COMMAND",
                        help=f"删除文件后执行的命令{cmd_desp}")
    parser.add_argument("-c", "--config", metavar="PATH",
                        help="配置文件路径")
    parser.add_argument("-v", "--version-file-dir", metavar="PATH",
                        help="版本文件存储路径（如果不指定此参数，默认不使用版本文件）")
    parser.add_argument("-d", "--download-dir", metavar="PATH",
                        help="下载路径（默认：当前工作目录）")
    parser.add_argument("--use-subdir", action="store_true",
                        help=f"使用子目录（用`所有者/仓库`的形式存放文件，默认不使用）")
    parser.add_argument("-f", "--force", action="store_true",
                        help=f"忽略当前版本文件，强制执行")
    parser.add_argument("--max-retry", metavar="N", type=int,
                        help=f"重试次数（默认：{DEFAULT_OPTIONS['max_retry']}）")
    parser.add_argument("--verbose", action="store_true",
                        help=f"显示调试输出")
    return parser


def main():
    parser = get_arg_parser(no_additional_help=True)
    parsed_args = vars(parser.parse_args())
    conf = configparser.ConfigParser()

    options = DEFAULT_OPTIONS

    parsed_conf = {}
    if parsed_args["config"] is not None:
        conf.read(parsed_args["config"])
        for conf_section in conf:
            parsed_conf[conf_section] = {}
            for key, val in conf[conf_section].items():
                if key in OPTION_TYPES:
                    if OPTION_TYPES[key] == str:
                        parsed_conf[conf_section][key] = val
                    elif OPTION_TYPES[key] == int:
                        parsed_conf[conf_section][key] = int(val)
                    elif OPTION_TYPES[key] == bool:
                        parsed_conf[conf_section][key] = \
                            conf.getboolean(conf_section, key)
                else:
                    raise Exception(f"未知配置选项：{key}")
        options.update(parsed_conf["DEFAULT"])
        del parsed_conf["DEFAULT"]
    del parsed_args["config"]

    prerelease = None
    if parsed_args["prerelease"]:
        prerelease = True
        del parsed_args["prerelease"]
    if parsed_args["no_prerelease"]:
        if prerelease == True:
            raise Exception(f"不能同时指定--prerelease和--no-prerelease。")
        prerelease = False
    del parsed_args["no_prerelease"]
    del parsed_args["prerelease"]

    if parsed_args["repo"]:
        repositories = {
            parsed_args["repo"]: {}
        }
        del parsed_args["repo"]
    else:
        repositories = parsed_conf

    for key, val in parsed_args.copy().items():
        if val is None:
            del parsed_args[key]

    options.update(parsed_args)

    logging.basicConfig(
        format="%(levelname)-6s %(message)s",
        level=logging.DEBUG if options["verbose"] else logging.INFO
    )
    del options["verbose"]

    if not repositories:
        logging.error("没有指定任何仓库。\n")
        parser.print_help()
        exit(-1)

    for repo_identifier, repo_options in repositories.items():
        logging.info(f"处理：{repo_identifier}")
        repo_options_merged = options.copy()
        repo_options_merged.update(repo_options)
        try:
            owner, repo = repo_identifier.split("/")
            download_repo_release(
                owner=owner,
                repo=repo,
                logger=logging,
                **repo_options_merged
            )
        except Exception as e:
            logging.error(f"发生了错误：{e}")
            logging.debug(traceback.format_exc())

    logging.info("完成。")


if __name__ == "__main__":
    main()
