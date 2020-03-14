# HubLatest

Script for retrieving latest releases from GitHub repositories.

## Requirements


* Python 3.6 and above

## Commandline options

```
usage: hublatest [-h] [-r REGEX] [--prerelease] [--no-prerelease]
                 [--post-download COMMAND] [--post-remove COMMAND] [-c PATH]
                 [-v PATH] [-d PATH] [--use-subdir] [-f] [--max-retry N]
                 [--verbose]
                 [OWNER/REPO]
```

### Positional Arguments

*  **`OWNER/REPO`**

   Repo identifier in format of `owner/repo` (if this option is specified, the repo list in config file will be overridden)

### Named Arguments

*  **`-r, --regex-filter`**

   Filter filenames by regex

*  **`--prerelease`**

   Get the latest prerelease
	- By default, the newest release will be downloaded, regardless of prerelease or not

*  **`--no-prerelease`**

   Get the latest non-prerelease
	- By default, the newest release will be downloaded, regardless of prerelease or not

*  **`--post-download`**

   Command to be executed after each file is downloaded
	- Variables can be inserted: `{filename}`, `{filedir}`, `{filepath}`, `{owner}`, `{repo}`, `{version}`; meaning filename, containing directory of the file, file path, repo owner, repo name, current version; all paths are relative to the work directory

*  **`--post-remove`**

   Command to be executed after each file is removed
	- Variables can be inserted: `{filename}`, `{filedir}`, `{filepath}`, `{owner}`, `{repo}`, `{version}`; meaning filename, containing directory of the file, file path, repo owner, repo name, current version; all paths are relative to the work directory

*  **`-c, --config`**

   Path to the config file

*  **`-v, --version-file-dir`**

   Directory to put version files (if not specified, version files will not be used)

*  **`-d, --download-dir`**

   Directory to put downloaded files (Default is current working directory)

*  **`--use-subdir`**

   Save files to sub-directories like `owner/repo` (no sub-directories by default)

*  **`-f, --force`**

   Ignore current version file(s) and forcibly execute

*  **`--max-retry`**

   Max retry attemps (default: 5)

*  **`--verbose`**

   Show debug output

## Config file

Config file is in INI format. Example:

```
## Settings under here applies to all downloads by default
[DEFAULT]

# Put versions under `./version_files/`
version_file_dir = ./version_files

# Download files to `./download_files/`
download_dir = ./download_files

# Use directory structure like `owner/repo/`
use_subdir = true


## Release files of `some_repo/some_project` will be downloaded
[some_repo/some_project]

# only download zip files
regex_filter = .zip$

# no prereleases
prerelease = false

# extract after download
post_download = unzip {filepath} -d {filedir}/extracted_files

# delete extracted files when old version is removed
post_delete = rm -r {filedir}/extracted_files
```

Usage:

```
hublatest -c config.ini
```

Notes:


* Options set under `[DEFAULT]` are glocal and will be applied by default


* Options set under `[DEFAULT]` can be overriden by commandline options or options


* Add sections named like `[owner/repo]` to auto-download release files from a list of repositories when no repositories are specified from commandline; if no specific options are needed for a repository, its section can be left empty


* Refer to the commandline option usages for the config options


* `prerelease = true` means `--prerelease`; `prerelease = false` means `--no-prerelease`


---

（中文版说明）

用来获取GitHub仓库的Release的脚本。

## 环境要求


* 需要Python 3.6及以上。

## 命令行用法

```
usage: hublatest [-h] [-r REGEX] [--prerelease] [--no-prerelease]
                 [--post-download COMMAND] [--post-remove COMMAND] [-c PATH]
                 [-v PATH] [-d PATH] [--use-subdir] [-f] [--max-retry N]
                 [--verbose]
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

   版本文件存放目录（如果不指定此参数，默认不使用版本文件）

*  **`-d, --download-dir`**

   下载目标目录（默认：当前工作目录）

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
## 这下面的设置会默认应用于所有的下载
[DEFAULT]

# 指定将版本文件放在`./version_files/`下
version_file_dir = ./version_files

# 指定下载文件至`./download_files/`下
download_dir = ./download_files

# 使用形如`owner/repo/`的子目录形式
use_subdir = true


## 下载仓库`some_repo/some_project`的Release文件
[some_repo/some_project]

# 只下载zip文件
regex_filter = .zip$

# 不下载Prerelease
prerelease = false

# 下载完成后解压
post_download = unzip {filepath} -d {filedir}/extracted_files

# 在删除旧版本时删除之前解压出来的文件
post_delete = rm -r {filedir}/extracted_files
```

用法例如：

```
hublatest -c config.ini
```

一些说明：


* `[DEFAULT]` 下的选项会应用于所有仓库


* 可以用命令行参数覆盖 `[DEFAULT]` 中所写的设置项


* 要下载Release的各仓库用形如 `[所有者/仓库名]` 的小节标题表示，针对单个仓库的选项可以指定它对应的小节标题下；如果不需要指定任何参数，可以放一个空的小节


* 配置文件中的设置项意义参见命令行参数的用法


* `prerelease` 这一项给 `true` 是 `--prerelease` 的效果；给 `false` 是 `--no-prerelease` 的效果
