from pprint import pprint

from loader import logger

logger.debug(f"{__name__} start import")
import asyncio
from random import choice

from aiogram import Dispatcher, types
from aiogram.dispatcher import DEFAULT_RATE_LIMIT
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled
from apps.core.bot.data.phrases import throttled_answers

logger.debug(f"{__name__} finish import")


class ThrottlingMiddleware(BaseMiddleware):
    """ Стандартный middleware для предотвращения спама через throttling
    """

    def __init__(self, limit: int = 0.5, key_prefix: str = 'antiflood_'):
        self.rate_limit = limit
        self.prefix = key_prefix
        super(ThrottlingMiddleware, self).__init__()

    # noinspection PyUnusedLocal
    async def on_process_message(self, message: types.Message, data: dict):
        if hasattr(message, "media_group_id") and message.media_group_id:
            return

        handler = current_handler.get()
        dispatcher = Dispatcher.get_current()

        if handler:
            limit = getattr(handler, 'throttling_rate_limit', self.rate_limit)
            key = getattr(handler, 'throttling_key', f"{self.prefix}_{handler.__name__}")
        else:
            limit = self.rate_limit
            key = f"{self.prefix}_message"

        try:
            await dispatcher.throttle(key, rate=limit)

        except Throttled as t:
            await self.message_throttled(message, t)
            raise CancelHandler()

    async def message_throttled(self, message: types.Message, throttled: Throttled):

        handler = current_handler.get()
        logger.debug(f'@{message.from_user.username}:{message.from_user.id} спамит командой {message.text}')
        limit = getattr(handler, 'throttling_rate_limit', self.rate_limit)
        delta = throttled.rate - throttled.delta

        if throttled.exceeded_count <= 2:
            pprint(await throttled_answers_generator(limit=limit), width=200)
            # await message.reply(text=await throttled_answers_generator(limit=limit))

        await asyncio.sleep(delta)


async def throttled_answers_generator(limit: int) -> str:
    return choice(throttled_answers).format(limit=limit)
