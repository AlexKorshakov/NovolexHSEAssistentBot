from loader import logger

logger.debug(f"{__name__} start import")
from aiogram import types
from aiogram.dispatcher.filters import Command
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.utils.misc import rate_limit
from apps.MyBot import MyBot, bot_send_message
from config.config import ADMIN_ID

logger.debug(f"{__name__} finish import")


@rate_limit(limit=5)
@MyBot.dp.message_handler(Command('admin_help'))
async def bot_help_buy(message: types.Message):
    """
    """
    chat_id = message.chat.id
    if not await check_user_access(chat_id=chat_id):
        return

    if str(message.from_user.id) in ADMIN_ID:
        await bot_send_message(chat_id=chat_id, text=f"Команды для админа" '\n'
                             "Добавить / зарегестрировать пользователя /add_user" '\n')
