import os
import importlib
import traceback
from datetime import datetime
from threading import Thread
from pathlib import Path

from vnpy.event import Event, EventEngine
from vnpy.trader.engine import BaseEngine, MainEngine
from vnpy.trader.constant import Interval
from vnpy.trader.utility import extract_vt_symbol
from vnpy.trader.object import HistoryRequest
from vnpy.trader.database import database_manager
from vnpy.app.cta_strategy import (
    CtaTemplate,
    BacktestingEngine,
    OptimizationSetting
)
# 回测应用
APP_NAME = "CtaBacktester"
# 回测日志 事件
EVENT_BACKTESTER_LOG = "eBacktesterLog"
# 回测结束 事件
EVENT_BACKTESTER_BACKTESTING_FINISHED = "eBacktesterBacktestingFinished"
#回测优化结束 事件
EVENT_BACKTESTER_OPTIMIZATION_FINISHED = "eBacktesterOptimizationFinished"


class BacktesterEngine(BaseEngine):
    """
    For running CTA strategy backtesting.
    回测策略
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super().__init__(main_engine, event_engine, APP_NAME)
        # 存放策略类
        self.classes = {}
        # 回测引擎
        self.backtesting_engine = None
        # 回测引擎线程
        self.thread = None

        # Backtesting reuslt
        # 回测 dataframe 结果
        self.result_df = None
        # 回测统计结果
        self.result_statistics = None

        # Optimization result
        # 优化结果
        self.result_values = None
        # 从源码加载策略类
        self.load_strategy_class()

    def init_engine(self):
        """"""
        self.write_log("初始化CTA回测引擎")

        self.backtesting_engine = BacktestingEngine()
        # Redirect log from backtesting engine outside.
        # 将日志重定向到回测引擎。
        self.backtesting_engine.output = self.write_log

        self.write_log("策略文件加载完成")

        # self.init_rqdata()

    def init_rqdata(self):
        """
        Init RQData client.
        """
        # result = rqdata_client.init()
        # if result:
        #     self.write_log("RQData数据接口初始化成功")

    def write_log(self, msg: str):
        """
        写回测日志
        :param msg: 
        :return: 
        """
        event = Event(EVENT_BACKTESTER_LOG)
        event.data = msg
        self.event_engine.put(event)

    def load_strategy_class(self):
        """
        Load strategy class from source code.
        从源码加载策略类
        """
        app_path = Path(__file__).parent.parent
        path1 = app_path.joinpath("cta_strategy", "strategies")
        self.load_strategy_class_from_folder(
            path1, "vnpy.app.cta_strategy.strategies")

        path2 = Path.cwd().joinpath("strategies")
        self.load_strategy_class_from_folder(path2, "strategies")

    def load_strategy_class_from_folder(self, path: Path, module_name: str = ""):
        """
        Load strategy class from certain folder.
        从文件夹加载策略类
        """
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                if filename.endswith(".py"):
                    strategy_module_name = ".".join(
                        [module_name, filename.replace(".py", "")])
                    self.load_strategy_class_from_module(strategy_module_name)

    def load_strategy_class_from_module(self, module_name: str):
        """
        Load strategy class from module file.
        从模块文件加载策略类
        """
        try:
            module = importlib.import_module(module_name)

            for name in dir(module):
                value = getattr(module, name)
                if (isinstance(value, type) and issubclass(value, CtaTemplate) and value is not CtaTemplate):
                    self.classes[value.__name__] = value
        except:  # noqa
            msg = f"策略文件{module_name}加载失败，触发异常：\n{traceback.format_exc()}"
            self.write_log(msg)

    def get_strategy_class_names(self):
        """
        获取策略类的所有名字
        :return: 
        """
        return list(self.classes.keys())

    def run_backtesting(
        self,
        class_name: str,
        vt_symbol: str,
        interval: str,
        start: datetime,
        end: datetime,
        rate: float,
        slippage: float,
        size: int,
        pricetick: float,
        capital: int,
        setting: dict
    ):
        """
        运行回测
        :param class_name:  策略名称
        :param vt_symbol: 交易对.交易所
        :param interval: 时间间隔
        :param start: 开始时间
        :param end: 结束时间
        :param rate: 手续费
        :param slippage: 滑点
        :param size: 合约乘数
        :param pricetick: 价格跳动
        :param capital: 起始资金
        :param setting: 配置参数
        :return: 
        """
        self.result_df = None
        self.result_statistics = None
        # 回测引擎
        engine = self.backtesting_engine
        # 清空数据
        engine.clear_data()
        # 设置参数
        engine.set_parameters(
            vt_symbol=vt_symbol,
            interval=interval,
            start=start,
            end=end,
            rate=rate,
            slippage=slippage,
            size=size,
            pricetick=pricetick,
            capital=capital
        )
        # 获取策略类
        strategy_class = self.classes[class_name]
        # 把配置信息 用于构造 策略类 ，然后添加到回测引擎
        engine.add_strategy(
            strategy_class,
            setting
        )
        # 回测引擎加载数据
        engine.load_data()
        # 回测 引擎进行回测
        engine.run_backtesting()
        # 得到 dataframe格式的结果
        self.result_df = engine.calculate_result()
        # 回测统计结果
        self.result_statistics = engine.calculate_statistics(output=False)

        # Clear thread object handler.
        # 释放 线程对象句柄
        self.thread = None

        # Put backtesting done event
        # 告诉主引擎 回测已经结束
        event = Event(EVENT_BACKTESTER_BACKTESTING_FINISHED)
        self.event_engine.put(event)

    def start_backtesting(
        self,
        class_name: str,
        vt_symbol: str,
        interval: str,
        start: datetime,
        end: datetime,
        rate: float,
        slippage: float,
        size: int,
        pricetick: float,
        capital: int,
        setting: dict
    ):
        """
        开始回测
        :param class_name: 
        :param vt_symbol: 
        :param interval: 
        :param start: 
        :param end: 
        :param rate: 
        :param slippage: 
        :param size: 
        :param pricetick: 
        :param capital: 
        :param setting: 
        :return: 
        """
        if self.thread:
            self.write_log("已有任务在运行中，请等待完成")
            return False

        self.write_log("-" * 40)
        self.thread = Thread(
            target=self.run_backtesting,
            args=(
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
        )
        self.thread.start()

        return True

    def get_result_df(self):
        """
        获取回测 dataframe 格式结果
        :return: 
        """
        return self.result_df

    def get_result_statistics(self):
        """
         获取回测统计结果
        :return: 
        """
        return self.result_statistics

    def get_result_values(self):
        """
        获取 优化结果
        :return: 
        """
        return self.result_values

    def get_default_setting(self, class_name: str):
        """
        获取默认设置
        :param class_name: 
        :return: 
        """
        strategy_class = self.classes[class_name]
        return strategy_class.get_class_parameters()

    def run_optimization(
        self,
        class_name: str,
        vt_symbol: str,
        interval: str,
        start: datetime,
        end: datetime,
        rate: float,
        slippage: float,
        size: int,
        pricetick: float,
        capital: int,
        optimization_setting: OptimizationSetting,
        use_ga: bool
    ):
        """"""
        if use_ga:
            self.write_log("开始遗传算法参数优化")
        else:
            self.write_log("开始多进程参数优化")

        self.result_values = None

        engine = self.backtesting_engine
        engine.clear_data()

        engine.set_parameters(
            vt_symbol=vt_symbol,
            interval=interval,
            start=start,
            end=end,
            rate=rate,
            slippage=slippage,
            size=size,
            pricetick=pricetick,
            capital=capital
        )

        strategy_class = self.classes[class_name]
        engine.add_strategy(
            strategy_class,
            {}
        )

        if use_ga:
            self.result_values = engine.run_ga_optimization(
                optimization_setting,
                output=False
            )
        else:
            self.result_values = engine.run_optimization(
                optimization_setting,
                output=False
            )

        # Clear thread object handler.
        self.thread = None
        self.write_log("多进程参数优化完成")

        # Put optimization done event
        event = Event(EVENT_BACKTESTER_OPTIMIZATION_FINISHED)
        self.event_engine.put(event)

    def start_optimization(
        self,
        class_name: str,
        vt_symbol: str,
        interval: str,
        start: datetime,
        end: datetime,
        rate: float,
        slippage: float,
        size: int,
        pricetick: float,
        capital: int,
        optimization_setting: OptimizationSetting,
        use_ga: bool
    ):
        if self.thread:
            self.write_log("已有任务在运行中，请等待完成")
            return False

        self.write_log("-" * 40)
        self.thread = Thread(
            target=self.run_optimization,
            args=(
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
                optimization_setting,
                use_ga
            )
        )
        self.thread.start()

        return True

    def run_downloading(
        self,
        vt_symbol: str,
        interval: str,
        start: datetime,
        end: datetime
    ):
        """
        下载历史数据，放在数据库里
        
        """
        self.write_log(f"{vt_symbol}-{interval}开始下载历史数据")

        symbol, exchange = extract_vt_symbol(vt_symbol)
        
        req = HistoryRequest(
            symbol=symbol,
            exchange=exchange,
            interval=Interval(interval),
            start=start,
            end=end
        )

        contract = self.main_engine.get_contract(vt_symbol)

        # If history data provided in gateway, then query
        # 如果 gateway 提供了历史数据接口，直接请求
        if contract and contract.history_data:
            data = self.main_engine.query_history(req, contract.gateway_name)
        # Otherwise use RQData to query data
        else:
            pass
            # data = rqdata_client.query_history(req)

        if data:
            database_manager.save_bar_data(data)
            self.write_log(f"{vt_symbol}-{interval}历史数据下载完成")
        else:
            self.write_log(f"数据下载失败，无法获取{vt_symbol}的历史数据")

        # Clear thread object handler.
        self.thread = None

    def start_downloading(
        self,
        vt_symbol: str,
        interval: str,
        start: datetime,
        end: datetime
    ):
        if self.thread:
            self.write_log("已有任务在运行中，请等待完成")
            return False

        self.write_log("-" * 40)
        self.thread = Thread(
            target=self.run_downloading,
            args=(
                vt_symbol,
                interval,
                start,
                end
            )
        )
        self.thread.start()

        return True
