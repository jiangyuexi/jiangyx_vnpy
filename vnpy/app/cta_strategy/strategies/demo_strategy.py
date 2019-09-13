# -*- coding: utf-8 -*-
# @Time    : 2019/9/10 10:55
# @Author  : 蒋越希
# @Email   : jiangyuexi1992@qq.com
# @File    : demo_strategy.py
# @Software: PyCharm
from vnpy.app.cta_strategy import CtaTemplate
from vnpy.trader.constant import Interval
from vnpy.trader.object import BarData, TickData
from vnpy.trader.utility import BarGenerator, ArrayManager


class DemoStrategy(CtaTemplate):
    """
    策略学习
    """
    author = "蒋越希"

    # 定义界面可以配置的参数
    fast_window = 10
    slow_window = 20
    parameters = [
        # 快速窗口
        "fast_window",
        # 慢速窗口
        "slow_window"
    ]

    # 定义变量
    fast_ma0 = 0.0
    fast_ma1 = 0.0
    slow_ma0 = 0.0
    slow_ma1 = 0.0
    variables = [
        "fast_ma0",
        "fast_ma1",
        "slow_ma0",
        "slow_ma1",
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super(DemoStrategy, self).__init__(cta_engine, strategy_name, vt_symbol, setting)
        # 在on_window_bar参数里合成K线
        self.bg = BarGenerator(self.on_bar, window=5, on_window_bar=self.on_5min_bar, interval=Interval.MINUTE)
        self.am = ArrayManager()

    def on_init(self):
        """
        策略初始化
        :return: 
        """
        self.write_log("策略初始化")
        # 10 天
        self.load_bar(10)

    def on_start(self):
        """
        启动
        :return: 
        """
        self.write_log("启动")

    def on_stop(self):
        """
        策略停止
        :return: 
        """
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """TICK"""
        self.bg.update_tick(tick)

    def on_5min_bar(self, bar: BarData):
        """
        5分钟K线
        :param bar: 
        :return: 
        """
        am = self.am

        am.update_bar(bar)
        if not am.inited:
            return
        # 快移动均线
        fast_ma = am.sma(self.fast_window, array=True)
        self.fast_ma0 = fast_ma[-1]
        self.fast_ma1 = fast_ma[-2]
        # 慢速移动均线
        slow_ma = am.sma(self.slow_window, array=True)
        self.slow_ma0 = slow_ma[-1]
        self.slow_ma1 = slow_ma[-2]

        # 判断均线交叉
        # 金叉
        cross_over = (self.fast_ma0 >= self.slow_ma0) and (self.fast_ma1 < self.slow_ma1)
        # 死叉
        cross_below = (self.fast_ma0 <= self.slow_ma0) and (self.fast_ma1 > self.slow_ma1)

        if cross_over:
            price = bar.close_price + 5
            if not self.pos:
                # 如果没有仓位

                # 买入开仓(看涨)
                self.buy(price, 1)
            elif self.pos < 0:
                # 买入平仓
                self.cover(price, 1)
                self.buy(price, 1)
            elif self.pos > 0:
                # 如果是 多, 不操作
                pass
        elif cross_below:
            price = bar.close_price - 5
            if not self.pos:
                # 做空 卖出开仓（看跌）
                self.short(price, 1)
            elif self.pos > 0:
                self.sell(price, 1)
                self.short(price, 1)

        self.put_event()

    def on_bar(self, bar: BarData):
        """
        K 线更新
        :param bar: 
        :return: 
        """
        self.bg.update_bar(bar)




