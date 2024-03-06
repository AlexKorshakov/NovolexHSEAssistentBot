from __future__ import annotations

from aiogram import types
from aiogram.dispatcher import FSMContext

from apps.MyBot import MyBot, bot_send_message
from apps.core.bot.handlers.catalog.catalog_support import notify_user_for_choice
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb, add_previous_paragraph_button
from apps.core.bot.messages.messages import Messages
from apps.core.bot.messages.messages_test import msg
from apps.core.bot.states.CatalogState import CatalogStateLNA
from apps.core.settyngs import get_sett
from apps.core.bot.data.board_config import BoardConfig as board_config
from loader import logger


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['catalog_lna']))
async def call_catalog_lna_answer(call: types.CallbackQuery, callback_data: dict = None, user_id: int | str = None,
                                  state: FSMContext = None, data_answer: str = None) -> None:
    """Обработка ответов
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {call.data = }')

    await notify_user_for_choice(call, data_answer=call.data)

    if not get_sett(cat='enable_features', param='use_catalog_lna').get_set():
        msg_text: str = f"{await msg(hse_user_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=hse_user_id, text=msg_text, disable_web_page_preview=True)
        return

    reply_markup = await add_catalog_inline_keyboard_with_action()

    text: str = 'Выберите действие'

    previous_level: str = 'call_catalog_func_handler'
    await board_config(state, "previous_level", ).set_data()

    reply_markup = await add_previous_paragraph_button(reply_markup, previous_level)

    await bot_send_message(chat_id=hse_user_id, text=text, reply_markup=reply_markup)


async def add_catalog_inline_keyboard_with_action():
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """

    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            text='Текстовый запрос',
            callback_data=posts_cb.new(id='-', action='cat_lna_text'))
    )
    markup.add(
        types.InlineKeyboardButton(
            text='Открыть справочник',
            callback_data=posts_cb.new(id='-', action='cat_lna_catalog'))
    )
    return markup


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['cat_lna_text']))
async def call_catalog_lna_catalog_answer(call: types.CallbackQuery, callback_data: dict = None,
                                          user_id: int | str = None, state: FSMContext = None) -> None:
    """Обработка ответов
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {call.data = }')

    await notify_user_for_choice(call, data_answer=call.data)

    if not get_sett(cat='enable_features', param='use_catalog_lna_text').get_set():
        msg_text: str = f"{await msg(hse_user_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=hse_user_id, text=msg_text, disable_web_page_preview=True)
        return

    await CatalogStateLNA.inquiry.set()
    item_txt: str = 'введите простой текстовый зарос'
    await bot_send_message(chat_id=hse_user_id, text=item_txt)


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['cat_lna_catalog']))
async def call_catalog_lna_catalog_answer(call: types.CallbackQuery, callback_data: dict = None,
                                          user_id: int | str = None, state: FSMContext = None) -> None:
    """Обработка ответов
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {call.data = }')

    await notify_user_for_choice(call, data_answer=call.data)

    if not get_sett(cat='enable_features', param='use_cat_lna_catalog').get_set():
        msg_text: str = f"{await msg(hse_user_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=hse_user_id, text=msg_text, disable_web_page_preview=True)
        return

    msg_text = await msg(hse_user_id, cat='error', msge='error_action', default=Messages.Error.error_action).g_mas()
    await bot_send_message(chat_id=hse_user_id, text=msg_text)
