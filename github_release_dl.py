#!/usr/bin/env python3

import json
import urllib.request
import os
import sys
import argparse
import traceback
import re
import logging

from collections import namedtuple


API_URL_TEMPLATE = "https://api.github.com/repos/{0}/{1}/releases/latest"
VER_FILE_NAME_TEMPLATE_SUBDIR = "{0}/{1}.json"
VER_FILE_NAME_TEMPLATE_NO_SUBDIR = ".{0}.{1}.json"


DEFAULT_OPTIONS = {
    "version_file_dir": ".",
    "download_dir": ".",
    "use_subdir": False,
    "repo_list": [],
    "use_subdir": False,
    "max_retry": 5
}


AssetFile = namedtuple("AssetFile", "filename updated_at length")


class DownloadRepoRelease:

    def __call__(
            self, owner, repo,
            version_file_dir=DEFAULT_OPTIONS["version_file_dir"],
            download_dir=DEFAULT_OPTIONS["download_dir"],
            use_subdir=DEFAULT_OPTIONS["use_subdir"],
            filter_regex=None,
            max_retry=DEFAULT_OPTIONS["max_retry"],
            logger=logging.getLogger("github_release_dl")):

        self.owner = owner
        self.repo = repo
        self.version_file_dir = version_file_dir
        self.filter_regex = filter_regex
        self.max_retry = max_retry
        self.logger = logger

        if use_subdir:
            ver_file_name_template = VER_FILE_NAME_TEMPLATE_SUBDIR
            self.download_dir = os.path.join(download_dir, repo[0], repo[1])
        else:
            ver_file_name_template = VER_FILE_NAME_TEMPLATE_NO_SUBDIR
            self.download_dir = download_dir
        os.makedirs(self.download_dir, 0o755, True)

        version_file_name = ver_file_name_template.format(owner, repo)
        self.version_file_path = os.path.join(version_file_dir,
                                              version_file_name)

        self.latest_version, self.release_files = self.get_release_files_list()
        self.files_needed = self.release_files.copy()
        logger.info(f"当前最新Release版本：{self.latest_version}")
        logger.debug(f"Release文件：{self.release_files}")

        local_version, self.local_files = self.get_local_files_list()
        logger.info(f"当前本地版本：{local_version}")
        logger.debug(f"本地文件：{self.local_files}")

        self.files_to_remove = []
        need_update_version_file = False

        for url in list(self.files_needed.keys()):
            if self.files_needed[url] in self.local_files:
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

        for file in self.local_files:
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
            parsed_response = json.loads(response.read())
        else:
            raise(f"API请求失败，返回：{response.getcode()}。")

        if self.filter_regex:
            pattern = re.compile(self.filter_regex)
        if "assets" in parsed_response and parsed_response["assets"]:
            assets = {}
            for asset in parsed_response["assets"]:
                url = asset["browser_download_url"]
                filename = asset["name"]
                if self.filter_regex and not pattern.findall(filename):
                    self.logger.debug(f"> 已排除：{filename}")
                    continue
                asset_obj = AssetFile(
                    filename=filename,
                    updated_at=asset["updated_at"],
                    length=asset["size"]
                )
                assets[url] = asset_obj
                self.logger.debug(f"> 已加入：{filename}")
            return parsed_response["tag_name"], assets
        else:
            raise Exception("没有找到assets。")

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
            self.try_function(urllib.request.urlretrieve,
                              [url, file_path])

    def remove_old_files(self):
        for file in self.files_to_remove:
            file_pathname = os.path.join(self.download_dir, file.filename)
            self.logger.info(f"删除旧文件：{file_pathname}")
            if os.path.isfile(file_pathname):
                os.remove(file_pathname)
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


download_repo_release = DownloadRepoRelease()


def get_arg_parser():
    parser = argparse.ArgumentParser(description="批量获取GitHub仓库的Release")
    parser.add_argument("-c", "--config", metavar="PATH",
                        help="配置文件路径")
    parser.add_argument("-v", "--version-file-dir", metavar="PATH",
                        help="版本文件存储路径（默认：当前工作目录）")
    parser.add_argument("-d", "--download-dir", metavar="PATH",
                        help="下载路径（默认：当前工作目录）")
    parser.add_argument("--use-subdir", action="store_true",
                        help=f"使用子目录（用`所有者/仓库`的形式存放文件，默认不使用）")
    parser.add_argument("-r", "--repo-list",
                        metavar="OWNER/REPO[:REGEX]", nargs="+",
                        help="仓库列表（仓库名后面可接`:regex`过滤文件名，不写则不过滤）")
    parser.add_argument("--max-retry", metavar="N", type=int,
                        help=f"重试次数（默认：{DEFAULT_OPTIONS['max_retry']}）")
    parser.add_argument("--verbose", action="store_true",
                        help=f"显示调试输出")
    return parser


def main():
    parser = get_arg_parser()
    parsed_args = vars(parser.parse_args())

    options = DEFAULT_OPTIONS
    if parsed_args["config"] is not None:
        with open(parsed_args["config"]) as conf_file:
            options.update(json.load(conf_file))
    del parsed_args["config"]
    for option, value in parsed_args.items():
        if parsed_args[option] is not None:
            options[option] = parsed_args[option]
    if not options["repo_list"]:
        print("没有指定任何仓库。\n", file=sys.stderr)
        parser.print_help()
        exit(-1)

    logging.basicConfig(
        format="%(levelname)-6s %(message)s",
        level=logging.DEBUG if options["verbose"] else logging.INFO
    )

    for repo_option in options["repo_list"]:
        logging.info(f"处理：{repo_option}")
        try:
            regex = None
            # 过滤用的regex用:跟在repo后面表示，先看有没有指定regex
            if ":" in repo_option:
                repo_option = repo_option.split(":", 1)
                regex = repo_option[1]
                repo_option = repo_option[0]

            owner, repo = repo_option.split("/")

            download_repo_release(
                owner=owner,
                repo=repo,
                version_file_dir=options["version_file_dir"],
                download_dir=options["download_dir"],
                use_subdir=options["use_subdir"],
                filter_regex=regex,
                max_retry=options["max_retry"],
                logger=logging
            )
        except Exception as e:
            logging.error(f"发生了错误：{e}")
            logging.debug(traceback.format_exc())

    logging.info("完成。")


if __name__ == "__main__":
    main()
