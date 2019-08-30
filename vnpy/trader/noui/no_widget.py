import datetime

from vnpy.app.cta_backtester import CtaBacktesterApp, BacktesterEngine
from vnpy.app.cta_strategy import BacktestingEngine
from vnpy.app.cta_strategy.strategies.atr_rsi_strategy import AtrRsiStrategy
from vnpy.trader.constant import Interval
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


class ConfigBacktester(object):
    """
    配置回测系统
    """
    def __init__(self, main_engine: MainEngine, gateway_name: str):
        """"""
        self.main_engine = main_engine
        self.gateway_name = gateway_name

    def run_backtesting(self):
        """
        
        :return: 
        """
        print("运行回测")
        # 获取所有的 apps
        apps = self.main_engine.get_all_apps()
        # 找到 回测app
        app = None
        for _ in apps:
            if isinstance(_, CtaBacktesterApp):
                app = _

        # 创建回测引擎

        backtesterengine = BacktesterEngine(main_engine=self.main_engine, event_engine=self.main_engine.event_engine)
        backtesterengine.init_engine()

        # 交易策略
        class_name = "AtrRsiStrategy"
        vt_symbol = "EOS-USDT.OKEX"
        interval = Interval.MINUTE
        start = datetime.datetime.strptime("2019-08-26", '%Y-%m-%d')
        end = datetime.datetime.strptime("2019-08-29", '%Y-%m-%d')
        # 手续费
        rate = float(0.00001)
        # 滑点
        slippage = float(0.3)
        # 合约乘数
        size = float(300)
        # 价格跳动
        pricetick = float(0.2)
        # 回测资金
        capital = float(100000)
        #设置
        setting = {"atr_length": 22, "atr_ma_length": 10, "rsi_length": 5,
                  "rsi_entry": 16, "trailing_percent": 0.8, "fixed_size": 1}

        backtesterengine.run_backtesting(
            class_name=class_name,
            vt_symbol=vt_symbol,
            interval=interval,
            start=start,
            end=end,
            rate=rate,
            slippage=slippage,
            size=size,
            pricetick=pricetick,
            capital=capital,
            setting=setting
        )


        i = 1




