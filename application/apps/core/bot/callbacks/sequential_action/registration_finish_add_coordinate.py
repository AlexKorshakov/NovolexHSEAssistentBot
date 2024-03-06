from __future__ import annotations

from aiogram import types
from aiogram.dispatcher import FSMContext

from apps.MyBot import MyBot, bot_send_message
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.callbacks.sequential_action.data_answer import notify_user_for_choice
from apps.core.bot.callbacks.sequential_action.registration_finist_keybord import registration_finish_keyboard_inline
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages import Messages
from apps.core.bot.messages.messages_test import msg
from apps.core.bot.reports.report_data import ViolationData
from apps.core.settyngs import get_sett
from loader import logger


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['registration_finish_add_coordinate']), state='*')
async def call_registration_finish_add_coordinate(call: types.CallbackQuery = None, callback_data: dict = None,
                                                  user_id: int | str = None, state: FSMContext = None):
    """Обработка ответов содержащихся в call_registration_finish_add_coordinate
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {call.data = }')

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    if not get_sett(cat='enable_features', param='use_registration_finish_add_coordinate').get_set():
        msg_text: str = f"{await msg(hse_user_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=hse_user_id, text=msg_text, disable_web_page_preview=True)
        return

    await notify_user_for_choice(call, data_answer=call.data)

    await ViolationData.location.set()
    await bot_send_message(chat_id=hse_user_id,
                           text="Отправьте своё местоположение нажав 'Геопозиция' в меню добавления файлов ")

    v_data: dict = await state.get_data()
    if v_data.get("comment"):
        reply_markup = await registration_finish_keyboard_inline()
        await bot_send_message(chat_id=hse_user_id, text=Messages.Registration.confirm, reply_markup=reply_markup)
