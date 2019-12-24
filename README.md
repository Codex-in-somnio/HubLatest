# HubLatest

用来获取GitHub仓库的Release的脚本。

## 环境要求


* 需要Python 3.6及以上。

## 命令行用法

```
usage: ./hublatest.py [-h] [-r REGEX] [--prerelease] [--no-prerelease]
                      [--post-download COMMAND] [--post-remove COMMAND]
                      [-c PATH] [-v PATH] [-d PATH] [--use-subdir] [-f]
                      [--max-retry N] [--verbose]
                      [OWNER/REPO]
```

### Positional Arguments

*  **`OWNER/REPO`**

   `所有者/仓库`的形式的仓库名（如果指定此参数，配置文件指定的仓库列表及选项会被覆盖）

### Named Arguments

*  **`-r, --regex-filter`**

   用regex过滤文件名

*  **`--prerelease`**

   下载最新的Prerelease
	- 默认不管是否是Prerelease，直接下载列表中最新的

*  **`--no-prerelease`**

   下载最新的非Prerelease
	- 默认不管是否是Prerelease，直接下载列表中最新的

*  **`--post-download`**

   下载完成后执行的命令
	- 可插入的变量：`{filename}`、`{filedir}`、`{filepath}`、`{owner}`、`{repo}`、`{version}`，分别代表文件名、文件所在目录、文件路径、仓库所有者、仓库名、当前版本；路径均用相对于工作目录的相对路径表示

*  **`--post-remove`**

   删除文件后执行的命令
	- 可插入的变量：`{filename}`、`{filedir}`、`{filepath}`、`{owner}`、`{repo}`、`{version}`，分别代表文件名、文件所在目录、文件路径、仓库所有者、仓库名、当前版本；路径均用相对于工作目录的相对路径表示

*  **`-c, --config`**

   配置文件路径

*  **`-v, --version-file-dir`**

   版本文件存储路径（如果不指定此参数，默认不使用版本文件）

*  **`-d, --download-dir`**

   下载路径（默认：当前工作目录）

*  **`--use-subdir`**

   使用子目录（用`所有者/仓库`的形式存放文件，默认不使用）

*  **`-f, --force`**

   忽略当前版本文件，强制执行

*  **`--max-retry`**

   重试次数（默认：5）

*  **`--verbose`**

   显示调试输出

## 配置文件用法

配置文件为INI格式，以下是配置文件的例子：

```
[DEFAULT]
version_file_dir = version_files
download_dir = download_files
use_subdir = false

[k9yyy/dead_by_unicode_gui]
regex_filter = zip
prerelease = false
post_download = unzip {filepath} -d {filedir}

[k9yyy/ThreadCutter]
regex_filter= zip$
prerelease = true
```

用法例如：

```
./hublatest.py -c config.ini
```

一些说明：


* `[DEFAULT]` 下的选项会应用于所有仓库


* 各仓库用形如 `[所有者/仓库名]` 的小节标题表示，针对单个仓库的选项可以指定它对应的小节标题下；如果不需要指定任何参数，可以放一个空的小节


* 配置文件中的设置项意义参见命令行参数的用法


* `prerelease` 这一项给 `true` 是 `--prerelease` 的效果；给 `false` 是 `--no-prerelease` 的效果


* 可以仅指定部分项目的值（省略的会使用默认值）


* 使用配置文件后，仍可以用命令行参数覆盖配置文件中所写的设置项
