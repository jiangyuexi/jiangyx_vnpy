# -*- coding: utf-8 -*-
"""
时间:
文件名:
描述:

@author: jiangyuexi1992@qq.com
"""
import os

from datetime import datetime

# 重启数据采集程序开关
from time import sleep

isRestart = False

# while True:
#     if datetime.minute % 10 > 9:
#         # os.system(重启程序)
#         isRestart = True
#         sleep(5 * 60)
#

os.system(r"C:\ProgramData\Anaconda3\envs\python36\python.exe "
          r"D:/jiangyx/pythonPro/jiangyx_vnpy/jiangyx_data_recorder/data_recorder.py")

