# -*- coding: utf-8 -*-
# @Time    : 2019/9/3 15:03
# @Author  : 蒋越希
# @Email   : jiangyuexi1992@qq.com
# @File    : no_widget.py
# @Software: PyCharm

from vnpy.trader.engine import MainEngine
from vnpy.trader.utility import load_json


class ConnectNoDialog(object):
    """
    Start connection of a certain gateway.
    开始一个gateway的连接
    """

    def __init__(self, main_engine: MainEngine, gateway_name: str):
        """"""
        self.main_engine = main_engine
        self.gateway_name = gateway_name
        self.filename = f"connect_{gateway_name.lower()}.json"

    def connect(self):
        """
        Get setting value from line edits and connect the gateway.
        获取配置从文本框，然后连接交易通道
        """
        setting = {}
        # 读取配置文件里的配置
        setting = load_json(self.filename)
        # 引入日志模块
        self.main_engine.connect(setting, self.gateway_name)

