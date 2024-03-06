from __future__ import annotations

import math
from datetime import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from pandas import DataFrame

from apps.MyBot import MyBot, bot_send_message, bot_delete_message, bot_delete_markup
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.data.board_config import BoardConfig as board_config
from apps.core.bot.handlers.correct_entries.correct_support import create_user_dataframe
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb, build_inlinekeyboard
from apps.core.bot.messages.messages import Messages, LogMessage
from apps.core.database.db_utils import (db_get_data_list,
                                         db_get_clean_headers,
                                         db_get_data_dict_from_table_with_id)
from apps.core.database.query_constructor import QueryConstructor
from loader import logger


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['correct_non_act_item']))
async def call_correct_item_violations(call: types.CallbackQuery = None, callback_data: dict[str, str] = None,
                                       user_id: int | str = None, state: FSMContext = None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {callback_data = }')

    # await bot_delete_markup(message=call.message)

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    if not call:
        await bot_send_message(chat_id=hse_user_id, text=Messages.Error.error_call)
        return

    if not call.message.values['text']:
        await bot_send_message(chat_id=hse_user_id, text=Messages.Error.error_call_text)
        return

    query_kwargs: dict = {
        "action": 'SELECT',
        "subject": '*',
        "conditions": {
            "finished_id": "!= 1",
            "status_id": "!= 1",
            "act_number": ""
        },
    }
    query: str = await QueryConstructor(None, 'core_violations', **query_kwargs).prepare_data()

    violations_dataframe: DataFrame = await create_lite_dataframe_from_query(query=query, table_name='core_violations')
    if violations_dataframe is None:
        text_violations: str = 'Незакрытых записей вне актов не обнаружено!'
        await bot_send_message(chat_id=hse_user_id, text=text_violations)
        return True

    if violations_dataframe.empty:
        logger.error(f'{hse_user_id = } {Messages.Error.dataframe_is_empty}  \n{query = }')
        return False

    user_violations_df: DataFrame = await create_user_dataframe(hse_user_id, violations_dataframe)

    if user_violations_df is None:
        text_violations: str = 'Незакрытых записей вне актов не обнаружено!'
        await bot_send_message(chat_id=hse_user_id, text=text_violations)
        return True

    if user_violations_df.empty:
        return False

    text_violations: str = await text_processor_user_violations(user_violations_df)
    for item_txt in await text_processor(text=text_violations):
        await bot_send_message(chat_id=hse_user_id, text=item_txt)

    reply_markup: types.InlineKeyboardMarkup = await add_correct_inline_keyboard_with_action(user_violations_df, state = state)

    await bot_send_message(chat_id=hse_user_id, text="Выберите запись", reply_markup=reply_markup)

    msg_id = call.message.message_id
    await bot_delete_message(chat_id=hse_user_id, message_id=msg_id, sleep_sec=15)

    return True


async def add_correct_inline_keyboard_with_action(user_violations: DataFrame, state: FSMContext = None):
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """

    unique_acts_numbers: list = user_violations.id.unique().tolist()
    unique_acts_numbers: list = [f'item_number_{item}' for item in unique_acts_numbers if item]

    # menu_level = board_config.menu_level = 1
    # menu_list = board_config.menu_list = unique_acts_numbers
    # count_col = board_config.count_col = 2

    menu_level = await board_config(state, "menu_level", 1).set_data()
    menu_list = await board_config(state, "menu_list", unique_acts_numbers).set_data()
    count_col = await board_config(state, "count_col", 2).set_data()

    reply_markup = await build_inlinekeyboard(some_list=menu_list, num_col=count_col, level=menu_level)

    return reply_markup


@MyBot.dp.callback_query_handler(lambda call: 'item_number_' in call.data)
async def item_number_answer(call: types.CallbackQuery, user_id: str = None) -> None:
    """Обработка ответов
    """

    non_act_item_number = call.data

    hse_user_id = call.message.chat.id if call else user_id
    logger.info(f'{hse_user_id = } {call.data = }')

    await bot_delete_markup(message=call.message)

    text_violations = f'Выбрано {non_act_item_number}'

    reply_markup = await add_act_inline_keyboard_with_action()

    await bot_send_message(chat_id=hse_user_id, text=text_violations, reply_markup=reply_markup)

    await bot_delete_message(chat_id=hse_user_id, message_id=call.message.message_id, sleep_sec=15)


async def add_act_inline_keyboard_with_action():
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """

    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(
        text='Финализировать и записать',
        callback_data=posts_cb.new(id='-', action='correct_non_act_item_finalize'))
    )
    markup.add(types.InlineKeyboardButton(
        text='Исправить отдельные параметры',
        callback_data=posts_cb.new(id='-', action='correct_non_act_item_item_correct'))
    )
    markup.add(types.InlineKeyboardButton(
        text='Удалить пункт полностью',
        callback_data=posts_cb.new(id='-', action='correct_non_act_item_delete'))
    )
    return markup


