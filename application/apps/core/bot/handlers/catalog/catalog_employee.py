from __future__ import annotations

import asyncio

from aiogram import types
from aiogram.dispatcher import FSMContext

from apps.MyBot import MyBot, bot_send_message
from apps.core.bot.data.board_config import BoardConfig as board_config
from apps.core.bot.handlers.catalog.catalog_support import (get_dataframe,
                                                            text_processor_level,
                                                            text_processor,
                                                            get_nan_value_text,
                                                            list_number,
                                                            level_1_column,
                                                            check_dataframe)
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import build_inlinekeyboard, posts_cb
from apps.core.bot.messages.messages import Messages
from apps.core.bot.messages.messages_test import msg

from apps.core.bot.states.CatalogState import CatalogStateEmployee
from apps.core.settyngs import get_sett
from loader import logger


@MyBot.dp.callback_query_handler(lambda call: 'catalog_employee' in call.data)
async def call_catalog_employee_answer(call: types.CallbackQuery, user_id: int | str = None,
                                       state: FSMContext = None) -> None:
    """Обработка ответов
    """

    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {call.data = }')

    if not get_sett(cat='enable_features', param='use_catalog_employee').get_set():
        msg_text: str = f"{await msg(hse_user_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=hse_user_id, text=msg_text, disable_web_page_preview=True)
        return

    reply_markup = await add_employee_inline_keyboard_with_action()
    text: str = 'Выберите действие'

    await bot_send_message(chat_id=hse_user_id, text=text, reply_markup=reply_markup)


async def add_employee_inline_keyboard_with_action():
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """

    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            text='Текстовый запрос',
            callback_data=posts_cb.new(id='-', action='cat_employee_text'))
    )
    markup.add(
        types.InlineKeyboardButton(
            text='Открыть справочник',
            callback_data=posts_cb.new(id='-', action='cat_employee_catalog'))
    )
    return markup


@MyBot.dp.callback_query_handler(lambda call: 'cat_employee_text' in call.data)
async def call_catalog_employee_catalog_answer(call: types.CallbackQuery, user_id: int | str = None,
                                               state: FSMContext = None) -> None:
    """Обработка ответов
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {call.data = }')

    if not get_sett(cat='enable_features', param='use_catalog_employee_text').get_set():
        msg_text: str = f"{await msg(hse_user_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=hse_user_id, text=msg_text, disable_web_page_preview=True)
        return

    await CatalogStateEmployee.inquiry.set()
    item_txt: str = 'введите простой текстовый зарос'
    await bot_send_message(chat_id=hse_user_id, text=item_txt)


@MyBot.dp.callback_query_handler(lambda call: 'cat_employee_catalog' in call.data)
async def call_catalog_normative_documents_catalog_answer(call: types.CallbackQuery, user_id: int | str = None,
                                                          state: FSMContext = None) -> None:
    """Обработка ответов
    """

    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {call.data = }')

    if not get_sett(cat='enable_features', param='use_catalog_employee_catalog').get_set():
        msg_text: str = f"{await msg(hse_user_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=hse_user_id, text=msg_text, disable_web_page_preview=True)
        return

    dataframe = await get_dataframe(hse_user_id, column_number=list_number)
    if not await check_dataframe(dataframe, hse_user_id=hse_user_id):
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены dataframe')
        return

    level_1: list = dataframe[dataframe.columns[level_1_column]].unique().tolist()
    if not level_1:
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены level_1')
        return

    title_list: list = [f"level_1__{num}" for num, item in enumerate(level_1, start=1) if item is not None]

    menu_level = await board_config(state, "menu_level", 1).set_data()
    menu_list = await board_config(state, "menu_list", title_list).set_data()
    count_col = await board_config(state, "count_col", 2).set_data()

    nan_value_text: str = await get_nan_value_text(hse_user_id, dataframe, column_nom=level_1_column)
    text: str = await text_processor_level(
        dataframe,
        # nan_value_text,
        level=level_1_column
    )

    for item_txt in await text_processor(text=text):
        await bot_send_message(chat_id=hse_user_id, text=item_txt)

    reply_markup = await build_inlinekeyboard(some_list=menu_list, num_col=count_col, level=menu_level, )
    await bot_send_message(chat_id=hse_user_id, text=Messages.Choose.choose_value, reply_markup=reply_markup)


async def test():
    """test"""

    call: types.CallbackQuery = None
    user_id = 373084462
    await call_catalog_employee_answer(call=call, user_id=user_id)


if __name__ == '__main__':
    asyncio.run(test())
