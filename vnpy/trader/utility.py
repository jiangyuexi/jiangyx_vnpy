"""
General utility functions.
"""

import json
from pathlib import Path
from typing import Callable

import numpy as np
import talib
import time

import datetime

from .object import BarData, TickData
from .constant import Exchange, Interval


def extract_vt_symbol(vt_symbol: str):
    """
    通过. 把 vt_symbol 拆分成 (symbol, exchange)
    :return: (symbol, exchange)
    """
    symbol, exchange_str = vt_symbol.split('.')
    return symbol, Exchange(exchange_str)


def generate_vt_symbol(symbol: str, exchange: Exchange):
    return f'{symbol}.{exchange.value}'


def _get_trader_dir(temp_name: str):
    """
    Get path where trader is running in.
    获取路径
    """
    cwd = Path.cwd()
    temp_path = cwd.joinpath(temp_name)

    # If .vntrader folder exists in current working directory,
    # then use it as trader running path.
    if temp_path.exists():
        return cwd, temp_path

    # Otherwise use home path of system.
    home_path = Path.home()
    temp_path = home_path.joinpath(temp_name)

    # Create .vntrader folder under home path if not exist.
    if not temp_path.exists():
        temp_path.mkdir()

    return home_path, temp_path


TRADER_DIR, TEMP_DIR = _get_trader_dir(".vntrader")


def get_file_path(filename: str):
    """
    Get path for temp file with filename.
    把文件名添加到 vntrader路径里
    """
    return TEMP_DIR.joinpath(filename)


def get_folder_path(folder_name: str):
    """
    Get path for temp folder with folder name.
    """
    folder_path = TEMP_DIR.joinpath(folder_name)
    if not folder_path.exists():
        folder_path.mkdir()
    return folder_path


def get_icon_path(filepath: str, ico_name: str):
    """
    Get path for icon file with ico name.
    """
    ui_path = Path(filepath).parent
    icon_path = ui_path.joinpath("ico", ico_name)
    return str(icon_path)


def load_json(filename: str):
    """
    Load data from json file in temp path.
    在temp path里加载json文件
    """
    filepath = get_file_path(filename)

    if filepath.exists():
        with open(filepath, mode='r') as f:
            data = json.load(f)
        return data
    else:
        save_json(filename, {})
        return {}


def save_json(filename: str, data: dict):
    """
    Save data into json file in temp path.
    """
    filepath = get_file_path(filename)
    with open(filepath, mode='w+') as f:
        json.dump(data, f, indent=4)


def round_to(value: float, target: float):
    """
    Round price to price tick value.
    """
    rounded = int(round(value / target)) * target
    return rounded


class ToString:
    """
    打印一个对象, 继承这个类，可以方便的打印一个对象的内容
    """
    def getDescription(self):
        """
        
        :return: 
        """
        #利用str的format格式化字符串
        #利用生成器推导式去获取key和self中key对应的值的集合
        return ",".join("{}={}".format(key, getattr(self, key)) for key in self.__dict__.keys())

    def __str__(self):
        """
        
        :return: 
        """
        return "{}->({})".format(self.__class__.__name__,self.getDescription())


