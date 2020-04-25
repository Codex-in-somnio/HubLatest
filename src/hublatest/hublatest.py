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
import gettext

from subprocess import run, PIPE
from shlex import quote
from collections import namedtuple
from .file_download import file_download


translation = gettext.translation(
    "messages",
    os.path.join(os.path.dirname(__file__), "locale"),
    fallback=True)
_ = translation.gettext


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
            self.download_dir = os.path.join(download_dir, owner, repo)
        else:
            ver_file_name_template = VER_FILE_NAME_TEMPLATE_NO_SUBDIR
            self.download_dir = download_dir
        os.makedirs(self.download_dir, 0o755, True)

        self.latest_version, self.release_files = self.get_release_files_list()
        self.files_needed = self.release_files.copy()
        logger.info(
            _("Current newest release version: {}").format(self.latest_version))
        logger.debug(_("Release assets: {}").format(self.release_files))

        if not version_file_dir:
            logger.debug(
                _("No --version-file-dir specified, will download only."))
            self.download_files()
            return

        version_file_name = ver_file_name_template.format(owner, repo)
        self.version_file_path = os.path.join(version_file_dir,
                                              version_file_name)

        if force == True:
            logger.debug(_("--force specified, ignoring version file."))
            local_files = []
            local_version = ""
        else:
            local_version, local_files = self.get_local_files_list()
            logger.info(_("Current local version: {}").format(local_version))
            logger.debug(_("Local assets: {}").format(local_files))

        self.local_version = local_version
        self.files_to_remove = []
        need_update_version_file = False

        for url in list(self.files_needed.keys()):
            if self.files_needed[url] in local_files:
                filename = self.files_needed[url].filename
                filepath = os.path.join(self.download_dir, filename)
                length = self.files_needed[url].length
                logger.debug(
                    _("Found latest record of {} from local version "
                      "file.").format(filename))
                if not os.path.isfile(filepath):
                    logger.debug(
                        "> " + _("{} not found, will be downloaded.").format(
                            filename))
                elif os.path.getsize(filepath) != length:
                    logger.debug(
                        "> " + _("The local copy of {} has wrong length, will "
                                 "be re-downloaded.").format(filename))
                else:
                    logger.debug(
                        "> " + _("The local copy of {} looks fine, no need to"
                                 " download.").format(filename))
                    del self.files_needed[url]

        if self.files_needed:
            self.download_files()
            need_update_version_file = True
        else:
            logger.info(_("No new releases need to be downloaded."))

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
            raise(_("API request failed, returned: {}.").format(
                response.getcode()))

        release = None
        for item in releases:
            if item["prerelease"] == self.prerelease or self.prerelease is None:
                release = item
                break
        if not release:
            raise Exception(_("No suitable releases found."))
        if "assets" not in release or not release["assets"]:
            raise Exception(_("No assets in release."))

        if self.regex_filter:
            pattern = re.compile(self.regex_filter)
        assets = {}
        for asset in release["assets"]:
            url = asset["browser_download_url"]
            filename = asset["name"]
            if self.regex_filter and not pattern.findall(filename):
                self.logger.debug("> " + _("Excluded {}").format(filename))
                continue
            asset_obj = AssetFile(
                filename=filename,
                updated_at=asset["updated_at"],
                length=asset["size"]
            )
            assets[url] = asset_obj
            self.logger.debug("> " + _("Added {}").format(filename))
        if not assets:
            raise Exception(_("No files matched the regex filter."))
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
            self.logger.info(_("Downloading: {}").format(url))
            file_path = os.path.join(self.download_dir, file.filename)
            self.try_function(file_download, [url, file_path])
            if self.post_download:
                self.exec_commands(self.post_download, file)

    def remove_old_files(self):
        for file in self.files_to_remove:
            file_pathname = os.path.join(self.download_dir, file.filename)
            self.logger.info(_("Removing old file: {}").format(file_pathname))
            if os.path.isfile(file_pathname):
                os.remove(file_pathname)
                if self.post_remove:
                    self.exec_commands(self.post_remove, file, is_remove=True)
            else:
                self.logger.warning(
                    _("Old file not found: {}").format(file_pathname))

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
                self.logger.warning(
                    _("Error occured: {}. Retrying.").format(e))
                if i == self.max_retry - 1:
                    self.logger.error(
                        _("Max retry attemps reached. ({} times).").format(
                            self.max_retry))
                    raise e

    def exec_commands(self, cmd_template, file, is_remove=False):
        cmd = cmd_template.format(
            filename=quote(file.filename),
            filedir=quote(self.download_dir),
            filepath=quote(os.path.join(self.download_dir, file.filename)),
            owner=quote(self.owner),
            repo=quote(self.repo),
            version=quote(self.local_version if is_remove else
                          self.latest_version))
        self.logger.debug(_("Executing command: {}").format(cmd))
        result = run(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        if result.returncode != 0:
            self.logger.error(
                _("Command `{0}` returned {1}.").format(cmd, result.returncode))
            self.logger.error(result.stderr.decode(sys.stdout.encoding))
            self.logger.debug(result.stdout.decode(sys.stdout.encoding))


download_repo_release = DownloadRepoRelease()


def get_arg_parser(no_additional_help=False):
    prerel_desp = \
        "\n&#9;- " + \
        _("By default, the newest release will be downloaded, regardless of "
          "prerelease or not")
    cmd_desp = \
        "\n&#9;- " + \
        _("Variables can be inserted: `{filename}`, `{filedir}`, `{filepath}`, "
          "`{owner}`, `{repo}`, `{version}`; meaning filename, containing "
          "directory of the file, file path, repo owner, repo name, current "
          "version; all paths are relative to the work directory")

    if no_additional_help:
        prerel_desp = cmd_desp = ""

    parser = argparse.ArgumentParser(
        description="Script to get latest release from GitHub repositories")
    parser.add_argument("repo", metavar="OWNER/REPO", nargs="?",
                        help=_("Repo identifier in format of `owner/repo` "
                               "(if this option is specified, the repo list in "
                               "config file will be overridden)"))
    parser.add_argument("-r", "--regex-filter", metavar="REGEX",
                        help=_("Filter filenames by regex"))
    parser.add_argument("--prerelease", action="store_true",
                        help=_("Get the latest prerelease") + prerel_desp)
    parser.add_argument("--no-prerelease", action="store_true",
                        help=_("Get the latest non-prerelease") + prerel_desp)
    parser.add_argument("--post-download", metavar="COMMAND",
                        help=_("Command to be executed after each file is "
                               "downloaded") + cmd_desp)
    parser.add_argument("--post-remove", metavar="COMMAND",
                        help=_("Command to be executed after each file is "
                               "removed") + cmd_desp)
    parser.add_argument("-c", "--config", metavar="PATH",
                        help=_("Path to the config file"))
    parser.add_argument("-v", "--version-file-dir", metavar="PATH",
                        help=_("Directory to put version files (if not "
                               "specified, version files will not be used)"))
    parser.add_argument("-d", "--download-dir", metavar="PATH",
                        help=_("Directory to put downloaded files (Default is "
                               "current working directory)"))
    parser.add_argument("--use-subdir", action="store_true",
                        help=_("Save files to sub-directories like "
                               "`owner/repo` (no sub-directories by default)"))
    parser.add_argument("-f", "--force", action="store_true",
                        help=_("Ignore current version file(s) and forcibly "
                               "execute"))
    parser.add_argument("--max-retry", metavar="N", type=int,
                        help=_("Max retry attemps (default: {})").format(
                            DEFAULT_OPTIONS['max_retry']))
    parser.add_argument("--verbose", action="store_true",
                        help=_("Show debug output"))
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
                    logging.error(_("Unknown config option: {}").format(key))
                    return -1
        options.update(parsed_conf["DEFAULT"])
        del parsed_conf["DEFAULT"]
    del parsed_args["config"]

    prerelease = None
    if parsed_args["prerelease"]:
        prerelease = True
    if parsed_args["no_prerelease"]:
        if prerelease == True:
            logging.error(
                _("`--prerelease` and `--no-prerelease` cannot be specified at "
                  "the same time."))
            return -1
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
        logging.error(_("No repositories specified.") + "\n")
        parser.print_help()
        return -1

    ret_code = 0
    for repo_identifier, repo_options in repositories.items():
        logging.info(_("Processing: {}".format(repo_identifier)))
        repo_options_merged = options.copy()
        repo_options_merged.update(repo_options)
        try:
            splited_identifier = repo_identifier.split("/")
            if len(splited_identifier) != 2:
                raise Exception(
                    _("Repo identifier must be in format of `repo/owner` "
                      "(Erroneous input: {})").format(repo_identifier))
            owner, repo = splited_identifier
            download_repo_release(
                owner=owner,
                repo=repo,
                logger=logging,
                **repo_options_merged
            )
        except Exception as e:
            logging.warning(_("Error occurred: {}").format(e))
            logging.debug(traceback.format_exc())
            ret_code = -1

    logging.info(_("Finished.") if ret_code == 0 else _("Partially finished."))
    return ret_code


if __name__ == "__main__":
    sys.exit(main())
