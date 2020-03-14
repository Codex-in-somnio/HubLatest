import imp
import gettext
import os


def get_arg_parser():
    hublatest = imp.load_source("hublatest", "../src/hublatest/hublatest.py")
    return hublatest.get_arg_parser()


def get_arg_parser_zh_cn():
    os.environ["LANG"] = "zh_CN.UTF-8"
    return get_arg_parser()


def get_arg_parser_en():
    os.environ["LANG"] = "C.UTF-8"
    return get_arg_parser()
