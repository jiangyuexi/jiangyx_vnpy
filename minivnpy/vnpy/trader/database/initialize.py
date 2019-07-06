""""""
from .database import BaseDatabaseManager, Driver


def init(settings: dict) -> BaseDatabaseManager:
    driver = Driver(settings["driver"])
    if driver is Driver.MONGODB:
        # 如果是 nosql ， 则初始化nosql的数据库
        return init_nosql(driver=driver, settings=settings)
    else:
        # 如果是 关系型数据库 ， 则初始化关系型数据库
        return init_sql(driver=driver, settings=settings)


def init_sql(driver: Driver, settings: dict):
    from .database_sql import init
    keys = {'database', "host", "port", "user", "password"}
    settings = {k: v for k, v in settings.items() if k in keys}
    _database_manager = init(driver, settings)
    return _database_manager


def init_nosql(driver: Driver, settings: dict):
    from .database_mongo import init
    _database_manager = init(driver, settings=settings)
    return _database_manager
