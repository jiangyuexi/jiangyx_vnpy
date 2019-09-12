# -*- coding: utf-8 -*-
# @Time    : 2019/9/11 11:32
# @Author  : 蒋越希
# @Email   : jiangyuexi1992@qq.com
# @File    : my_utility.py
# @Software: PyCharm
from collections import Callable

from vnpy.trader.constant import Interval
from vnpy.trader.object import TickData, BarData
from vnpy.trader.utility import BarGenerator, ArrayManager


class NewBarGenerator(BarGenerator):
    """
    蒋越希 2019年9月11日10:49:19
    BarGenerator 可以继承 并重载  这里是demo
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
        super(NewBarGenerator, self).__init__(on_bar, window, on_window_bar, interval)

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
        # elif self.bar.datetime.minute != tick.datetime.minute:
        # 调整 时间窗口，避开高峰时间 蒋越希  修改 2019年9月11日11:03:31
        elif (tick.datetime.second >= 50) and (self.last_tick.datetime.second < 50):
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


class NewArrayManager(ArrayManager):
    """
        ArrayManager 扩展计算指标
        蒋越希 2019年9月11日11:36:04
    """

    def __init__(self, size=100):
        """
        
        :param size: numpy 数组大小
        """
        super(NewArrayManager, self).__init__(size)
