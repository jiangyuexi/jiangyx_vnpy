# -*- coding: utf-8 -*-
# @Time    : 2019/9/5 10:19
# @Author  : 蒋越希
# @Email   : jiangyuexi1992@qq.com
# @File    : zb_gateway.py
# @Software: PyCharm
# encoding: UTF-8

import hashlib
import hmac
import sys
import time
import json
import struct
import base64
import ccxt
import zlib
from copy import copy
from datetime import datetime, timedelta
from threading import Lock
from urllib.parse import urlencode

from gevent import sleep

from requests import ConnectionError

from vnpy.api.rest import Request, RestClient
from vnpy.api.websocket import WebsocketClient
from vnpy.trader.constant import (
    Direction,
    Exchange,
    OrderType,
    Product,
    Status,
    Offset,
    Interval
)
from vnpy.trader.gateway import BaseGateway
from vnpy.trader.object import (
    TickData,
    OrderData,
    TradeData,
    AccountData,
    ContractData,
    PositionData,
    BarData,
    OrderRequest,
    CancelRequest,
    SubscribeRequest,
    HistoryRequest,
    SubscribeRequest1Min)
from vnpy.trader.utility import TimeUtils

REST_HOST_MARKET = "http://api.zb.cn"
REST_HOST_TRADE = "https://trade.zb.cn"
WEBSOCKET_HOST = "wss://api.zb.cn/websocket"

STATUS_ZB = {
    0: "待成交/待成交未交易部份",
    1: Status.CANCELLED,
    2: Status.ALLTRADED,
    3: "待成交/待成交未交易部份",

}

ORDERTYPE_VT2OKEX = {
    OrderType.LIMIT: "limit",
    OrderType.MARKET: "market"
}
ORDERTYPE_ZB2VT = {
    1: "buy",
    0: "sell"
}

# 把枚举类型和字符串建立字典
INTERVAL_VT2ZB = {
    Interval.MINUTE: "1min",
    Interval.HOUR: "1hour",
    Interval.DAILY: "1day",
}
# 单位 s
TIMEDELTA_MAP = {
    Interval.MINUTE: 60,
    Interval.HOUR: 3600,
    Interval.DAILY: 86400,
}
# 交易对集合
instruments = set()
# 数字货币的集合
currencies = set()


class ZbGateway(BaseGateway):
    """
    VN Trader Gateway for Zb connection.
    Zb 现货
    """
    # 配置信息
    default_setting = {
        "API Key": "",
        "Secret Key": "",
        "会话数": 3,
        "代理地址": "",
        "代理端口": "",
    }

    exchanges = [Exchange.ZB]

    def __init__(self, event_engine):
        """Constructor"""
        super(ZbGateway, self).__init__(event_engine, "ZB")
        # 中币市场行情 rest api
        self.rest_market_api = ZbMarketRestApi(self)
        # # 中币交易rest api
        self.rest_trade_api = ZbTradeRestApi(self)
        # 中币 websocket api
        self.ws_api = ZbWebsocketApi(self)

        self.orders = {}

    def connect(self, setting: dict):
        """"""
        key = setting["API Key"]
        secret = setting["Secret Key"]
        session_number = setting["会话数"]
        proxy_host = setting["代理地址"]
        proxy_port = setting["代理端口"]

        if proxy_port.isdigit():
            proxy_port = int(proxy_port)
        else:
            proxy_port = 0

        self.rest_market_api.connect(key, secret,
                              session_number, proxy_host, proxy_port)
        self.rest_trade_api.connect(key, secret,
                              session_number, proxy_host, proxy_port)
        self.ws_api.connect(key, secret, proxy_host, proxy_port)

    def subscribe(self, req: SubscribeRequest):
        """"""
        # 等待websocket对象创建成功
        sleep(5)
        self.ws_api.subscribe(req)

    def subscribe1min(self, req: SubscribeRequest1Min):
        """"""
        # 等待websocket对象创建成功
        sleep(5)
        self.ws_api.subscribe1min(req)

    def send_order(self, req: OrderRequest):
        """"""
        return self.rest_api.send_order(req)

    def cancel_order(self, req: CancelRequest):
        """"""
        self.rest_api.cancel_order(req)

    def query_account(self):
        """"""
        pass

    def query_position(self):
        """"""
        pass

    def query_history(self, req: HistoryRequest):
        """"""
        return self.rest_market_api.query_history(req)

    def close(self):
        """"""
        self.rest_market_api.stop()
        # self.ws_api.stop()

    def on_order(self, order: OrderData):
        """"""
        self.orders[order.orderid] = order
        super().on_order(order)

    def get_order(self, orderid: str):
        """"""
        return self.orders.get(orderid, None)


