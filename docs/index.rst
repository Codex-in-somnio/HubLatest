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

默认的版本文件路径和下载路径均为当前工作目录。

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

TODO
****

目前仅根据tag名称来判断本地文件是否是最新，暂时不能应对Release可能被编辑过之类的情况。考虑加入基于时间戳的判断。