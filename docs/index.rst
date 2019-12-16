github_release_dl
=================

用来获取GitHub仓库的Release的脚本。

环境要求
********

* 需要Python 3.5及以上。

命令行用法
**********

.. argparse::
  :filename: ../github_release_dl.py
  :func: get_arg_parser
  :prog: ./github_release_dl.py
  :nodescription:
  :nodefault:
  :markdownhelp:

配置文件用法
************

配置文件为JSON格式，以下是配置文件的例子：

.. include:: ../config_example.json
   :literal:

用法例如：

::

  ./github_release_dl.py -c config.json

一些说明：

* 配置文件中的设置项意义参见命令行参数的用法；
* 可以仅指定部分项目的值（省略的会使用默认值）；
* 使用配置文件后，仍可以用命令行参数覆盖配置文件中所写的设置项。