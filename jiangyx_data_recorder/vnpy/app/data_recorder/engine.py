""""""

from threading import Thread
from queue import Queue, Empty
from copy import copy

from vnpy.event import Event, EventEngine
from vnpy.trader.database import database_manager
from vnpy.trader.engine import BaseEngine, MainEngine
from vnpy.trader.object import (
    SubscribeRequest,
    TickData,
    BarData,
    ContractData
)
from vnpy.trader.event import EVENT_TICK, EVENT_CONTRACT
from vnpy.trader.utility import load_json, save_json, BarGenerator

APP_NAME = "DataRecorder"

EVENT_RECORDER_LOG = "eRecorderLog"
EVENT_RECORDER_UPDATE = "eRecorderUpdate"


class RecorderEngine(BaseEngine):
    """
    数据收集引擎
    """
    # 配置文件
    setting_filename = "data_recorder_setting.json"

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super().__init__(main_engine, event_engine, APP_NAME)
        # 线程安全队列 数据库使用
        self.queue = Queue()
        self.thread = Thread(target=self.run)
        self.active = False
        # tick数据  需要记录的tick数据
        self.tick_recordings = {}
        # bar 数据 需要记录的bar数据
        self.bar_recordings = {}
        # 生成bar数据
        self.bar_generators = {}
        # 加载 "data_recorder_setting.json"
        self.load_setting()

        self.register_event()
        self.start()
        self.put_event()

    def load_setting(self):
        """"""
        # 从配置文件加载配置
        setting = load_json(self.setting_filename)
        self.tick_recordings = setting.get("tick", {})
        self.bar_recordings = setting.get("bar", {})

    def save_setting(self):
        """"""
        setting = {
            "tick": self.tick_recordings,
            "bar": self.bar_recordings
        }
        save_json(self.setting_filename, setting)

    def run(self):
        """
        数据收集引擎，事件循环函数
        :return: 
        """
        while self.active:
            try:
                # 从队列获取数据， 超时1秒
                task = self.queue.get(timeout=1)
                # 类型， 数据
                task_type, data = task

                if task_type == "tick":
                    # tick 数据存数据库
                    database_manager.save_tick_data([data])
                elif task_type == "bar":
                    # bar 数据存数据库
                    database_manager.save_bar_data([data])

            except Empty:
                continue

    def close(self):
        """"""
        self.active = False

        if self.thread.isAlive():
            self.thread.join()

    def start(self):
        """"""
        self.active = True
        self.thread.start()

    def register_event(self):
        """"""
        self.event_engine.register(EVENT_TICK, self.process_tick_event)
        self.event_engine.register(EVENT_CONTRACT, self.process_contract_event)

    def process_tick_event(self, event: Event):
        """
        事件函数 出来tick数据
        :param event: 
        :return: 
        """
        tick = event.data

        if tick.vt_symbol in self.tick_recordings:
            self.record_tick(tick)

        if tick.vt_symbol in self.bar_recordings:
            bg = self.get_bar_generator(tick.vt_symbol)
            bg.update_tick(tick)

    def process_contract_event(self, event: Event):
        """
        事件函数  交易对
        :param event: 
        :return: 
        """
        contract = event.data
        vt_symbol = contract.vt_symbol

        if(vt_symbol in self.tick_recordings or vt_symbol in self.bar_recordings):
            self.subscribe(contract)

    def write_log(self, msg: str):
        """
        向事件引擎 队列里丢 EVENT_RECORDER_LOG = "eRecorderLog" 类型的事件
        :param msg: 
        :return: 
        """
        event = Event(
            EVENT_RECORDER_LOG,
            msg
        )
        self.event_engine.put(event)

    def put_event(self):
        """"""
        tick_symbols = list(self.tick_recordings.keys())
        tick_symbols.sort()

        bar_symbols = list(self.bar_recordings.keys())
        bar_symbols.sort()

        data = {
            "tick": tick_symbols,
            "bar": bar_symbols
        }

        event = Event(
            EVENT_RECORDER_UPDATE,
            data
        )
        self.event_engine.put(event)

    def record_tick(self, tick: TickData):
        """"""
        task = ("tick", copy(tick))
        self.queue.put(task)

    def record_bar(self, bar: BarData):
        """"""
        task = ("bar", copy(bar))
        self.queue.put(task)

    def get_bar_generator(self, vt_symbol: str):
        """"""
        bg = self.bar_generators.get(vt_symbol, None)

        if not bg:
            bg = BarGenerator(self.record_bar)
            self.bar_generators[vt_symbol] = bg

        return bg

    def subscribe(self, contract: ContractData):
        """"""
        req = SubscribeRequest(
            symbol=contract.symbol,
            exchange=contract.exchange
        )
        self.main_engine.subscribe(req, contract.gateway_name)
