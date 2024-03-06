from __future__ import annotations

from loader import logger

logger.debug(f"{__name__} start import")
import traceback

from aiogram import types
from aiogram.dispatcher import FSMContext

from apps.core.bot.filters.custom_filters import (filter_is_private)
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.messages.messages import Messages
from apps.MyBot import MyBot, bot_send_message

logger.debug(f"{__name__} finish import")


@MyBot.dp.message_handler(filter_is_private, content_types=['text'], state='*')
async def text_message_handler_in_private(message: types.Message, state: FSMContext = None):
    """"""
    if message.chat.type in ['group', 'supergroup']:
        return
    # if message.from_user.id not in [member.user.id for member in await message.chat.get_administrators()]:
    #     return

    chat_id = message.chat.id
    if not await check_user_access(chat_id=chat_id):
        return

    # current_state = await state.get_state()
    # await state.finish()
    # logger.info(f'{await fanc_name()} state is finish {current_state = }')

    get_message_bot = message.text.strip().lower()
    logger.info(f'get_message_bot {get_message_bot}')
    await bot_send_message(chat_id=chat_id, text=f'Это текст \n {get_message_bot} \n {Messages.help_message}')


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])