class TimeUtils(object):
    """
    时间处理函数
    """

    def convert_time(self, timestamp):
        """
        时间戳转换成日期和时间 str类型 单位 s
        :param timestamp: 
        :return: 
        """
        # 转换成localtime
        time_local = time.localtime(timestamp)
        # 转换成新的时间格式(2016-05-05 20:28:54)
        dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
        return dt

    def convert_date(self, timestamp):
        """
        时间戳转换成日期  单位 s
        :param timestamp: 
        :return: 
        """
        # 转换成localtime
        time_local = time.localtime(timestamp)
        # 转换成新的时间格式(2016-05-05 20:28:54)
        dt = time.strftime("%Y-%m-%d", time_local)
        return dt

    def convert_datetime(self, timestamp):
        """
        时间戳转换成日期 datetime类型 单位 s
        :param timestamp: 
        :return: datetime类型 的日期和时间
        """
        # 转换成localtime
        time_local = time.localtime(timestamp)
        # str  to   datetime
        dt_datetime = datetime.datetime(time_local.tm_year, time_local.tm_mon, time_local.tm_mday,
                                        time_local.tm_hour, time_local.tm_min, time_local.tm_sec)
        return dt_datetime

    def get_secend(self, timestamp):
        """
        从时间戳（s）中获取到秒   
        :param timestamp: 时间戳 （s）
        :return: 返回 秒
        """
        # 转换成localtime
        time_local = time.localtime(timestamp)
        return time_local.tm_sec

    def convert_date2timestamp(self, date):
        """
        str    把日期(2016-05-05 20:28:54) 转换成 时间戳    单位s
        :param date: (2016-05-05 20:28:54)
        :return: 时间戳 s
        """
        # 转为时间数组
        timeArray = time.strptime(date, "%Y-%m-%d %H:%M:%S")
        # 转为时间戳
        timeStamp = int(time.mktime(timeArray))
        return timeStamp

    def convert_date2timeArray(self, date):
        """
        str    把日期(2016-05-05 20:28:54) 转换成 timeArray    
        :param date: (2016-05-05 20:28:54)
        :return: datatime
        """
        # 转为时间数组
        timeArray = time.strptime(date, "%Y-%m-%d %H:%M:%S")
        return timeArray

    def convert_datetime2timestamp(self, datetime):
        """
        （datetime 类型 ）把日期 转换成 时间戳    单位s
        :param date: (2016-05-05 20:28:54)
        :return: 时间戳 s
        """
        # 转为时间戳
        timeStamp = int(time.mktime(datetime.timetuple()))
        return timeStamp

    def datetime2str(self, datetime):
        """
        （datetime 类型 ）把日期 转换成 字符串
        :param date: (2016-05-05 20:28:54)
        :return: “2016-05-05 20:28:54”
        """
        return datetime.strftime("%Y-%m-%d")


