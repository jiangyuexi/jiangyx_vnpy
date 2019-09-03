from time import sleep

from vnpy.app.cta_backtester import CtaBacktesterApp
from vnpy.app.cta_backtester.ui.no_widget import BacktesterManager
from vnpy.app.cta_strategy import CtaStrategyApp
from vnpy.app.cta_strategy.ui.no_widget import CtaManager, StrategyManager
from vnpy.app.data_recorder.ui.no_widget import ConnectNoDialog
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
    main_engine.add_gateway(OkexfGateway)

    # 添加火币的交互通道
    # 从json文件加载配置
    # settings = load_json("connect_huobi.json")
    # for setting in settings["Keys"]:
    #     # self.main_engine.connect(setting, self.gateway_name)
    #     # sleep(10)
    #     main_engine.add_gateway(HuobiGateway)
    # main_engine.add_gateway(HuobiGateway)

    # main_engine.add_gateway(BitfinexGateway)
    # main_engine.add_gateway(OnetokenGateway)
    # main_engine.add_gateway(OkexGateway)
    # main_engine.add_gateway(HbdmGateway)

    # 把 app 保存到 apps 和 engines 里
    main_engine.add_app(CtaStrategyApp)
    main_engine.add_app(CtaBacktesterApp)
    main_engine.add_app(CsvLoaderApp)
    main_engine.add_app(AlgoTradingApp)
    main_engine.add_app(DataRecorderApp)

    # 获取所有交易通道 名字
    gateway_names = main_engine.get_all_gateway_names()
    for name in gateway_names:
        # 连接火币平台
        connect = ConnectNoDialog(main_engine=main_engine, gateway_name=name)
        connect.connect()
        sleep(1)
        # 配置回测系统
        # backtester = BacktesterManager(main_engine=main_engine, event_engine=event_engine, gateway_name=name)
        # backtester.start_backtesting()
        # CTA 管理器
        ctamanager = CtaManager(main_engine=main_engine, event_engine=event_engine)
        data = {'strategy_name': 'testjiang', 'vt_symbol': 'BTC-USD-190927.OKEX', 'class_name':
            'TestStrategy', 'author': '用Python的交易员', 'parameters': {'test_trigger': 10},
                'variables': {'inited': False, 'trading': False, 'pos': 0, 'tick_count': 0, 'test_all_done': False}}

        strategymanager = StrategyManager(cta_manager=ctamanager, cta_engine=ctamanager.cta_engine, data=data)
        strategymanager.init_strategy()
        strategymanager.start_strategy()

    while True:
        sleep(100000)


if __name__ == "__main__":
    main()
