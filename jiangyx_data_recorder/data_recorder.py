from time import sleep

import logging

from vnpy.event import EventEngine
from vnpy.trader.constant import Exchange

from vnpy.trader.engine import MainEngine


# from vnpy.gateway.bitmex import BitmexGateway
# from vnpy.gateway.futu import FutuGateway
# from vnpy.gateway.ib import IbGateway
# from vnpy.gateway.ctp import CtpGateway
# from vnpy.gateway.femas import FemasGateway
# from vnpy.gateway.tiger import TigerGateway
# from vnpy.gateway.oes import OesGateway
from vnpy.gateway.okex import OkexGateway
from vnpy.gateway.huobi import HuobiGateway
# from vnpy.gateway.bitfinex import BitfinexGateway
# from vnpy.gateway.onetoken import OnetokenGateway
from vnpy.gateway.okexf import OkexfGateway
# from vnpy.gateway.xtp import XtpGateway
from vnpy.gateway.hbdm import HbdmGateway


from vnpy.app.data_recorder import DataRecorderApp

from vnpy.trader.noui.no_widget import ConnectNoDialog


def main():
    """"""
    # 创建 QApplication  对象 并进行初始化

    # 事件引擎
    event_engine = EventEngine()
    # 把事件引擎附加到主引擎里
    main_engine = MainEngine(event_engine)

    # 添加火币的交互通道
    main_engine.add_gateway(HuobiGateway)
    sleep(1)
    # main_engine.add_gateway(BitfinexGateway)
    # main_engine.add_gateway(OnetokenGateway)
    # main_engine.add_gateway(OkexGateway)
    sleep(1)
    # main_engine.add_gateway(OkexfGateway)
    sleep(1)
    # main_engine.add_gateway(HbdmGateway)
    sleep(1)

    # 把 app 保存到 apps 和 engines 里
    main_engine.add_app(DataRecorderApp)
    # 获取所有交易通道
    gateway_names = main_engine.get_all_gateway_names()
    for name in gateway_names:
        # 连接火币平台
        connect = ConnectNoDialog(main_engine=main_engine, gateway_name=name)
        connect.connect()
        sleep(5)
    while True:
        # 一天
        sleep(24 * 60 * 60)


if __name__ == "__main__":
    main()
