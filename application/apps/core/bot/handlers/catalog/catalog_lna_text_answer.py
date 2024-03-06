from __future__ import annotations

import traceback

from aiogram import types
from aiogram.dispatcher import FSMContext
from pandas import DataFrame

from apps.MyBot import MyBot, bot_send_message, bot_send_document
from apps.core.bot.data.board_config import BoardConfig as board_config
from apps.core.bot.filters.custom_filters import is_lna_text_answer
from apps.core.bot.handlers.catalog.catalog_support import check_dataframe, notify_user_for_choice, \
    get_dataframe_from_local_files
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages import Messages
from apps.core.bot.messages.messages_test import msg
from apps.core.settyngs import get_sett
from loader import logger


@MyBot.dp.callback_query_handler(is_lna_text_answer, state='*')
async def catalog_lna_text_answer(call: types.CallbackQuery, user_id: int | str = None,
                                  state: FSMContext = None) -> None:
    """Обработка ответов

    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {call.data = }')

    await notify_user_for_choice(call, data_answer=call.data)

    lna_send_file = call.data.replace('_lna_file_', '').replace('...', '')
    await board_config(state, "lna_send_file", lna_send_file).set_data()

    if not get_sett(cat='enable_features', param='use_catalog_lna').get_set():
        msg_text: str = f"{await msg(hse_user_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=hse_user_id, text=msg_text, disable_web_page_preview=True)
        return

    reply_markup = await add_catalog_inline_keyboard_with_action()
    text: str = 'Выберите действие '

    await bot_send_message(chat_id=hse_user_id, text=text, reply_markup=reply_markup)


async def add_catalog_inline_keyboard_with_action():
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """

    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            text='Скачать себе',
            callback_data=posts_cb.new(id='-', action='cat_lna_download_file'))
    )
    markup.add(types.InlineKeyboardButton(
        text='Отправить',
        callback_data=posts_cb.new(id='-', action='cat_lna_send_file'))
    )
    return markup


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['cat_lna_download_file']))
async def call_bagration_admin_get_pass_report(call: types.CallbackQuery = None, callback_data: dict = None,
                                               user_id: int | str = None, state: FSMContext = None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST

    """
    hse_user_id = call.message.chat.id if call else user_id
    if call: logger.debug(f'{hse_user_id = } {call.data = }')

    v_data: dict = await state.get_data()
    lna_send_file = v_data.get('lna_send_file')

    await notify_user_for_choice(call, data_answer=call.data)

    dataframe: DataFrame = await get_dataframe_from_local_files(hse_user_id, column_number=0)
    if not await check_dataframe(dataframe, hse_user_id=hse_user_id):
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены dataframe')
        return

    mask = dataframe['file'].str.contains(f"{lna_send_file}", case=False, regex=True, na=False)
    df_res: DataFrame = dataframe.loc[mask]

    doc_path: str = df_res['file_path'].values[0]
    caption: str = 'Отправлено'

    await bot_send_document(
        chat_id=hse_user_id, doc_path=doc_path, caption=caption, calling_fanc_name=await fanc_name()
    )


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['cat_lna_send_file']))
async def call_bagration_admin_get_pass_report(call: types.CallbackQuery = None, callback_data: dict = None,
                                               user_id: int | str = None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST

    """

    hse_user_id = call.message.chat.id if call else user_id
    if call: logger.debug(f'{hse_user_id = } {call.data = }')

    await notify_user_for_choice(call, data_answer=call.data)

    msg_text = await msg(hse_user_id, cat='error', msge='error_action', default=Messages.Error.error_action).g_mas()
    await bot_send_message(chat_id=hse_user_id, text=msg_text)


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])
