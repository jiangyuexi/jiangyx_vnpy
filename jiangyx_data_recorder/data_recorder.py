from time import sleep

from vnpy.event import EventEngine

from vnpy.trader.engine import MainEngine


# from vnpy.gateway.bitmex import BitmexGateway
# from vnpy.gateway.futu import FutuGateway
# from vnpy.gateway.ib import IbGateway
# from vnpy.gateway.ctp import CtpGateway
# from vnpy.gateway.femas import FemasGateway
# from vnpy.gateway.tiger import TigerGateway
# from vnpy.gateway.oes import OesGateway
# from vnpy.gateway.okex import OkexGateway
from vnpy.gateway.huobi import HuobiGateway
# from vnpy.gateway.bitfinex import BitfinexGateway
# from vnpy.gateway.onetoken import OnetokenGateway
# from vnpy.gateway.okexf import OkexfGateway
# from vnpy.gateway.xtp import XtpGateway
# from vnpy.gateway.hbdm import HbdmGateway


from vnpy.app.data_recorder import DataRecorderApp


def main():
    """"""
    # 创建 QApplication  对象 并进行初始化

    # 事件引擎
    event_engine = EventEngine()
    # 把事件引擎附加到主引擎里
    main_engine = MainEngine(event_engine)

    # 添加火币的交互通道
    main_engine.add_gateway(HuobiGateway)
    # main_engine.add_gateway(BitfinexGateway)
    # main_engine.add_gateway(OnetokenGateway)
    # main_engine.add_gateway(OkexfGateway)
    # main_engine.add_gateway(HbdmGateway)

    # 把 app 保存到 apps 和 engines 里

    main_engine.add_app(DataRecorderApp)

    while True:

        # 连接火币平台
    

        # 一天
        sleep(24 * 60 * 60)


if __name__ == "__main__":
    main()