class ZbMarketRestApi(RestClient):
    """
    ZB REST API
    """

    def __init__(self, gateway: BaseGateway):
        """"""
        super(ZbMarketRestApi, self).__init__()
        # gateway 对象
        self.gateway = gateway
        # gateway 对象名
        self.gateway_name = gateway.gateway_name

        self.key = ""
        self.secret = ""

        self.connect_time = 0

    def connect(
            self,
            key: str,
            secret: str,
            session_number: int,
            proxy_host: str,
            proxy_port: int,
    ):
        """
        Initialize connection to REST server.
        """
        # 连接时间
        self.connect_time = int(datetime.now().strftime("%y%m%d%H%M%S"))
        # 把 rest api 行情接口的连接地址保存到 url_base
        self.init(REST_HOST_MARKET, proxy_host, proxy_port)
        self.start(session_number)
        self.gateway.write_log("ZB REST API 行情接口启动成功")
        # 获取服务器时间
        self.query_time()
        # 获取所有交易对
        self.query_contract()

    def query_contract(self):
        """
        获取交易对
        :return: 
        """
        self.add_request(
            "GET",
            "/data/v1/markets",
            callback=self.on_query_contract
        )

    def query_time(self):
        """"""
        self.add_request(
            "GET",
            "/data/v1/ticker?market=btc_usdt",
            callback=self.on_query_time
        )

    def on_query_contract(self, data, request):
        """"""
        for symbol in data:
            priceScale = int(data[symbol]["priceScale"])
            amountScale = int(data[symbol]["amountScale"])
            contract = ContractData(
                symbol=symbol,
                exchange=Exchange.ZB,
                name=symbol,
                product=Product.SPOT,
                size=1,
                pricetick=round(0.1 ** priceScale, priceScale),
                min_volume=round(0.1 ** amountScale, amountScale),
                history_data=True,
                gateway_name=self.gateway_name
            )
            self.gateway.on_contract(contract)
            instruments.add(symbol)
            spot1, spot2 = symbol.split("_")
            currencies.add(spot1)
            currencies.add(spot2)

        self.gateway.write_log("ZB 现货信息查询成功")
        # Start websocket api after instruments data
        # 当现货 信息查询成功后 开始 websocket
        # self.gateway.ws_api.start()

    def on_query_time(self, data, request):
        """
        获取时间
        :param data: rest api 请求返回的数据
        :param request: 
        :return: 
        """
        tu = TimeUtils()
        server_time = tu.convert_time(float(data["date"])/1000.0)
        local_time = datetime.utcnow().isoformat()
        msg = f"ZB 服务器时间：{server_time}，本机时间：{local_time}"
        self.gateway.write_log(msg)

    def on_failed(self, status_code: int, request: Request):
        """
        Callback to handle request failed.
        """
        msg = f"ZB 请求失败，状态码：{status_code}，信息：{request.response.text}"
        self.gateway.write_log(msg)

    def on_error(
            self, exception_type: type, exception_value: Exception, tb, request: Request
    ):
        """
        Callback to handler request exception.
        """
        msg = f"ZB 触发异常，状态码：{exception_type}，信息：{exception_value}"
        self.gateway.write_log(msg)

        sys.stderr.write(
            self.exception_detail(exception_type, exception_value, tb, request)
        )

    def query_history(self, req: HistoryRequest):
        """
        通过 rest 获取最新的历史k线数据 1000条
        :param req: 历史数据结构体
        :return: 返回历史K线数据
        """

        buf = {}
        # datetime 类型
        tu = TimeUtils()
        end_time = req.end
        # 开始时间戳 ms
        start = tu.convert_datetime2timestamp(req.start) * 1000
        # 时间间隔
        _type = INTERVAL_VT2ZB[req.interval]
        for i in range(10):
            # 尝试 10次
            # 开始时间
            path = f"/data/v1/kline?market={req.symbol}&type={_type}&since={start}"
            # K线个数默认1000个
            # Get response from server
            resp = self.request(
                "GET",
                path,
            )

            # Break if request failed with other status code
            # 如果 请求失败 跳出循环
            if resp.status_code // 100 != 2:
                msg = f"获取历史数据失败，状态码：{resp.status_code}，信息：{resp.text}"
                self.gateway.write_log(msg)
                break
            else:
                data = resp.json()["data"]
                if not data:
                    msg = f"获取历史数据为空"
                    break
                tu = TimeUtils()
                for l in data:
                    ts, o, h, l, c, v = l
                    dt = tu.convert_datetime(ts/1000)
                    bar = BarData(
                        symbol=req.symbol,
                        exchange=req.exchange,
                        datetime=dt,
                        interval=req.interval,
                        volume=float(v),
                        open_price=float(o),
                        high_price=float(h),
                        low_price=float(l),
                        close_price=float(c),
                        gateway_name=self.gateway_name
                    )
                    buf[bar.datetime] = bar
                # 单位  ms
                begin = data[0][0]
                end = data[-1][0]
                msg = f"获取历史数据成功，{req.symbol} - {req.interval.value}，{tu.convert_time(begin/1000)}" \
                      f" - {tu.convert_time(end/1000)}"
                self.gateway.write_log(msg)
                break

        index = list(buf.keys())
        index.sort()

        history = [buf[i] for i in index]
        return history


