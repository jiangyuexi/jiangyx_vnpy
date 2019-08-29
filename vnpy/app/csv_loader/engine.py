"""
Author: Zehua Wei (nanoric)

Load data from a csv file.

Differences to 1.9.2:
    * combine Date column and Time column into one Datetime column

Sample csv file:

```csv
"Datetime","Open","High","Low","Close","Volume"
2010-04-16 09:16:00,3450.0,3488.0,3450.0,3468.0,489
2010-04-16 09:17:00,3468.0,3473.8,3467.0,3467.0,302
2010-04-16 09:18:00,3467.0,3471.0,3466.0,3467.0,203
2010-04-16 09:19:00,3467.0,3468.2,3448.0,3448.0,280
2010-04-16 09:20:00,3448.0,3459.0,3448.0,3454.0,250
2010-04-16 09:21:00,3454.0,3456.8,3454.0,3456.8,109
```

"""

import csv
from datetime import datetime
from typing import TextIO

from vnpy.event import EventEngine
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.database import database_manager
from vnpy.trader.engine import BaseEngine, MainEngine
from vnpy.trader.object import BarData

# CSV 加载 应用
APP_NAME = "CsvLoader"


class CsvLoaderEngine(BaseEngine):
    """"""

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super().__init__(main_engine, event_engine, APP_NAME)
        # 文件路径
        self.file_path: str = ""
        # 交易对符号
        self.symbol: str = ""
        # 交易所
        self.exchange: Exchange = Exchange.SSE
        # 时间间隔
        self.interval: Interval = Interval.MINUTE
        self.datetime_head: str = ""
        self.open_head: str = ""
        self.close_head: str = ""
        self.low_head: str = ""
        self.high_head: str = ""
        self.volume_head: str = ""

    def load_by_handle(
        self,
        f: TextIO,
        symbol: str,
        exchange: Exchange,
        interval: Interval,
        datetime_head: str,
        open_head: str,
        high_head: str,
        low_head: str,
        close_head: str,
        volume_head: str,
        datetime_format: str,
    ):
        """
        load by text mode file handle
        通过文件 句柄加载 bar 数据
        返回 开始 结束 和 总共有多少个 bar
        """
        reader = csv.DictReader(f)

        bars = []
        start = None
        count = 0
        # 循环生成 bar 数据， 放进bar列表里
        for item in reader:
            if datetime_format:
                dt = datetime.strptime(item[datetime_head], datetime_format)
            else:
                dt = datetime.fromisoformat(item[datetime_head])

            bar = BarData(
                symbol=symbol,
                exchange=exchange,
                datetime=dt,
                interval=interval,
                volume=item[volume_head],
                open_price=item[open_head],
                high_price=item[high_head],
                low_price=item[low_head],
                close_price=item[close_head],
                gateway_name="DB",
            )

            bars.append(bar)

            # do some statistics
            count += 1
            if not start:
                start = bar.datetime
        end = bar.datetime

        # insert into database
        # 存放到数据库
        database_manager.save_bar_data(bars)
        return start, end, count

    def load(
        self,
        file_path: str,
        symbol: str,
        exchange: Exchange,
        interval: Interval,
        datetime_head: str,
        open_head: str,
        high_head: str,
        low_head: str,
        close_head: str,
        volume_head: str,
        datetime_format: str,
    ):
        """
        load by filename
        通过文件名 加载数据
        """
        with open(file_path, "rt") as f:
            return self.load_by_handle(
                f,
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                datetime_head=datetime_head,
                open_head=open_head,
                high_head=high_head,
                low_head=low_head,
                close_head=close_head,
                volume_head=volume_head,
                datetime_format=datetime_format,
            )