class BarGenerator(ToString):
    """
    For: 
    1. generating 1 minute bar data from tick data
    从tick 数据里生成 1分钟bar， （这里并不准确）
    2. generateing x minute bar/x hour bar data from 1 minute data
    从1 分钟bar里生成x分钟/x小时bar
    Notice:
    1. for x minute bar, x must be able to divide 60: 2, 3, 5, 6, 10, 15, 20, 30
    2. for x hour bar, x can be any number
    """

    def __init__(
        self,
        on_bar: Callable,
        window: int = 0,
        on_window_bar: Callable = None,
        interval: Interval = Interval.MINUTE
    ):
        """
         Constructor
         先调用 on_bar，然后调用 on_window_bar
        
        :param on_bar:  更新 bar
        :param window: window 个 bar
        :param on_window_bar: 合成bar的函数
        :param interval: bar的单位
        """
        self.bar = None
        self.on_bar = on_bar

        self.interval = interval
        self.interval_count = 0

        self.window = window
        self.window_bar = None
        # 合成 K线的回调函数
        self.on_window_bar = on_window_bar

        self.last_tick = None
        self.last_bar = None

    def update_tick(self, tick: TickData):
        """
        Update new tick data into generator.
        把新的tick数据更新到生成器
        """
        # flag 是否是新的一分钟
        new_minute = False

        # Filter tick data with 0 last price
        # 过滤掉 最新价格为0的数据
        if not tick.last_price:
            return

        if not self.bar:
            # bar里为空，那么是新的min
            new_minute = True
        elif self.bar.datetime.minute != tick.datetime.minute:
        # 调整 时间窗口，避开高峰时间 蒋越希  修改 2019年9月11日11:03:31
        # elif (tick.datetime.second >= 50) and (self.last_tick.datetime.second < 50):
            # 判断是否走完当前分钟
            self.bar.datetime = self.bar.datetime.replace(
                second=0, microsecond=0
            )
            # 把老的bar更新一下，开启新的一分钟
            self.on_bar(self.bar)

            new_minute = True

        if new_minute:
            # 如果是新的分钟，则生成新的bar
            self.bar = BarData(
                symbol=tick.symbol,
                exchange=tick.exchange,
                interval=Interval.MINUTE,
                datetime=tick.datetime,
                gateway_name=tick.gateway_name,
                open_price=tick.last_price,
                high_price=tick.last_price,
                low_price=tick.last_price,
                close_price=tick.last_price,
                open_interest=tick.open_interest
            )
        else:
            # 高 price
            self.bar.high_price = max(self.bar.high_price, tick.last_price)
            # 低 price
            self.bar.low_price = min(self.bar.low_price, tick.last_price)
            # 收 price
            self.bar.close_price = tick.last_price
            # 当前持仓量
            self.bar.open_interest = tick.open_interest
            self.bar.datetime = tick.datetime

        if self.last_tick:
            # 统计出bar里的成交量
            volume_change = tick.volume - self.last_tick.volume
            self.bar.volume += max(volume_change, 0)

        self.last_tick = tick

    def update_bar(self, bar: BarData):
        """
        Update 1 minute bar into generator
        """
        # If not inited, creaate window bar object
        if not self.window_bar:
            # Generate timestamp for bar data
            if self.interval == Interval.MINUTE:
                dt = bar.datetime.replace(second=0, microsecond=0)
            else:
                dt = bar.datetime.replace(minute=0, second=0, microsecond=0)

            self.window_bar = BarData(
                symbol=bar.symbol,
                exchange=bar.exchange,
                datetime=dt,
                gateway_name=bar.gateway_name,
                open_price=bar.open_price,
                high_price=bar.high_price,
                low_price=bar.low_price
            )
        # Otherwise, update high/low price into window bar
        else:
            self.window_bar.high_price = max(
                self.window_bar.high_price, bar.high_price)
            self.window_bar.low_price = min(
                self.window_bar.low_price, bar.low_price)

        # Update close price/volume into window bar
        self.window_bar.close_price = bar.close_price
        self.window_bar.volume += int(bar.volume)
        self.window_bar.open_interest = bar.open_interest

        # Check if window bar completed
        finished = False

        if self.interval == Interval.MINUTE:
            # x-minute bar
            if not (bar.datetime.minute + 1) % self.window:
                finished = True
        elif self.interval == Interval.HOUR:
            if self.last_bar and bar.datetime.hour != self.last_bar.datetime.hour:
                # 1-hour bar
                if self.window == 1:
                    finished = True
                # x-hour bar
                else:
                    self.interval_count += 1

                    if not self.interval_count % self.window:
                        finished = True
                        self.interval_count = 0

        if finished:
            self.on_window_bar(self.window_bar)
            self.window_bar = None

        # Cache last bar object
        self.last_bar = bar

    def generate(self):
        """
        Generate the bar data and call callback immediately.
        """
        self.bar.datetime = self.bar.datetime.replace(
            second=0, microsecond=0
        )
        self.on_bar(self.bar)
        self.bar = None