class ZbTradeRestApi(RestClient):
    """
    ZB 交易REST API 
    """

    def __init__(self, gateway: BaseGateway):
        """"""
        super(ZbTradeRestApi, self).__init__()

        self.gateway = gateway
        self.gateway_name = gateway.gateway_name

        self.key = ""
        self.secret = ""

        self.order_count = 10000
        self.order_count_lock = Lock()

        self.connect_time = 0

    def sign(self, request):
        """
        Generate ZB signature.
        填充 ZB request 的必要参数
        """
        # # 把路劲 和参数分离出来
        # url_path, str_params = request.path.split("?")
        # request.path = url_path
        # params = {}
        # for k_vs in str_params.split("&"):
        #     k, v = k_vs.split("=")
        #     params[k] = v
        #
        # request.params = params

        return request

    def create_url(self, url, params=''):
        """
        生成 zb rest api http请求
        :param url: Zb rest api 接口
        :param params: 字符串格式的参数
        :return: ZB 服务器可以识别的http请求
        """
        full_url = url
        if params:
            sha_secret = digest(self.secret)
            sign = hmac_sign(params, sha_secret)
            req_time = int(round(time.time() * 1000))
            params += '&sign=%s&reqTime=%d' % (sign, req_time)
            full_url += '?' + params
        return full_url

    def connect(
            self,
            key: str,
            secret: str,
            session_number: int,
            proxy_host: str,
            proxy_port: int,
    ):
        """
        Initialize connection to REST server.
        """
        self.key = key
        self.secret = secret
        self.connect_time = int(datetime.now().strftime("%y%m%d%H%M%S"))

        self.init(REST_HOST_TRADE, proxy_host, proxy_port)
        self.start(session_number)
        self.gateway.write_log("ZB 交易 REST API 启动成功")

        self.query_account()
        # 指定要查询的交易对
        self.query_order(symbol="usdt_qc")

        # 测试接口
        req = OrderRequest(symbol="usdt_qc", exchange=Exchange.ZB, direction=Direction.LONG, type=OrderType.LIMIT,
                           volume=0.01)
        # 价格
        req.price = 6.9
        req.offset = Offset.NONE
        self.send_order(req)

    def _new_order_id(self):
        with self.order_count_lock:
            self.order_count += 1
            return self.order_count

    def send_order(self, req: OrderRequest):
        """
        发送委托单
        :param req: 
        :return: 
        """
        orderid = f"a{self.connect_time}{self._new_order_id()}"
        order = req.create_order_data(orderid, self.gateway_name)
        tradetype = None
        if Direction.LONG == req.direction:
            #     buy
            tradetype = 1
        elif Direction.SHORT == req.direction:
            #     sell
            tradetype = 0
        params = 'accesskey=%s&amount=%s&currency=%s&method=order&price=%s&tradeType=%s' % \
                 (self.key, req.volume, req.symbol, req.price, tradetype)

        path = self.create_url("/api/order",
                               params)

        data = {}
        self.add_request(
            "POST",
            path,
            callback=self.on_send_order,
            data=data,
            extra=order,
            on_failed=self.on_send_order_failed,
            on_error=self.on_send_order_error,
        )

        self.gateway.on_order(order)
        return order.vt_orderid

    def cancel_order(self, req: CancelRequest):
        """"""
        data = {}
        params = 'accesskey=%s&currency=%s&id=%s&method=cancelOrder' % (self.key, req.symbol, req.orderid)
        path = self.create_url("/api/cancelOrder",
                               params)
        self.add_request(
            "GET",
            path,
            callback=self.on_cancel_order,
            data=data,
            on_error=self.on_cancel_order_error,
            on_failed=self.on_cancel_order_failed,
            extra=req
        )

    def query_account(self):
        """
        获取资金
        :return: 
        """
        path = self.create_url("/api/getAccountInfo",
                               f"accesskey={self.key}&method=getAccountInfo")
        self.add_request(
            "GET",
            path,
            callback=self.on_query_account
        )

    def query_order(self, symbol):
        """
        获取所有没有成交的委托 获取10*10
        :return: 
        """
        for i in range(10):
            sleep(0.01)
            path = self.create_url("/api/getUnfinishedOrdersIgnoreTradeType",
                                   f"accesskey={self.key}&currency={symbol}&method=getUnfinishedOrdersIgnoreTradeType&"
                                   f"pageIndex={i + 1}&pageSize=10")

            self.add_request(
                "GET",
                path,
                callback=self.on_query_order
            )

    def on_query_account(self, data, request):
        """
        获取资金
        :param data: 
        :param request: 
        :return: 
        """

        for account_data in data["result"]["coins"]:
            account = AccountData(
                accountid=account_data["enName"],
                balance=float(account_data["available"]),
                frozen=float(account_data["freez"]),
                gateway_name=self.gateway_name
            )
            self.gateway.on_account(account)

        self.gateway.write_log("ZB 账户资金查询成功")

    def on_query_order(self, data, request):
        """
        查询出所有的 "待成交/待成交未交易部份" 状态的委托
        :param data: 
        :param request: 
        :return: 
        """
        if "code" in data:
            return None
        tu = TimeUtils()
        for order_data in data:
            order = OrderData(
                symbol=order_data['currency'],
                exchange=Exchange.ZB,
                type=ORDERTYPE_ZB2VT[order_data["type"]],
                orderid=order_data["id"],
                price=float(order_data["price"]),
                volume=float(order_data["total_amount"]),
                traded=float(order_data["trade_amount"]),
                time=tu.convert_time(order_data["trade_date"]/1000),
                status=STATUS_ZB[order_data["status"]],
                gateway_name=self.gateway_name,
            )
            self.gateway.on_order(order)

        self.gateway.write_log("ZB 委托信息查询成功")

    def on_send_order_failed(self, status_code: str, request: Request):
        """
        Callback when sending order failed on server.
        """
        order = request.extra
        order.status = Status.REJECTED
        self.gateway.on_order(order)

        msg = f"ZB 委托失败，状态码：{status_code}，信息：{request.response.text}"
        self.gateway.write_log(msg)

    def on_send_order_error(
            self, exception_type: type, exception_value: Exception, tb, request: Request
    ):
        """
        Callback when sending order caused exception.
        """
        order = request.extra
        order.status = Status.REJECTED
        self.gateway.on_order(order)

        # Record exception if not ConnectionError
        if not issubclass(exception_type, ConnectionError):
            self.on_error(exception_type, exception_value, tb, request)

    def on_send_order(self, data, request):
        """Websocket will push a new order status"""
        order = request.extra

        code = data["code"]
        if 1000 != code:
            order.status = Status.REJECTED
            self.gateway.on_order(order)

            self.gateway.write_log(f"ZB 委托失败：{error_msg}")

    def on_cancel_order_error(
            self, exception_type: type, exception_value: Exception, tb, request: Request
    ):
        """
        Callback when cancelling order failed on server.
        """
        # Record exception if not ConnectionError
        if not issubclass(exception_type, ConnectionError):
            self.on_error(exception_type, exception_value, tb, request)

    def on_cancel_order(self, data, request):
        """Websocket will push a new order status"""
        pass

    def on_cancel_order_failed(self, status_code: int, request: Request):
        """If cancel failed, mark order status to be rejected."""
        req = request.extra
        order = self.gateway.get_order(req.orderid)
        if order:
            order.status = Status.REJECTED
            self.gateway.on_order(order)

    def on_failed(self, status_code: int, request: Request):
        """
        Callback to handle request failed.
        """
        msg = f"ZB 请求失败，状态码：{status_code}，信息：{request.response.text}"
        self.gateway.write_log(msg)

    def on_error(
            self, exception_type: type, exception_value: Exception, tb, request: Request
    ):
        """
        Callback to handler request exception.
        """
        msg = f"ZB 触发异常，状态码：{exception_type}，信息：{exception_value}"
        self.gateway.write_log(msg)

        sys.stderr.write(
            self.exception_detail(exception_type, exception_value, tb, request)
        )


