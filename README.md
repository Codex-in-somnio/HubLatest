# github_release_dl

用来获取GitHub仓库的Release的脚本。

## 环境要求


* 需要Python 3.5及以上。

## 命令行用法

```
usage: ./github_release_dl.py [-h] [-f REGEX] [--prerelease] [--no-prerelease]
                              [--post-download COMMAND]
                              [--post-remove COMMAND] [-c PATH] [-v PATH]
                              [-d PATH] [--use-subdir] [--max-retry N]
                              [--verbose]
                              [OWNER/REPO]
```

### Positional Arguments

*  **`OWNER/REPO`**

   `所有者/仓库`的形式的仓库名（如果指定此参数，配置文件指定的仓库列表及选项会被覆盖）

### Named Arguments

*  **`-f, --regex-filter`**

   用regex过滤文件名
	- 通过命令行指定此参数时，此参数仅对命令行参数指定的仓库生效

*  **`--prerelease`**

   下载最新的Prerelease
	- 通过命令行指定此参数时，此参数仅对命令行参数指定的仓库生效
	- 默认不管是否是Prerelease，直接下载列表中最新的

*  **`--no-prerelease`**

   下载最新的非Prerelease
	- 通过命令行指定此参数时，此参数仅对命令行参数指定的仓库生效
	- 默认不管是否是Prerelease，直接下载列表中最新的

*  **`--post-download`**

   下载完成后执行的命令
	- 通过命令行指定此参数时，此参数仅对命令行参数指定的仓库生效
	- 可插入的变量：`{{filename}}`、`{{filedir}}`、`{{filepath}}`、`{{owner}}`、`{{repo}}、{{version}}`,分别代表文件名、文件所在目录、文件路径、仓库所有者、仓库名、当前版本；路径均用相对于工作目录的相对路径表示

*  **`--post-remove`**

   删除文件后执行的命令
	- 通过命令行指定此参数时，此参数仅对命令行参数指定的仓库生效
	- 可插入的变量：`{{filename}}`、`{{filedir}}`、`{{filepath}}`、`{{owner}}`、`{{repo}}、{{version}}`,分别代表文件名、文件所在目录、文件路径、仓库所有者、仓库名、当前版本；路径均用相对于工作目录的相对路径表示

*  **`-c, --config`**

   配置文件路径

*  **`-v, --version-file-dir`**

   版本文件存储路径（如果不指定此参数，默认不使用版本文件）

*  **`-d, --download-dir`**

   下载路径（默认：当前工作目录）

*  **`--use-subdir`**

   使用子目录（用`所有者/仓库`的形式存放文件，默认不使用）

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
    "repositories": {
        "k9yyy/dead_by_unicode_gui": {
            "regex_filter": "zip$",
            "prerelease": false
        },
        "k9yyy/ThreadCutter": {
            "regex_filter": "zip$",
            "prerelease": true
        }
    },
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
