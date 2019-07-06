"""
Global setting of VN Trader.
"""

from logging import CRITICAL, INFO

from .utility import load_json



# 基本配置信息
SETTINGS = {
    "font.family": "Arial",
    "font.size": 8,

    "log.active": True,
    "log.level": INFO,
    "log.console": True,
    "log.file": True,

    "email.server": "smtp.qq.com",
    "email.port": 465,
    "email.username": "",
    "email.password": "",
    "email.sender": "",
    "email.receiver": "",

    "rqdata.username": "",
    "rqdata.password": "",
    # mysql 数据库
    "database.driver": "mysql",  # see database.Driver
    "database.database": "myvnpycore",  # for sqlite, use this as filepath
    "database.host": "47.107.61.193",
    "database.port": 3306,
    "database.user": "root",
    "database.password": "root",
    "database.authentication_source": "admin",  # for mongodb
}

# Load global setting from json file.
SETTING_FILENAME = "vt_setting.json"
SETTINGS.update(load_json(SETTING_FILENAME))


def get_settings(prefix: str = ""):
    prefix_length = len(prefix)
    return {k[prefix_length:]: v for k, v in SETTINGS.items() if k.startswith(prefix)}
