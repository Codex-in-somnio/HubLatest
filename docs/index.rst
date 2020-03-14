HubLatest
=========

Script for retrieving latest releases from GitHub repositories.

Requirements
************

* Python 3.6 and above

Commandline options:

.. argparse::
  :filename: ./get_arg_parser.py
  :func: get_arg_parser_en
  :prog: hublatest
  :nodescription:
  :nodefault:
  :markdownhelp:

Config file
***********

Config file is in INI format. Example:

.. include:: ./config_example.ini
   :literal:

Usage:

::

  hublatest -c config.ini

Notes:

* Options set under ``[DEFAULT]`` are glocal and will be applied by default

* Options set under ``[DEFAULT]`` can be overriden by commandline options or options

* Add sections named like ``[owner/repo]`` to auto-download release files from a list of repositories when no repositories are specified from commandline; if no specific options are needed for a repository, its section can be left empty

* Refer to the commandline option usages for the config options

* ``prerelease = true`` means ``--prerelease``; ``prerelease = false`` means ``--no-prerelease``


------------

（中文版说明）

用来获取GitHub仓库的Release的脚本。

环境要求
********

* 需要Python 3.6及以上。

命令行用法
**********

.. argparse::
  :filename: ./get_arg_parser.py
  :func: get_arg_parser_zh_cn
  :prog: hublatest
  :nodescription:
  :nodefault:
  :markdownhelp:

配置文件用法
************

配置文件为INI格式，以下是配置文件的例子：

.. include:: ./config_example_zh_cn.ini
   :literal:

用法例如：

::

  hublatest -c config.ini

一些说明：

* ``[DEFAULT]`` 下的选项会应用于所有仓库

* 可以用命令行参数覆盖 ``[DEFAULT]`` 中所写的设置项

* 要下载Release的各仓库用形如 ``[所有者/仓库名]`` 的小节标题表示，针对单个仓库的选项可以指定它对应的小节标题下；如果不需要指定任何参数，可以放一个空的小节

* 配置文件中的设置项意义参见命令行参数的用法

* ``prerelease`` 这一项给 ``true`` 是 ``--prerelease`` 的效果；给 ``false`` 是 ``--no-prerelease`` 的效果