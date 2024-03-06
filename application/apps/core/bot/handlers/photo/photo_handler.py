from __future__ import annotations

import traceback

from loader import logger

logger.debug(f"{__name__} start import")

from aiogram import types
from aiogram.dispatcher import FSMContext

from apps.core.settyngs import get_sett
from apps.MyBot import MyBot, bot_send_message

from apps.core.utils.misc import rate_limit
from apps.core.bot.filters.custom_filters import filter_message_not_media_group, filter_is_private
from apps.core.bot.messages.messages import Messages
from apps.core.bot.messages.messages_test import msg
from apps.core.bot.data.board_config import BoardConfig as board_config
from apps.core.bot.handlers.photo.qr_photo_processing import qr_code_processing
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.callbacks.select_start_category import select_start_category
from apps.core.bot.reports.report_data_preparation import preparing_violation_data, download_photo

logger.debug(f"{__name__} finish import")
logger.debug("message_handler 'photo'")


@rate_limit(limit=5)
@MyBot.dp.message_handler(filter_message_not_media_group, filter_is_private, content_types=["photo"], state='*')
async def photo_handler(message: types.Message, state: FSMContext, chat_id: str = None):
    """Обработчик сообщений с фото
    """
    if message.chat.type in ['group', 'supergroup']:
        return
    # if message.from_user.id not in [member.user.id for member in await message.chat.get_administrators()]:
    #     return

    hse_user_id = chat_id if chat_id else message.chat.id

    if not await check_user_access(chat_id=hse_user_id):
        return

    current_state = await state.get_state()
    await state.finish()
    logger.info(f'{await fanc_name()} state is finish {current_state = }')

    if not get_sett(cat='enable_features', param='use_photo_handler').get_set():
        msg_text: str = f"{await msg(chat_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=chat_id, text=msg_text, disable_web_page_preview=True)
        return

    logger.info("photo_handler get photo")
    if await qr_code_processing(message, state=state):
        return

    start_photo_message_id = await board_config(state).set_data("start_violation_mes_id", message.message_id)
    logger.info(f"start_photo_message_id message.from_user.id {start_photo_message_id}")

    await preparing_violation_data(message=message, state=state, chat_id=hse_user_id)

    await download_photo(message, hse_user_id)

    await select_start_category(message)


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])
