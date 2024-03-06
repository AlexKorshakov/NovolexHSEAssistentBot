from loader import logger
from .album_middleware import AlbumMiddleware

logger.debug(f"{__name__} start import")
from aiogram import Dispatcher
from .throttling import ThrottlingMiddleware

logger.debug(f"{__name__} finish import")


async def setup_middlewares(dp: Dispatcher):
    logger.info(f"{dp.bot._me.first_name} Установка middlewares...")

    dp.middleware.setup(ThrottlingMiddleware())
    dp.middleware.setup(AlbumMiddleware())
