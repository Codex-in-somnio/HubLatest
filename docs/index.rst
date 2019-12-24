HubLatest
=================

用来获取GitHub仓库的Release的脚本。

环境要求
********

* 需要Python 3.6及以上。

命令行用法
**********

.. argparse::
  :filename: ../hublatest.py
  :func: get_arg_parser
  :prog: ./hublatest.py
  :nodescription:
  :nodefault:
  :markdownhelp:

配置文件用法
************

配置文件为INI格式，以下是配置文件的例子：

.. include:: ../config_example.ini
   :literal:

用法例如：

::

  ./hublatest.py -c config.ini

一些说明：

* ``[DEFAULT]`` 下的选项会应用于所有仓库

* 各仓库用形如 ``[所有者/仓库名]`` 的小节标题表示，针对单个仓库的选项可以指定它对应的小节标题下；如果不需要指定任何参数，可以放一个空的小节

* 配置文件中的设置项意义参见命令行参数的用法

* ``prerelease`` 这一项给 ``true`` 是 ``--prerelease`` 的效果；给 ``false`` 是 ``--no-prerelease`` 的效果

* 可以仅指定部分项目的值（省略的会使用默认值）

* 使用配置文件后，仍可以用命令行参数覆盖配置文件中所写的设置项