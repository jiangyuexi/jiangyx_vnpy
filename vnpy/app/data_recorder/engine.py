""""""

from threading import Thread
from queue import Queue, Empty
from copy import copy

from vnpy.event import Event, EventEngine
from vnpy.trader.engine import BaseEngine, MainEngine
from vnpy.trader.object import (
    SubscribeRequest,
    SubscribeRequest1Min,
    TickData,
    BarData,
    ContractData
)
from vnpy.trader.event import EVENT_TICK, EVENT_CONTRACT, EVENT_BAR
from vnpy.trader.utility import load_json, save_json, BarGenerator
from vnpy.trader.database import database_manager


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
        # 数据库操作线程
        self.thread = Thread(target=self.run)
        # 活动状态初始为False
        self.active = False
        # 存入数据库的 tick 交易对
        self.tick_recordings = {}
        # 存入数据库的 bar 交易对
        self.bar_recordings = {}
        # 存放生成的 bar
        self.bar_generators = {}
        # 加载 data_recorder_setting.json
        self.load_setting()
        # 注册 事件
        self.register_event()
        # 启动数据库事件驱动
        self.start()
        # 把需要保存的tick、bar数据的交易对代号放进事件引擎。
        self.put_event()

    def load_setting(self):
        """
        从setting_filename里面加载，要存入数据库的交易对
        :return: 
        """
        setting = load_json(self.setting_filename)
        # 存入数据库的 tick 交易对
        self.tick_recordings = setting.get("tick", {})
        # 存入数据库的 bar 交易对
        self.bar_recordings = setting.get("bar", {})

    def save_setting(self):
        """
        保存 setting_filename = "data_recorder_setting.json"
        :return: 
        """
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
        """
        停止 数据收集引擎
        :return: 
        """
        self.active = False

        if self.thread.isAlive():
            self.thread.join()

    def start(self):
        """
        开始 数据收集引擎
        :return: 
        """
        self.active = True
        self.thread.start()

    def add_bar_recording(self, vt_symbol: str):
        """
        添加 交易对符号到 bar_recordings，
        :param vt_symbol: 交易对符号
        :return: 
        """
        if vt_symbol in self.bar_recordings:
            self.write_log(f"已在K线记录列表中：{vt_symbol}")
            return

        contract = self.main_engine.get_contract(vt_symbol)
        if not contract:
            self.write_log(f"找不到合约：{vt_symbol}")
            return

        self.bar_recordings[vt_symbol] = {
            "symbol": contract.symbol,
            "exchange": contract.exchange.value,
            "gateway_name": contract.gateway_name
        }

        self.subscribe(contract)
        self.subscribe1min(contract)
        self.save_setting()
        self.put_event()

        self.write_log(f"添加K线记录成功：{vt_symbol}")

    def add_tick_recording(self, vt_symbol: str):
        """
        添加 交易对符号到 tick_recordings，
        :param vt_symbol: 
        :return: 
        """
        if vt_symbol in self.tick_recordings:
            self.write_log(f"已在Tick记录列表中：{vt_symbol}")
            return

        contract = self.main_engine.get_contract(vt_symbol)
        if not contract:
            self.write_log(f"找不到合约：{vt_symbol}")
            return

        self.tick_recordings[vt_symbol] = {
            "symbol": contract.symbol,
            "exchange": contract.exchange.value,
            "gateway_name": contract.gateway_name
        }

        self.subscribe(contract)
        self.subscribe1min(contract)
        self.save_setting()
        self.put_event()

        self.write_log(f"添加Tick记录成功：{vt_symbol}")

    def remove_bar_recording(self, vt_symbol: str):
        """
        从 bar_recordings里，删除交易对符号
        :param vt_symbol: 交易对符号
        :return: 
        """
        if vt_symbol not in self.bar_recordings:
            self.write_log(f"不在K线记录列表中：{vt_symbol}")
            return

        self.bar_recordings.pop(vt_symbol)
        self.save_setting()
        self.put_event()

        self.write_log(f"移除K线记录成功：{vt_symbol}")

    def remove_tick_recording(self, vt_symbol: str):
        """
        不需要采集vt_symbol  的tick 数据了，从tick_recordings字典里移除，并更新事件引擎的数据采集事件        
        :param vt_symbol: 
        :return: 
        """
        if vt_symbol not in self.tick_recordings:
            self.write_log(f"不在Tick记录列表中：{vt_symbol}")
            return
        # 移除掉vt_symbol
        self.tick_recordings.pop(vt_symbol)
        # 保存配置信息
        self.save_setting()
        # 更新事件引擎的数据采集事件
        self.put_event()

        self.write_log(f"移除Tick记录成功：{vt_symbol}")

    def register_event(self):
        """
        注册事件到事件引擎  把数据存入数据库   和 订阅tick数据
        :return: 
        """
        # tick 数据事件， 把数据存入数据库
        self.event_engine.register(EVENT_TICK, self.process_tick_event)
        # bar 数据数据， 把bar数据存入数据库
        self.event_engine.register(EVENT_BAR, self.process_bar_event)
        # 订阅tick数据 和 bar 1min 数据
        self.event_engine.register(EVENT_CONTRACT, self.process_contract_event)

    def process_tick_event(self, event: Event):
        """
        EVENT_TICK 事件 关联的回调函数， 把tick数据存入数据库  
        :param event: Event
        :return: 
        """
        # 拿到 tick数据
        tick = event.data

        if tick.vt_symbol in self.tick_recordings:
            # 如果tick的符号在 tick_recordings里，则存入数据库
            self.record_tick(tick)

        # if tick.vt_symbol in self.bar_recordings:
        #     # 如果tick的符号在 bar_recordings里，则根据tick数据生成bar数据，但是这并不准确
        #     bg = self.get_bar_generator(tick.vt_symbol)
        #     # 这里存入数据库了吗？？
        #     bg.update_tick(tick)

    def process_bar_event(self, event: Event):
        """
         EVENT_BAR 事件 关联的回调函数， 把bar数据存入数据库 
        :param event: 
        :return: 
        """
        # 拿到 bar数据
        bar = event.data

        if bar.vt_symbol in self.bar_recordings:
            # 如果bar的符号在 tick_recordings里，则存入数据库
            self.record_bar(bar)

    def process_contract_event(self, event: Event):
        """
        处理contract 事件，订阅tick数据 和 bar 1min 数据
        :param event: 
        :return: 
        """
        # 事件数据
        contract = event.data
        # 交易对符号
        vt_symbol = contract.vt_symbol

        if vt_symbol in self.tick_recordings:
            # 如果交易对符号在tick_recordings，则订阅tick 数据
            self.subscribe(contract)

        if vt_symbol in self.bar_recordings:
            # 如果交易对符号在bar_recordings，则订阅bar 数据
            self.subscribe1min(contract)

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
        """
        把需要保存的tick、bar数据的交易对代号放进事件引擎。
        :return: 
        """
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
        """
        把TickData类型的数据存入数据库
        :param tick: TickData数据
        :return: 
        """
        task = ("tick", copy(tick))
        # 数据库专用队列里放 tick数据
        self.queue.put(task)

    def record_bar(self, bar: BarData):
        """
        把BarData类型的数据存入数据库
        :param bar: BarData 数据
        :return: 
        """
        task = ("bar", copy(bar))
        # 数据库专用队列里放 bar数据
        self.queue.put(task)

    def get_bar_generator(self, vt_symbol: str):
        """
        获取bar_generators里面存放的bar， 如果不存在则生成bar
        :param vt_symbol: 交易对符号 
        :return: 
        """
        # 从bar_generators获取 vt_symbol相关的bar ，一个BarGenerator对象
        bg = self.bar_generators.get(vt_symbol, None)

        if not bg:
            # 如果没有就生成 bar
            bg = BarGenerator(self.record_bar)
            self.bar_generators[vt_symbol] = bg

        return bg

    def subscribe(self, contract: ContractData):
        """
        订阅数据 tick 数据
        :param contract: 
        :return: 
        """
        req = SubscribeRequest(
            symbol=contract.symbol,
            exchange=contract.exchange
        )
        # 从指定的gateway 订阅tick数据
        self.main_engine.subscribe(req, contract.gateway_name)

    def subscribe1min(self, contract: ContractData):
        """
        订阅数据 1min bar 数据
        :param contract: 
        :return: 
        """
        req = SubscribeRequest1Min(
            symbol=contract.symbol,
            exchange=contract.exchange
        )
        # 从指定的gateway 订阅 1min bar数据
        self.main_engine.subscribe1min(req, contract.gateway_name)
