import os
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .database import BaseDatabaseManager

if "VNPY_TESTING" not in os.environ:
    from ..setting import get_settings
    from .initialize import init
    # vt_setting.json 中 "database."前缀的配置
    settings = get_settings("database.")
    database_manager: "BaseDatabaseManager" = init(settings=settings)
