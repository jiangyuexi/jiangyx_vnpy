# -*- coding: utf-8 -*-
# @Time    : 2019/9/3 15:21
# @Author  : 蒋越希
# @Email   : jiangyuexi1992@qq.com
# @File    : no_widget.py
# @Software: PyCharm

from vnpy.event import Event, EventEngine
from vnpy.trader.engine import MainEngine

from ..base import (
    APP_NAME,
    EVENT_CTA_LOG,
    EVENT_CTA_STOPORDER,
    EVENT_CTA_STRATEGY
)
from ..engine import CtaEngine


class CtaManager(object):
    """
    CTA 管理器
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        super(CtaManager, self).__init__()
        # 主引擎
        self.main_engine = main_engine
        # 事件引擎
        self.event_engine = event_engine
        # CTA 策略引擎
        self.cta_engine = main_engine.get_engine(APP_NAME)

        self.managers = {}
        # 注册事件
        self.register_event()
        # CTA策略引擎初始化
        self.cta_engine.init_engine()

    def register_event(self):
        """"""
        self.event_engine.register(
            EVENT_CTA_STRATEGY, self.process_strategy_event
        )
        self.event_engine.register(EVENT_CTA_LOG, self.process_log_event)

    def process_log_event(self, event: Event):
        """
        Output log event data with logging function.
        """
        log = event.data
        self.main_engine.engines["log"].logger.log(log.level, log.msg)

    def process_strategy_event(self, event):
        """
        Update strategy status onto its monitor.
        """
        data = event.data
        strategy_name = data["strategy_name"]

        if strategy_name in self.managers:
            manager = self.managers[strategy_name]
            # manager.update_data(data)
        else:
            manager = StrategyManager(self, self.cta_engine, data)

            self.managers[strategy_name] = manager

    def remove_strategy(self, strategy_name):
        """"""
        manager = self.managers.pop(strategy_name)
        manager.deleteLater()


class StrategyManager(object):
    """
    Manager for a strategy
    策略管理器
    """

    def __init__(
        self, cta_manager: CtaManager, cta_engine: CtaEngine, data: dict
    ):
        """"""
        super(StrategyManager, self).__init__()

        self.cta_manager = cta_manager
        self.cta_engine = cta_engine

        self.strategy_name = data["strategy_name"]
        print(data)
        self._data = data

    def init_strategy(self):
        """"""
        self.cta_engine.init_strategy(self.strategy_name)

    def start_strategy(self):
        """"""
        self.cta_engine.start_strategy(self.strategy_name)

    def stop_strategy(self):
        """"""
        self.cta_engine.stop_strategy(self.strategy_name)

    def remove_strategy(self):
        """"""
        result = self.cta_engine.remove_strategy(self.strategy_name)

        # Only remove strategy gui manager if it has been removed from engine
        if result:
            self.cta_manager.remove_strategy(self.strategy_name)


