"""
Event type string used in VN Trader.
事件字符串
"""

from vnpy.event import EVENT_TIMER  # noqa

# websocket   tick数据存入数据库事件
EVENT_TICK = "eTick."
# jiangyx  add  websocket  bar数据存入数据库事件
EVENT_BAR = "eBar."
# 交易
EVENT_TRADE = "eTrade."
# 委托单
EVENT_ORDER = "eOrder."

EVENT_POSITION = "ePosition."
# 商品  资金
EVENT_ACCOUNT = "eAccount."
# websocket 请求 tick 和bar数据事件
EVENT_CONTRACT = "eContract."

# 日志事件
EVENT_LOG = "eLog"