class ZbWebsocketApi(WebsocketClient):
    """"""

    def __init__(self, gateway):
        """"""
        super(ZbWebsocketApi, self).__init__()
        self.ping_interval = 20  # OKEX use 30 seconds for ping

        self.gateway = gateway
        self.gateway_name = gateway.gateway_name

        self.key = ""
        self.secret = ""

        self.trade_count = 10000
        self.connect_time = 0

        self.callbacks = {}
        # tick 数据字典
        self.ticks = {}
        # bar 数据字典
        self.bars = {}

    def connect(
            self,
            key: str,
            secret: str,
            proxy_host: str,
            proxy_port: int
    ):
        """"""
        self.key = key
        self.secret = secret.encode()
        self.connect_time = int(datetime.now().strftime("%y%m%d%H%M%S"))

        self.init(WEBSOCKET_HOST, proxy_host, proxy_port)
        self.start()

    def unpack_data(self, data):
        """"""
        return json.loads(zlib.decompress(data, -zlib.MAX_WBITS))

    def subscribe(self, req: SubscribeRequest):
        """
        Subscribe to tick data upate.
        订阅tick数据来更新
        """
        tick = TickData(
            symbol=req.symbol,
            exchange=req.exchange,
            name=req.symbol,
            timestamp=0.0,
            datetime=datetime.now(),
            gateway_name=self.gateway_name,
        )
        self.ticks[req.symbol] = tick
        # 现货 ticker数据  和行情深度
        sopt1, sopt2 = req.symbol.split("_")
        channel_ticker = f'{sopt1}{sopt2}_ticker'
        channel_depth = f"{sopt1}{sopt2}_depth"

        self.callbacks[channel_ticker] = self.on_ticker
        self.callbacks[channel_depth] = self.on_depth
        # websocket 订阅
        req = {
            "event": "addChannel",
            "channel": [channel_ticker, channel_depth]
        }
        self.send_packet(req)

    def subscribe1min(self, req: SubscribeRequest1Min):
        """
        Subscribe to bar data upate.
        订阅1 分钟 bar数据来更新
        """
        # 中币websocket 上没有 获取K线数据的接口
        # min1bar = BarData(
        #     symbol=req.symbol,
        #     exchange=req.exchange,
        #     datetime=datetime.now(),
        #     interval=Interval.MINUTE,
        #     gateway_name=self.gateway_name,
        # )
        #
        # self.bars[req.symbol] = min1bar
        # sopt1, sopt2 = req.symbol.split("_")
        # # 现货 1 分钟 bar
        # channel_1min_bar = f"spot/candle60s:{req.symbol}"
        # self.callbacks[channel_1min_bar] = self.on_1min_bar
        # # websocket 订阅
        # req = {
        #     "op": "subscribe",
        #     "args": [channel_1min_bar]
        # }
        # self.send_packet(req)

    def on_connected(self):
        """"""
        self.gateway.write_log("ZB Websocket API连接成功")
        self.login()

    def on_disconnected(self):
        """"""
        self.gateway.write_log("ZB Websocket API连接断开")

    def on_packet(self, packet: dict):
        """"""
        if "event" in packet:
            event = packet["event"]
            if event == "subscribe":
                return
            elif event == "error":
                msg = packet["message"]
                self.gateway.write_log(f"ZB  Websocket API请求异常：{msg}")
            elif event == "login":
                self.on_login(packet)
        else:
            channel = packet["table"]
            data = packet["data"]
            callback = self.callbacks.get(channel, None)

            if callback:
                for d in data:
                    callback(d)

    def on_error(self, exception_type: type, exception_value: Exception, tb):
        """"""
        msg = f"ZB 触发异常，状态码：{exception_type}，信息：{exception_value}"
        self.gateway.write_log(msg)

        sys.stderr.write(self.exception_detail(
            exception_type, exception_value, tb))

    def login(self):
        """
        Need to login befores subscribe to websocket topic.
        """
        timestamp = str(time.time())

        msg = timestamp + 'GET' + '/users/self/verify'
        signature = generate_signature(msg, self.secret)

        req = {
            "op": "login",
            "args": [
                self.key,
                self.passphrase,
                timestamp,
                signature.decode("utf-8")
            ]
        }
        self.send_packet(req)
        self.callbacks['login'] = self.on_login

    def subscribe_topic(self):
        """
        Subscribe to all private topics.
        订阅所有私有主题
        """
        self.callbacks["spot/ticker"] = self.on_ticker
        self.callbacks["spot/depth5"] = self.on_depth
        self.callbacks["spot/candle60s"] = self.on_1min_bar
        self.callbacks["spot/account"] = self.on_account
        self.callbacks["spot/order"] = self.on_order

        # Subscribe to order update
        channels = []
        for instrument_id in instruments:
            channel = f"spot/order:{instrument_id}"
            channels.append(channel)

        req = {
            "op": "subscribe",
            "args": channels
        }
        self.send_packet(req)

        # Subscribe to account update
        channels = []
        for currency in currencies:
            channel = f"spot/account:{currency}"
            channels.append(channel)

        req = {
            "op": "subscribe",
            "args": channels
        }
        self.send_packet(req)

        # Subscribe to BTC/USDT trade for keep connection alive
        req = {
            "op": "subscribe",
            "args": ["spot/trade:BTC-USDT"]
        }
        self.send_packet(req)

    def on_login(self, data: dict):
        """"""
        success = data.get("success", False)

        if success:
            self.gateway.write_log("ZB Websocket API登录成功")
            self.subscribe_topic()
        else:
            self.gateway.write_log("ZB Websocket API登录失败")

    def on_ticker(self, d):
        """"""
        symbol = d["instrument_id"]
        tick = self.ticks.get(symbol, None)
        if not tick:
            return
        # 最新成交价
        tick.last_price = float(d["last"])
        # 	24小时开盘价
        tick.open_price = float(d["open_24h"])
        # 24小时最高价
        tick.high_price = float(d["high_24h"])
        # 24小时最低价
        tick.low_price = float(d["low_24h"])
        # 24小时成交量，按交易货币统计
        tick.volume = float(d["base_volume_24h"])
        # 年月日时分秒
        tick.datetime = utc_to_local(d["timestamp"])
        # 时间戳
        tick.timestamp = datetime.timestamp(tick.datetime)
        self.gateway.on_tick(copy(tick))

    def on_depth(self, d):
        """"""
        for tick_data in d:
            symbol = d["instrument_id"]
            tick = self.ticks.get(symbol, None)
            if not tick:
                return

            bids = d["bids"]
            asks = d["asks"]
            for n, buf in enumerate(bids):
                price, volume, _ = buf
                tick.__setattr__("bid_price_%s" % (n + 1), float(price))
                tick.__setattr__("bid_volume_%s" % (n + 1), float(volume))

            for n, buf in enumerate(asks):
                price, volume, _ = buf
                tick.__setattr__("ask_price_%s" % (n + 1), float(price))
                tick.__setattr__("ask_volume_%s" % (n + 1), float(volume))

            tick.datetime = utc_to_local(d["timestamp"])
            # 时间戳
            tick.timestamp = datetime.timestamp(tick.datetime)
            self.gateway.on_tick(copy(tick))

    def on_1min_bar(self, d):
        """

        :param d: 
        :return: 
        """
        symbol = d["instrument_id"]
        bar = self.bars.get(symbol, None)
        if not bar:
            return

        # 日期时间
        bar.datetime = utc_to_local(d["candle"][0])
        # print(d["candle"][0])
        # print(bar.datetime)
        # 开盘价
        bar.open_price = float(d["candle"][1])
        # 最高价
        bar.high_price = float(d["candle"][2])
        # 最低价
        bar.low_price = float(d["candle"][3])
        # 收盘价
        bar.close_price = float(d["candle"][4])
        # 成交量
        bar.volume = float(d["candle"][5])
        self.gateway.on_bar(copy(bar))

    def on_order(self, d):
        """"""
        order = OrderData(
            symbol=d["instrument_id"],
            exchange=Exchange.OKEX,
            type=ORDERTYPE_OKEX2VT[d["type"]],
            orderid=d["client_oid"],
            direction=DIRECTION_OKEX2VT[d["side"]],
            price=float(d["price"]),
            volume=float(d["size"]),
            traded=float(d["filled_size"]),
            time=utc_to_local(d["timestamp"]).strftime("%H:%M:%S"),
            status=STATUS_OKEX2VT[d["status"]],
            gateway_name=self.gateway_name,
        )
        self.gateway.on_order(copy(order))

        trade_volume = d.get("last_fill_qty", 0)
        if not trade_volume or float(trade_volume) == 0:
            return

        self.trade_count += 1
        tradeid = f"{self.connect_time}{self.trade_count}"

        trade = TradeData(
            symbol=order.symbol,
            exchange=order.exchange,
            orderid=order.orderid,
            tradeid=tradeid,
            direction=order.direction,
            price=float(d["last_fill_px"]),
            volume=float(trade_volume),
            time=d["last_fill_time"][11:19],
            gateway_name=self.gateway_name
        )
        self.gateway.on_trade(trade)

    def on_account(self, d):
        """"""
        account = AccountData(
            accountid=d["currency"],
            balance=float(d["balance"]),
            frozen=float(d["hold"]),
            gateway_name=self.gateway_name
        )

        self.gateway.on_account(copy(account))

    # ----------------------------------------------------------------------

    def __fill(self, value, lenght, fillByte):
        if len(value) >= lenght:
            return value
        else:
            fillSize = lenght - len(value)
        return value + chr(fillByte) * fillSize
        # ----------------------------------------------------------------------


    def __doXOr(self, s, value):
        slist = list(s)
        for index in range(len(slist)):
            slist[index] = chr(ord(slist[index]) ^ value)
        return "".join(slist)
    # ----------------------------------------------------------------------

    def __hmacSign(self, aValue, aKey):
        keyb = struct.pack("%ds" % len(aKey), aKey)
        value = struct.pack("%ds" % len(aValue), aValue)
        k_ipad = self.__doXOr(keyb, 0x36)
        k_opad = self.__doXOr(keyb, 0x5c)
        k_ipad = self.__fill(k_ipad, 64, 54)
        k_opad = self.__fill(k_opad, 64, 92)
        m = hashlib.md5()
        m.update(k_ipad)
        m.update(value)
        dg = m.digest()

        m = hashlib.md5()
        m.update(k_opad)
        subStr = dg[0:16]
        m.update(subStr)
        dg = m.hexdigest()
        return dg

        # ----------------------------------------------------------------------

    def __digest(self, aValue):
        value = struct.pack("%ds" % len(aValue), aValue)
        h = sha.new()
        h.update(value)
        dg = h.hexdigest()
        return dg

        # ----------------------------------------------------------------------

    def generateSign(self, params):
        # 参数按照ASCII值排序: {"accesskey":"ce2a18e0-dshs-4c44-4515-9aca67dd706e","amount":"0.001","channel":"usdtqc_order","event":"addChannel","no":"test001","price":"1.0","tradeType":"1"}
        # secretKey 加密后:86429c69799d3d6ac5da5c2c514baa874d75a4ba
        SHA_secret = self.__digest(self.secretKey)
        # 计算出sign: 6b9cd4aaee79a6b74fffa49146ae8879
        return self.__hmacSign(paramsStr, SHA_secret)


