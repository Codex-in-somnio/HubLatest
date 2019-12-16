# github_release_dl

用来获取GitHub仓库的Release的脚本。

## 环境要求


* 需要Python 3.5及以上。

## 命令行用法

```
usage: ./github_release_dl.py [-h] [-c PATH] [-v PATH] [-d PATH]
                              [--use-subdir] [-r OWNER/REPO[:REGEX]
                              [OWNER/REPO[:REGEX] ...]] [--max-retry N]
                              [--verbose]
```

### Named Arguments

*  **`-c, --config`**

   配置文件路径

*  **`-v, --version-file-dir`**

   版本文件存储路径（默认：当前工作目录）

*  **`-d, --download-dir`**

   下载路径（默认：当前工作目录）

*  **`--use-subdir`**

   使用子目录（用`所有者/仓库`的形式存放文件，默认不使用）

*  **`-r, --repo-list`**

   仓库列表（仓库名后面可接`:regex`过滤文件名，不写则不过滤）

*  **`--max-retry`**

   重试次数（默认：5）

*  **`--verbose`**

   显示调试输出

## 配置文件用法

配置文件为JSON格式，以下是配置文件的例子：

```
{
    "version_file_dir": "version_files",
    "download_dir": "download_files",
    "repo_list": [
        "k9yyy/dead_by_unicode_gui:.*\\.zip$"
    ],
    "use_subdir": false,
    "max_retry": 3
}
```

用法例如：

```
./github_release_dl.py -c config.json
```

一些说明：


* 配置文件中的设置项意义参见命令行参数的用法；


* 可以仅指定部分项目的值（省略的会使用默认值）；


* 使用配置文件后，仍可以用命令行参数覆盖配置文件中所写的设置项。
