# -*- coding: utf-8 -*-
"""
时间:
文件名:
描述:

@author: jiangyuexi1992@qq.com
"""
# 创建一个logger
import os
import sys

import logging

import time

logger = logging.getLogger('mylogger')
# logger.setLevel(logging.INFO)

# 创建一个handler，用于写入日志文件
file_name = "./log/" + time.strftime("%Y-%m-%d", time.localtime()) + ".log"
if os.path.exists(file_name):
    pass
else:
    os.mknod(file_name)

fh = logging.FileHandler(file_name)
# fh.setLevel(logging.INFO)

# 再创建一个handler，用于输出到控制台
#ch = logging.StreamHandler(sys.stdout)
#ch.setLevel(logging.INFO)

# 定义handler的输出格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
#ch.setFormatter(formatter)

# 给logger添加handler
logger.addHandler(fh)
#logger.addHandler(ch)
