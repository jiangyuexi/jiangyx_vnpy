"""
Basic data structure used for general trading function in VN Trader.
"""

from dataclasses import dataclass
from datetime import datetime
from logging import INFO

from .constant import Direction, Exchange, Interval, Offset, Status, Product, OptionType, OrderType

ACTIVE_STATUSES = set([Status.SUBMITTING, Status.NOTTRADED, Status.PARTTRADED])


@dataclass
class BaseData:
    """
    Any data object needs a gateway_name as source 
    and should inherit base data.
    通信类的名字
    """
    # 通信类的名字
    gateway_name: str

# "就是你定义一个很普通的类，@dataclass 装饰器可以帮你生成 " \
# "__repr__ __init__ 等等方法，就不用自己写一遍了。但是此装饰器返回的依然是一个" \
# " class，这意味着并没有带来任何不便，你依然可以使用继承、metaclass、docstring、定义方法等。"
@dataclass
class TickData(BaseData):
    """
    Tick data contains information about:
        * last trade in market
        * orderbook snapshot
        * intraday market statistics.
        tick数据结构， 请求得到的数据结构
    """

    symbol: str
    exchange: Exchange
    timestamp: float
    datetime: datetime

    name: str = ""
    volume: float = 0
    last_price: float = 0
    last_volume: float = 0
    limit_up: float = 0
    limit_down: float = 0

    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    pre_close: float = 0

    bid_price_1: float = 0
    bid_price_2: float = 0
    bid_price_3: float = 0
    bid_price_4: float = 0
    bid_price_5: float = 0

    ask_price_1: float = 0
    ask_price_2: float = 0
    ask_price_3: float = 0
    ask_price_4: float = 0
    ask_price_5: float = 0

    bid_volume_1: float = 0
    bid_volume_2: float = 0
    bid_volume_3: float = 0
    bid_volume_4: float = 0
    bid_volume_5: float = 0

    ask_volume_1: float = 0
    ask_volume_2: float = 0
    ask_volume_3: float = 0
    ask_volume_4: float = 0
    ask_volume_5: float = 0

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass
class BarData(BaseData):
    """
    Candlestick bar data of a certain trading period.
    开高低收 数据结构
    """

    symbol: str
    exchange: Exchange
    datetime: datetime

    interval: Interval = None
    volume: float = 0
    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    close_price: float = 0

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass
class OrderData(BaseData):
    """
    Order data contains information for tracking lastest status 
    of a specific order.
    订单数据结构
    """
    # 交易对
    symbol: str
    # 交易所
    exchange: Exchange
    # 订单号
    orderid: str
    # 交易类型  限价 市价
    type: OrderType = OrderType.LIMIT
    # 方向
    direction: Direction = ""
    offset: Offset = Offset.NONE
    # 价格
    price: float = 0
    # 挂单总数量
    volume: float = 0
    # 已成交数量
    traded: float = 0
    # 状态
    status: Status = Status.SUBMITTING
    time: str = ""

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
        self.vt_orderid = f"{self.gateway_name}.{self.orderid}"

    def is_active(self):
        """
        Check if the order is active.
        """
        if self.status in ACTIVE_STATUSES:
            return True
        else:
            return False

    def create_cancel_request(self):
        """
        Create cancel request object from order.
        """
        req = CancelRequest(
            orderid=self.orderid, symbol=self.symbol, exchange=self.exchange
        )
        return req


@dataclass
class TradeData(BaseData):
    """
    Trade data contains information of a fill of an order. One order
    can have several trade fills.
    """

    symbol: str
    exchange: Exchange
    orderid: str
    tradeid: str
    direction: Direction = ""

    offset: Offset = Offset.NONE
    price: float = 0
    volume: float = 0
    time: str = ""

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
        self.vt_orderid = f"{self.gateway_name}.{self.orderid}"
        self.vt_tradeid = f"{self.gateway_name}.{self.tradeid}"


@dataclass
class PositionData(BaseData):
    """
    Positon data is used for tracking each individual position holding.
    """

    symbol: str
    exchange: Exchange
    direction: Direction

    volume: float = 0
    frozen: float = 0
    price: float = 0
    pnl: float = 0
    yd_volume: float = 0

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
        self.vt_positionid = f"{self.vt_symbol}.{self.direction}"


@dataclass
class AccountData(BaseData):
    """
    Account data contains information about balance, frozen and
    available.
    """
    # 商品名
    accountid: str
    # 余额
    balance: float = 0
    # 冻结资金
    frozen: float = 0

    def __post_init__(self):
        """"""
        self.available = self.balance - self.frozen
        self.vt_accountid = f"{self.gateway_name}.{self.accountid}"


@dataclass
class LogData(BaseData):
    """
    Log data is used for recording log messages on GUI or in log files.
    """

    msg: str
    level: int = INFO

    def __post_init__(self):
        """"""
        self.time = datetime.now()


@dataclass
class ContractData(BaseData):
    """
    Contract data contains basic information about each contract traded.
    Contract数据，包含每一份交易Contract的基本信息。
    """
    # 交易对符号
    symbol: str
    # 交易所名字
    exchange: Exchange
    # 合约中文名
    name: str
    # 合约类型
    product: Product
    # 合约大小
    size: int
    # 合约最小价格TICK
    pricetick: float

    min_volume: float = 1           # minimum trading volume of the contract
    stop_supported: bool = False    # whether server supports stop order
    net_position: bool = False      # whether gateway uses net position volume
    history_data: bool = False      # whether gateway provides bar history data

    option_strike: float = 0
    option_underlying: str = ""     # vt_symbol of underlying contract
    option_type: OptionType = None
    option_expiry: datetime = None

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass
class SubscribeRequest:
    """
    Request sending to specific gateway for subscribing tick data update.
    请求tick数据
    """
    # 交易对
    symbol: str
    # 交易所
    exchange: Exchange

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass
class SubscribeRequest1Min:
    """
    请求1 min bar数据
    """

    symbol: str
    exchange: Exchange

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass
class OrderRequest:
    """
    Request sending to specific gateway for creating a new order.
    """
    # 交易对
    symbol: str
    # 交易所
    exchange: Exchange
    # 方向
    direction: Direction
    # 下单类型
    type: OrderType
    # 数量
    volume: float
    # 价格
    price: float = 0

    offset: Offset = Offset.NONE

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"

    def create_order_data(self, orderid: str, gateway_name: str):
        """
        Create order data from request.
        """
        order = OrderData(
            symbol=self.symbol,
            exchange=self.exchange,
            orderid=orderid,
            type=self.type,
            direction=self.direction,
            offset=self.offset,
            price=self.price,
            volume=self.volume,
            gateway_name=gateway_name,
        )
        return order


@dataclass
class CancelRequest:
    """
    Request sending to specific gateway for canceling an existing order.
    """
    # 订单号
    orderid: str
    # 交易对
    symbol: str
    # 交易所
    exchange: Exchange

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass
class HistoryRequest:
    """
    Request sending to specific gateway for querying history data.
    向指定的gateway，请求历史数据
    """
    # 交易对
    symbol: str
    # 交易所
    exchange: Exchange
    # 开始时间
    start: datetime
    # 结束时间
    end: datetime = None
    # 时间间隔
    interval: Interval = None

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
