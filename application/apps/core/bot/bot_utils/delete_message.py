from loader import logger

logger.debug(f"{__name__} start import")
import asyncio
from contextlib import suppress
from aiogram.utils.exceptions import (MessageCantBeDeleted,
                                      MessageCantBeEdited,
                                      MessageToDeleteNotFound,
                                      MessageToEditNotFound)
from apps.MyBot import MyBot
from config.config import BOT_DELETE_MESSAGE

logger.debug(f"{__name__} finish import")


async def bot_delete_message(chat_id: str, message_id: str, sleep_time: int = 1):
    """Удаление сообщений по таймеру

    :param message_id: id сообщения
    :param chat_id: id чата из которого удаляется сообщение
    :param sleep_time:int - время в секундах
    """
    if BOT_DELETE_MESSAGE:
        await asyncio.sleep(sleep_time)
        # with suppress(MessageToEditNotFound, MessageCantBeEdited, MessageCantBeDeleted, MessageToDeleteNotFound):
        #     await MyBot.bot.delete_message(chat_id=chat_id, message_id=message_id)
