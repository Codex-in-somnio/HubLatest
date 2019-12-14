#!/usr/bin/env python3

import json
import urllib.request
import os
import argparse
import traceback
import re


API_URL_TEMPLATE = "https://api.github.com/repos/{0}/{1}/releases/latest"
VERSION_FILE_NAME_TEMPLATE = "{0}/{1}.json"


def check_api(repo):
    api_url = API_URL_TEMPLATE.format(repo[0], repo[1])
    response = urllib.request.urlopen(api_url)
    if response.getcode() == 200:
        parsed_response = json.loads(response.read())
    else:
        raise(f"API请求失败，返回：{response.getcode()}。")

    latest_version = parsed_response["tag_name"]
    if "assets" in parsed_response and parsed_response["assets"]:
        assets = {}
        for asset in parsed_response["assets"]:
            url = asset["browser_download_url"]
            filename = asset["name"]
            assets[url] = filename
        return latest_version, assets
    else:
        raise Exception("没有找到assets。")


def get_version_file_pathname(repo, version_file_dir):
    version_file_name = VERSION_FILE_NAME_TEMPLATE.format(repo[0], repo[1])
    return os.path.join(version_file_dir, version_file_name)


def get_local_version(repo, version_file_dir):
    version_file_name = get_version_file_pathname(repo, version_file_dir)
    local_version = None
    current_files = set()
    if os.path.isfile(version_file_name):
        with open(version_file_name) as ver_file:
            local_version_json = json.load(ver_file)
        local_version = local_version_json["version"]
        current_files = set(local_version_json["files"])
    return local_version, current_files


def download_assets(assets, download_file_dir, max_retry):
    downloaded_files = set()
    for url, filename in assets.items():
        print(f"下载：{url}")
        file_path = os.path.join(download_file_dir, filename)
        try_function(urllib.request.urlretrieve, [url, file_path], max_retry)
        downloaded_files.add(filename)
    return downloaded_files


def remove_old_files(files, download_file_dir):
    for filename in files:
        file_pathname = os.path.join(download_file_dir, filename)
        if os.path.isfile(file_pathname):
            print(f"删除旧文件：{file_pathname}")
            os.remove(file_pathname)
        else:
            print(f"未找到旧文件：{file_pathname}。")


def update_version_file(repo, version, files, version_file_dir):
    version_file_pathname = get_version_file_pathname(repo, version_file_dir)
    os.makedirs(os.path.dirname(version_file_pathname), 0o755, True)
    with open(version_file_pathname, "w") as ver_file:
        ver_file_data = {"version": version, "files": list(files)}
        json.dump(ver_file_data, ver_file)


def try_function(function, params, max_retry):
    for i in range(max_retry):
        try:
            return function(*params)
        except Exception as e:
            print(f"发生了错误：{e}。即将重试。")
            if i == max_retry - 1:
                print(f"达到最大重试次数（{max_retry}次）。")
                raise e


def filter_download_files_list(download_files_list, regex):
    pattern = re.compile(regex)
    matched = {}
    for url, filename in download_files_list.items():
        if pattern.match(filename):
            matched[url] = filename
    return matched


def update_repo(repo, version_file_dir, download_dir, filter_regex, max_retry):
    latest_version, assets = try_function(check_api, [repo], max_retry)
    local_version, local_files = get_local_version(repo, version_file_dir)

    download_file_dir = os.path.join(download_dir, repo[0], repo[1])
    os.makedirs(download_file_dir, 0o755, True)

    filtered_download_list = filter_download_files_list(assets, filter_regex)

    files_to_remove = set()
    need_update_version_file = False
    if local_version != latest_version:
        print(f"发现更新版本：{latest_version}，即将下载。")
        downloaded_files = download_assets(
            filtered_download_list, download_file_dir, max_retry)
        for filename in local_files:
            if filename not in downloaded_files:
                files_to_remove.add(filename)
        need_update_version_file = True
    else:
        print(f"当前本地的{local_version}已经是最新版本。")

        # 下面处理万一filter改变导致需要的文件变化的情况
        files_needed = {}
        for url, filename in filtered_download_list.items():
            if filename not in local_files:
                files_needed[url] = filename
        if files_needed:
            download_assets(files_needed, download_file_dir, max_retry)
            need_update_version_file = True
        for filename in local_files:
            if filename not in filtered_download_list.values():
                files_to_remove.add(filename)
                need_update_version_file = True

    if files_to_remove:
        remove_old_files(files_to_remove, download_file_dir)
    if need_update_version_file:
        update_version_file(repo,
                            latest_version,
                            filtered_download_list.values(),
                            version_file_dir)

def get_arg_parser():
    parser = argparse.ArgumentParser(description="批量获取GitHub仓库的Release")
    parser.add_argument("-c", "--config", metavar="PATH",
                        help="配置文件路径")
    parser.add_argument("-e", "--version-file-dir", metavar="PATH",
                        help="版本文件存储路径")
    parser.add_argument("-d", "--download-dir", metavar="PATH",
                        help="下载路径")
    parser.add_argument("-r", "--repo-list", metavar="OWNER/REPO", nargs="+",
                        help="仓库列表")
    parser.add_argument("-f", "--filter", metavar="REGEX",
                        help="过滤文件名")
    parser.add_argument("--max-retry", metavar="N", type=int,
                        help="重试次数")
    return parser

def main():
    default_options = {
        "version_file_dir": "",
        "download_dir": "",
        "repo_list": [],
        "filter": ".*",
        "max_retry": 5
    }
    
    parser = get_arg_parser()
    parsed_args = vars(parser.parse_args())

    options = default_options
    if parsed_args["config"] is not None:
        with open(parsed_args["config"]) as conf_file:
            options.update(json.load(conf_file))
    del parsed_args["config"]
    for option, value in parsed_args.items():
        if parsed_args[option] is not None:
            options[option] = parsed_args[option]
    if not options["repo_list"]:
        print("没有指定任何仓库。\n")
        parser.print_help()
        exit(-1)

    for repo in options["repo_list"]:
        print(f"处理：{repo}")
        repo = repo.split("/")
        try:
            update_repo(repo,
                        options["version_file_dir"],
                        options["download_dir"],
                        options["filter"],
                        options["max_retry"])
        except Exception as e:
            print(f"发生了错误：{e}")
            print(traceback.format_exc())

    print("完成。")


if __name__ == "__main__":
    main()
