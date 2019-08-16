"""
Event-driven framework of vn.py framework.
"""

from collections import defaultdict
from queue import Empty, Queue
from threading import Thread
from time import sleep
from typing import Any, Callable

# 定时器事件
EVENT_TIMER = "eTimer"


class Event:
    """
    Event object consists of a type string which is used 
    by event engine for distributing event, and a data 
    object which contains the real data. 
    本类提供给EventEngine 使用
    """

    def __init__(self, type: str, data: Any = None):
        """"""
        # str类型的type
        self.type = type
        # 数据
        self.data = data


# Defines handler function to be used in event engine.
# 定义处理函数在EventEngine使用
HandlerType = Callable[[Event], None]


class EventEngine:
    """
    Event engine distributes event object based on its type 
    to those handlers registered.

    It also generates timer event by every interval seconds,
    which can be used for timing purpose.
    事件引擎
    """

    def __init__(self, interval: int = 1):
        """
        Timer event is generated every 1 second by default, if
        interval not specified.
        默认定时器事件1秒一次
        """
        # 定时器事件的产生间隔，默认1秒
        self._interval = interval
        # 队列
        self._queue = Queue()
        # 下面两个线程的开关，一个是_thread， 另外一个是_timer
        self._active = False
        # 从队列获取事件，并且处理它。
        self._thread = Thread(target=self._run)
        # 休眠（interval）一秒
        # 然后生成一个定时器事件
        self._timer = Thread(target=self._run_timer)
        # 事件注册表
        self._handlers = defaultdict(list)
        self._general_handlers = []
        # 一个事件的数据结构 type 和 dict 类型的handlerList

    def _run(self):
        """
        Get event from queue and then process it.
        从队列获取事件，并且处理它。 事件引擎
        """
        while self._active:
            try:
                event = self._queue.get(block=True, timeout=1)
                self._process(event)
            except Empty:
                pass

    def _process(self, event: Event):
        """
        First ditribute event to those handlers registered listening
        to this type. 
        Then distrubute event to those general handlers which listens
        to all types.
        根据事件类型和事件内容，调用相应的回调函数，来进行处理
        """
        if event.type in self._handlers:
            [handler(event) for handler in self._handlers[event.type]]

        if self._general_handlers:
            [handler(event) for handler in self._general_handlers]

    def _run_timer(self):
        """
        Sleep by interval second(s) and then generate a timer event.
        休眠（interval）一秒 然后生成一个定时器事件
        """
        while self._active:
            sleep(self._interval)
            event = Event(EVENT_TIMER)
            self.put(event)

    def start(self):
        """
        Start event engine to process events and generate timer events.
        开始事件引擎，并产生定时器事件
        """
        self._active = True
        self._thread.start()
        self._timer.start()

    def stop(self):
        """
        Stop event engine.
        关闭事件引擎
        """
        self._active = False
        self._timer.join()
        self._thread.join()

    def put(self, event: Event):
        """
        Put an event object into event queue.
        """
        self._queue.put(event)

    def register(self, type: str, handler: HandlerType):
        """
        Register a new handler function for a specific event type. Every 
        function can only be registered once for each event type.
        """
        handler_list = self._handlers[type]
        if handler not in handler_list:
            handler_list.append(handler)

    def unregister(self, type: str, handler: HandlerType):
        """
        Unregister an existing handler function from event engine.
        """
        handler_list = self._handlers[type]

        if handler in handler_list:
            handler_list.remove(handler)

        if not handler_list:
            self._handlers.pop(type)

    def register_general(self, handler: HandlerType):
        """
        Register a new handler function for all event types. Every 
        function can only be registered once for each event type.
        """
        if handler not in self._general_handlers:
            self._general_handlers.append(handler)

    def unregister_general(self, handler: HandlerType):
        """
        Unregister an existing general handler function.
        """
        if handler in self._general_handlers:
            self._general_handlers.remove(handler)
