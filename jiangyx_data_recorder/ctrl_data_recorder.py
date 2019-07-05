# -*- coding: utf-8 -*-
"""
时间:
文件名:
描述:

@author: jiangyuexi1992@qq.com
"""
import os

import time

# 重启数据采集程序开关
from time import sleep
# run_oneday.py 是否运行 True 运行， False 没运行
IS_ONEDAY_EXIST = True

# 重启程序 后台运行
os.system(r'ps -efww|grep -w "run_oneday.py"|grep -v grep|cut -c 9-15|xargs kill -9')
os.system(r"nohup /usr/bin/python3 ./run_oneday.py&")
sleep(10)
os.system(r'ps -efww|grep -w "run_nextday.py"|grep -v grep|cut -c 9-15|xargs kill -9')
print(" start run_oneday.py")

while True:
    sleep(1 * 60)
    # print(int(time.strftime('%M', time.localtime())) % 10)
    # 一天快结束
    if (int(time.strftime('%M', time.localtime())) % 60 >= 57) \
            and (int(time.strftime('%H', time.localtime())) % 24 >= 23):
        if IS_ONEDAY_EXIST:
            # run_oneday.py 为未运行
            IS_ONEDAY_EXIST = False
            # 重启程序程序的另外一个对象 run_nextday.py
            os.system(r'ps -efww|grep -w "run_nextday.py"|grep -v grep|cut -c 9-15|xargs kill -9')
            os.system(r"nohup /usr/bin/python3 ./run_nextday.py&")
            print(" start run_nextday.py")
            print(" kill run_oneday.py")
            # 等待一段事件
            sleep(5 * 60)

            # 关闭前一个程序
            os.system(r'ps -efww|grep -w "run_oneday.py"|grep -v grep|cut -c 9-15|xargs kill -9')

        else:
            IS_ONEDAY_EXIST = True
            # 重启程序程序的另外一个对象 run_oneday.py
            os.system(r'ps -efww|grep -w "run_oneday.py"|grep -v grep|cut -c 9-15|xargs kill -9')
            os.system(r"nohup /usr/bin/python3 ./run_oneday.py&")
            print(" start run_oneday.py")
            print(" kill run_nextday.py")
            # 等待一段事件
            sleep(5 * 60)

            # 关闭前一个程序
            os.system(r'ps -efww|grep -w "run_nextday.py"|grep -v grep|cut -c 9-15|xargs kill -9')







