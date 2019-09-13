from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)


class AtrRsiStrategy(CtaTemplate):
    """
    相对强弱指标（Relative Strength Index，RSI）
    均幅指标（Average True Range，ATR）
    """

    author = "用Python的交易员"
    # ATR指标的周期长度，也即是多少日的TR的均值
    atr_length = 22
    # ATR指标的移动平均值长度。
    atr_ma_length = 10
    # RSI指标的周期长度。
    rsi_length = 5
    # RSI指标的进场数值。
    rsi_entry = 16
    # 用于止盈或者止损的百分比。
    trailing_percent = 0.8
    # 仓位数。
    fixed_size = 1

    # 当前ATR的值。
    atr_value = 0
    # 当前ATR的移动均值。
    atr_ma = 0
    # 当前RSI的值。
    rsi_value = 0
    # RSI的多头上轨。
    rsi_buy = 0
    # RSI的空头上轨。
    rsi_sell = 0
    # 分别用于表示日内交易当前bar的最高价和最低价
    intra_trade_high = 0
    intra_trade_low = 0
    # 交易策略 参数配置
    parameters = ["atr_length", "atr_ma_length", "rsi_length",
                  "rsi_entry", "trailing_percent", "fixed_size"]
    variables = ["atr_value", "atr_ma", "rsi_value", "rsi_buy", "rsi_sell"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(AtrRsiStrategy, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )
        # 1min bar 合成 器
        self.bg = BarGenerator(self.on_bar)
        # bar 数据容器， 包含各种技术指标值
        self.am = ArrayManager()

    def on_init(self):
        """
        Callback when strategy is inited.
        回调函数，用于策略的初始化
        """
        self.write_log("策略初始化")
        # RSI的多头上轨。
        self.rsi_buy = 50 + self.rsi_entry
        # RSI的空头上轨。
        self.rsi_sell = 50 - self.rsi_entry

        # 加载 10天的 1min bar
        self.load_bar(10)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        回调函数  当一条新的bar数据更新
        """
        # 、通过策略 关闭所有订单
        self.cancel_all()

        am = self.am
        # 添加一个新的bar到 am里
        am.update_bar(bar)
        if not am.inited:
            return

        atr_array = am.atr(self.atr_length, array=True)
        # 得到atr值
        self.atr_value = atr_array[-1]
        # atr 的 移动均线
        self.atr_ma = atr_array[-self.atr_ma_length:].mean()
        #  得到rsi的值
        self.rsi_value = am.rsi(self.rsi_length)

        # 交易逻辑
        if self.pos == 0:
            # bar 的最高价
            self.intra_trade_high = bar.high_price
            # bar 的最低价
            self.intra_trade_low = bar.low_price

            if self.atr_value > self.atr_ma:
                # atr值 大于 atr均线
                if self.rsi_value > self.rsi_buy:
                    self.buy(bar.close_price + 5, self.fixed_size)
                elif self.rsi_value < self.rsi_sell:
                    self.short(bar.close_price - 5, self.fixed_size)

        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price

            long_stop = self.intra_trade_high * \
                (1 - self.trailing_percent / 100)
            self.sell(long_stop, abs(self.pos), stop=True)

        elif self.pos < 0:
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
            self.intra_trade_high = bar.high_price

            short_stop = self.intra_trade_low * \
                (1 + self.trailing_percent / 100)
            self.cover(short_stop, abs(self.pos), stop=True)

        self.put_event()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
