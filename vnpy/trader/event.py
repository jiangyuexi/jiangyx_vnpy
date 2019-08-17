"""
Event type string used in VN Trader.
事件字符串
"""

from vnpy.event import EVENT_TIMER  # noqa

# websocket   tick数据存入数据库事件
EVENT_TICK = "eTick."
# jiangyx  add  websocket  bar数据存入数据库事件
EVENT_BAR = "eBar."
EVENT_TRADE = "eTrade."
EVENT_ORDER = "eOrder."
EVENT_POSITION = "ePosition."
EVENT_ACCOUNT = "eAccount."
# websocket 请求 tick 和bar数据事件
EVENT_CONTRACT = "eContract."
# rest api 请求 1min bar 历史数据
EVENT_CONTRACT_1MIN = "eContract1min."
# 日志事件
EVENT_LOG = "eLog"
