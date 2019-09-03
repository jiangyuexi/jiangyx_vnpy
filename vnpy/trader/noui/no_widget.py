import datetime

from vnpy.app.cta_backtester import CtaBacktesterApp, BacktesterEngine, APP_NAME
from vnpy.app.cta_backtester.engine import EVENT_BACKTESTER_LOG, EVENT_BACKTESTER_BACKTESTING_FINISHED, \
    EVENT_BACKTESTER_OPTIMIZATION_FINISHED
from vnpy.app.cta_strategy import BacktestingEngine
from vnpy.app.cta_strategy.strategies.atr_rsi_strategy import AtrRsiStrategy
from vnpy.event import EventEngine, Event
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


class BacktesterManager(object):
    """
    配置回测系统
    """
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine, gateway_name: str):
        """
        
        :param main_engine: 主引擎对象
        :param event_engine: 事件引擎对象
        :param gateway_name: gateway 名字
        """
        # 主引擎
        self.main_engine = main_engine
        # 事件引擎
        self.event_engine = event_engine
        # gateway名字
        self.gateway_name = gateway_name
        # 回测引擎
        self.backtester_engine = main_engine.get_engine(APP_NAME)
        self.class_names = []
        self.settings = {}

        self.target_display = ""
        # 初始化策略设置
        self.init_strategy_settings()

        # 绑定 事件处理函数
        self.register_event()
        # 初始化回测引擎
        self.backtester_engine.init_engine()

    def init_strategy_settings(self):
        """"""
        self.class_names = self.backtester_engine.get_strategy_class_names()

        for class_name in self.class_names:
            setting = self.backtester_engine.get_default_setting(class_name)
            self.settings[class_name] = setting

    def register_event(self):
        """"""
        self.event_engine.register(EVENT_BACKTESTER_LOG, self.process_log_event)
        self.event_engine.register(
            EVENT_BACKTESTER_BACKTESTING_FINISHED, self.process_backtesting_finished_event)
        self.event_engine.register(
            EVENT_BACKTESTER_OPTIMIZATION_FINISHED, self.process_optimization_finished_event)

    def process_log_event(self, event: Event):
        """"""
        msg = event.data
        self.write_log(msg)

    def write_log(self, msg):
        """"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        msg = f"{timestamp}\t{msg}"
        print(msg)

    def process_backtesting_finished_event(self, event: Event):
        """"""
        # 统计结果
        statistics = self.backtester_engine.get_result_statistics()
        # 打印
        print(statistics)
        # self.statistics_monitor.set_data(statistics)
        # 获取回测 dataframe 格式结果
        df = self.backtester_engine.get_result_df()
        print(df)
        # self.chart.set_data(df)

    def process_optimization_finished_event(self, event: Event):
        """"""
        self.write_log("请点击[优化结果]按钮查看")
        self.result_button.setEnabled(True)

    def start_backtesting(self):
        """"""
        # 交易策略
        class_name = "AtrRsiStrategy"
        vt_symbol = "EOS-USDT.OKEX"
        interval = Interval.MINUTE
        start = datetime.datetime.strptime("2019-08-18", '%Y-%m-%d')
        end = datetime.datetime.strptime("2019-09-03", '%Y-%m-%d')
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
        # 设置
        setting = {"atr_length": 22, "atr_ma_length": 10, "rsi_length": 5,
                   "rsi_entry": 16, "trailing_percent": 0.8, "fixed_size": 1}
        print(setting)
        result = self.backtester_engine.start_backtesting(
            class_name,
            vt_symbol,
            interval,
            start,
            end,
            rate,
            slippage,
            size,
            pricetick,
            capital,
            setting
        )

        # if result:
        #     self.statistics_monitor.clear_data()
        #     self.chart.clear_data()

    def start_optimization(self):
        """"""
        # class_name = self.class_combo.currentText()
        # vt_symbol = self.symbol_line.text()
        # interval = self.interval_combo.currentText()
        # start = self.start_date_edit.date().toPyDate()
        # end = self.end_date_edit.date().toPyDate()
        # rate = float(self.rate_line.text())
        # slippage = float(self.slippage_line.text())
        # size = float(self.size_line.text())
        # pricetick = float(self.pricetick_line.text())
        # capital = float(self.capital_line.text())
        #
        # parameters = self.settings[class_name]
        # dialog = OptimizationSettingEditor(class_name, parameters)
        # i = dialog.exec()
        # if i != dialog.Accepted:
        #     return
        #
        # optimization_setting, use_ga = dialog.get_setting()
        # self.target_display = dialog.target_display
        #
        # self.backtester_engine.start_optimization(
        #     class_name,
        #     vt_symbol,
        #     interval,
        #     start,
        #     end,
        #     rate,
        #     slippage,
        #     size,
        #     pricetick,
        #     capital,
        #     optimization_setting,
        #     use_ga
        # )
        #
        # self.result_button.setEnabled(False)

    def start_downloading(self):
        """"""
        # vt_symbol = self.symbol_line.text()
        # interval = self.interval_combo.currentText()
        # start = self.start_date_edit.date().toPyDate()
        # end = self.end_date_edit.date().toPyDate()
        #
        # self.backtester_engine.start_downloading(
        #     vt_symbol,
        #     interval,
        #     start,
        #     end
        # )

    def show_optimization_result(self):
        """"""


        # result_values = self.backtester_engine.get_result_values()
        #
        # dialog = OptimizationResultMonitor(
        #     result_values,
        #     self.target_display
        # )
        # dialog.exec_()