class ArrayManager(object):
    """
    For:
    1. time series container of bar data
    bar数据时序容器
    2. calculating technical indicator value
    计算技术指标值
    """

    def __init__(self, size=100):
        """Constructor"""
        # 推送进来的k线个数
        self.count = 0
        # 数据容器的大小
        self.size = size
        # 如果没有达到size大小，计算是没有意义的，不进行计算，一旦达到size大小，则开始计算
        self.inited = False
        # 使用numpy ,速度比list提升10以上
        self.open_array = np.zeros(size)
        self.high_array = np.zeros(size)
        self.low_array = np.zeros(size)
        self.close_array = np.zeros(size)
        self.volume_array = np.zeros(size)

    def update_bar(self, bar):
        """
        Update new bar data into array manager.
        添加一个新的bar 数据到 am
        """
        # 统计推送进来的k线个数
        self.count += 1
        if not self.inited and self.count >= self.size:
            self.inited = True
        # 1把老数据丢掉，2数组向左平移一个，
        self.open_array[:-1] = self.open_array[1:]
        self.high_array[:-1] = self.high_array[1:]
        self.low_array[:-1] = self.low_array[1:]
        self.close_array[:-1] = self.close_array[1:]
        self.volume_array[:-1] = self.volume_array[1:]
        # 3倒数第一个填充新的数据
        self.open_array[-1] = bar.open_price
        self.high_array[-1] = bar.high_price
        self.low_array[-1] = bar.low_price
        self.close_array[-1] = bar.close_price
        self.volume_array[-1] = bar.volume

    @property
    def open(self):
        """
        Get open price time series.
        获取到 open 数据序列
        """
        return self.open_array

    @property
    def high(self):
        """
        Get high price time series.
        获取到 high 数据序列
        """
        return self.high_array

    @property
    def low(self):
        """
        Get low price time series.
        获取到 low 数据序列
        """
        return self.low_array

    @property
    def close(self):
        """
        Get close price time series.
        获取到 close 数据序列
        """
        return self.close_array

    @property
    def volume(self):
        """
        Get trading volume time series.
        获取到 交易量 数据序列
        """
        return self.volume_array

    def sma(self, n, array=False):
        """
        Simple moving average.
        简单移动均线  n是窗口
        array  False 返回最后一个数据， True 返回数组
        """
        result = talib.SMA(self.close, n)
        if array:
            return result
        return result[-1]

    def std(self, n, array=False):
        """
        Standard deviation
        标准差 n是窗口
        array  False 返回最后一个数据， True 返回数组
        """
        result = talib.STDDEV(self.close, n)
        if array:
            return result
        return result[-1]

    def cci(self, n, array=False):
        """
        Commodity Channel Index (CCI).
        n是窗口
        array  False 返回最后一个数据， True 返回数组
        """
        result = talib.CCI(self.high, self.low, self.close, n)
        if array:
            return result
        return result[-1]

    def atr(self, n, array=False):
        """
        Average True Range (ATR).
        计算 ATR  n是窗口
        array  False 返回最后一个数据， True 返回数组
        """
        result = talib.ATR(self.high, self.low, self.close, n)
        if array:
            return result
        return result[-1]

    def rsi(self, n, array=False):
        """
        Relative Strenght Index (RSI).
        n是窗口
        array  False 返回最后一个数据， True 返回数组
        """
        result = talib.RSI(self.close, n)
        if array:
            return result
        return result[-1]

    def macd(self, fast_period, slow_period, signal_period, array=False):
        """
        MACD.
        """
        macd, signal, hist = talib.MACD(
            self.close, fast_period, slow_period, signal_period
        )
        if array:
            return macd, signal, hist
        return macd[-1], signal[-1], hist[-1]

    def adx(self, n, array=False):
        """
        ADX.
        """
        result = talib.ADX(self.high, self.low, self.close, n)
        if array:
            return result
        return result[-1]

    def boll(self, n, dev, array=False):
        """
        Bollinger Channel.
        """
        mid = self.sma(n, array)
        std = self.std(n, array)

        up = mid + std * dev
        down = mid - std * dev

        return up, down

    def keltner(self, n, dev, array=False):
        """
        Keltner Channel.
        """
        mid = self.sma(n, array)
        atr = self.atr(n, array)

        up = mid + atr * dev
        down = mid - atr * dev

        return up, down

    def donchian(self, n, array=False):
        """
        Donchian Channel.
        """
        up = talib.MAX(self.high, n)
        down = talib.MIN(self.low, n)

        if array:
            return up, down
        return up[-1], down[-1]


def virtual(func: "callable"):
    """
    mark a function as "virtual", which means that this function can be override.
    any base class should use this or @abstractmethod to decorate all functions
    that can be (re)implemented by subclasses.
    """
    return func
