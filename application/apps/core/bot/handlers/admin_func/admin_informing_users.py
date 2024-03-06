from __future__ import annotations

from aiogram import types
from aiogram.dispatcher import FSMContext

from apps.MyBot import MyBot, bot_send_message
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages import Messages
from apps.core.bot.messages.messages_test import msg
from apps.core.settyngs import get_sett
from loader import logger


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['admin_informing_users']), state='*')
async def admin_add_user_answer(call: types.CallbackQuery, callback_data: dict[str, str],
                                state: FSMContext = None, user_id: int | str = None):
    """

    :return:
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {call.data = }')

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    if not get_sett(cat='enable_features', param='use_bagration_admin_add_user').get_set():
        msg_text: str = f"{await msg(hse_user_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=hse_user_id, text=msg_text, disable_web_page_preview=True)
        return

    msg_text = await msg(hse_user_id, cat='error', msge='error_action', default=Messages.Error.error_action).g_mas()
    await bot_send_message(chat_id=hse_user_id, text=msg_text)
