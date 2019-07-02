from vnpy.trader.engine import MainEngine
from vnpy.trader.utility import load_json


class ConnectNoDialog(object):
    """
    Start connection of a certain gateway.
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