async def text_processor_user_violations(user_violations_df: DataFrame) -> str:
    """Формирование текста для отправки пользователю"""

    unique_items_ids: list = user_violations_df.id.unique().tolist()

    items_description: list = []
    len_unique_acts: int = 0

    for item_id in unique_items_ids:

        item_violations_dataframe = user_violations_df.copy(deep=True)
        item_df = item_violations_dataframe.loc[item_violations_dataframe['id'] == item_id]

        if item_violations_dataframe.empty:
            logger.error(f'{Messages.Error.dataframe_is_empty}')
            continue

        created_at = item_df['created_at'].values[0]
        item_status = await get_item_title_for_id(
            'core_status', item_id=item_df['status_id'].values[0]
        )
        item_main_category = await get_item_title_for_id(
            table_name='core_maincategory', item_id=item_df['main_category_id'].values[0]
        )
        item_category = await get_item_title_for_id(
            table_name='core_category', item_id=item_df['category_id'].values[0]
        )
        item_general_contractor_id = await get_item_title_for_id(
            table_name='core_generalcontractor', item_id=item_df['general_contractor_id'].values[0]
        )
        item_main_location = await get_item_title_for_id(
            table_name='core_mainlocation', item_id=item_df['main_location_id'].values[0]
        )
        item_sub_location = await get_item_title_for_id(
            table_name='core_sublocation', item_id=item_df['sub_location_id'].values[0]
        )
        item_description = item_df['description'].values[0]
        elimination_time = await get_item_title_for_id(
            table_name='core_eliminationtime', item_id=item_df['elimination_time_id'].values[0]
        )
        normative_documents_title = await get_item_title_for_id(
            table_name='core_normativedocuments', item_id=item_df['normative_documents_id'].values[0],
        )
        normative_documents_desc = await get_item_title_for_id(
            table_name='core_normativedocuments', item_id=item_df['normative_documents_id'].values[0],
            item_name='normative'
        )

        item_info = f'Ном пункта: {item_id} от {created_at}\n' \
                    f'Статус: {item_status} \n' \
                    f'Устранить до: {elimination_time} ' \
                    f'Подрядчик: {item_general_contractor_id} \n' \
                    f'Территория: {item_main_location} - {item_sub_location} \n' \
                    f'Направление: {item_main_category} - Категория: {item_category}\n' \
                    f'Описание: {item_description} \n' \
                    f'Подкатегория: {normative_documents_title} ' \
                    f'Нормативка: {normative_documents_desc}\n'

        items_description.append(item_info)
        len_unique_acts += 1

    items_text: str = '\n'.join(items_description)

    header_text: str = f'Всего пунктов {len_unique_acts}'
    final_text: str = f'{header_text} \n\n{items_text}'
    return final_text


async def text_processor(text: str = None) -> list:
    """Принимает data_list_to_text[] для формирования текста ответа
    Если len(text) <= 3500 - отправляет [сообщение]
    Если len(text) > 3500 - формирует list_with_parts_text = []

    :param text:
    :return: list - list_with_parts_text
    """
    if not text:
        return []

    step = 3500
    if len(text) <= step:
        return [text]

    len_parts = math.ceil(len(text) / step)
    list_with_parts_text: list = [text[step * (i - 1):step * i] for i in range(1, len_parts + 1)]

    return list_with_parts_text


async def get_item_title_for_id(table_name: str, item_id: int, item_name: str = None) -> str:
    """

    :param item_name:
    :param table_name:
    :param item_id:
    :return:
    """
    item_dict: dict = await db_get_data_dict_from_table_with_id(
        table_name=table_name,
        post_id=item_id
    )

    item_name = item_name if item_name else 'title'
    item_text: str = item_dict.get(item_name, '')
    return item_text


async def create_lite_dataframe_from_query(query: str, table_name: str) -> DataFrame or None:
    """Возвращает list с нарушениями

    :return: DataFrame or None
    """

    if not query:
        logger.error(f"{LogMessage.Check.no_query} ::: {await get_now()}")
        return None

    violations_data: list = await db_get_data_list(query=query)

    if not violations_data:
        logger.debug(f"{LogMessage.Check.no_violations} ::: {await get_now()}")
        return None

    clean_headers = await db_get_clean_headers(table_name=table_name)

    try:
        dataframe = DataFrame(violations_data, columns=clean_headers)
        return dataframe
    except Exception as err:
        logger.error(f"create_dataframe {repr(err)}")
        return None


async def get_now() -> str:
    """Возвращает текущую дату и время.
    :return: str
    """
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")