def fill(value, lenght, fill_byte):
    if len(value) >= lenght:
        return value
    else:
        fill_size = lenght - len(value)
    return value + chr(fill_byte) * fill_size


def xor(s, value):
    slist = list(s.decode('utf-8'))
    for index in range(len(slist)):
        slist[index] = chr(ord(slist[index]) ^ value)
    return "".join(slist)


def hmac_sign(arg_value, arg_key):
    keyb = struct.pack("%ds" % len(arg_key), arg_key.encode('utf-8'))
    value = struct.pack("%ds" % len(arg_value), arg_value.encode('utf-8'))
    k_ipad = xor(keyb, 0x36)
    k_opad = xor(keyb, 0x5c)
    k_ipad = fill(k_ipad, 64, 54)
    k_opad = fill(k_opad, 64, 92)
    m = hashlib.md5()
    m.update(k_ipad.encode('utf-8'))
    m.update(value)
    dg = m.digest()

    m = hashlib.md5()
    m.update(k_opad.encode('utf-8'))
    subStr = dg[0:16]
    m.update(subStr)
    dg = m.hexdigest()
    return dg


def digest(arg_value):
    value = struct.pack("%ds" % len(arg_value), arg_value.encode('utf-8'))
    h = hashlib.sha1()
    h.update(value)
    dg = h.hexdigest()
    return dg


def get_timestamp():
    """"""
    now = datetime.utcnow()
    timestamp = now.isoformat("T", "milliseconds")
    return timestamp + "Z"


def utc_to_local(timestamp):
    time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    utc_time = time + timedelta(hours=8)
    return utc_time
