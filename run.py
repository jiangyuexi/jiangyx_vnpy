
from vnpy.event import EventEngine

from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

from vnpy.gateway.bitmex import BitmexGateway
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


from vnpy.app.csv_loader import CsvLoaderApp
from vnpy.app.algo_trading import AlgoTradingApp
# from vnpy.app.cta_backtester import CtaBacktesterApp
from vnpy.app.data_recorder import DataRecorderApp
from vnpy.trader.utility import load_json


def main():
    """"""
    # 创建 QApplication  对象 并进行初始化
    qapp = create_qapp()
    # 事件引擎
    event_engine = EventEngine()
    # 把事件引擎附加到主引擎里
    main_engine = MainEngine(event_engine)
    # main_engine.add_gateway(XtpGateway)
    # main_engine.add_gateway(CtpGateway)
    # main_engine.add_gateway(FemasGateway)
    # main_engine.add_gateway(IbGateway)
    # main_engine.add_gateway(FutuGateway)

    # bitmex交易所
    # main_engine.add_gateway(BitmexGateway)
    # main_engine.add_gateway(TigerGateway)
    # main_engine.add_gateway(OesGateway)
    # main_engine.add_gateway(OkexfGateway)


    # 添加火币的交互通道
    # 从json文件加载配置
    # settings = load_json("connect_huobi.json")
    # for setting in settings["Keys"]:
    #     # self.main_engine.connect(setting, self.gateway_name)
    #     # sleep(10)
    #     main_engine.add_gateway(HuobiGateway)
    main_engine.add_gateway(HuobiGateway)



    # main_engine.add_gateway(BitfinexGateway)
    # main_engine.add_gateway(OnetokenGateway)
    main_engine.add_gateway(OkexGateway)
    # main_engine.add_gateway(HbdmGateway)

    # 把 app 保存到 apps 和 engines 里
    # main_engine.add_app(CtaStrategyApp)
    # main_engine.add_app(CtaBacktesterApp)
    # main_engine.add_app(CsvLoaderApp)
    # main_engine.add_app(AlgoTradingApp)
    main_engine.add_app(DataRecorderApp)

    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()
    # qt 事件循环
    qapp.exec()


if __name__ == "__main__":
    main()
