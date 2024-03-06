from __future__ import annotations

import asyncio
import math
from datetime import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from pandas import DataFrame

from loader import logger
from apps.MyBot import MyBot, bot_send_message
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.data.board_config import BoardConfig as board_config
from apps.core.bot.filters.custom_filters import filter_is_private
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import build_inlinekeyboard, posts_cb
from apps.core.bot.messages.messages import Messages, LogMessage
from apps.core.bot.messages.messages_test import msg
from apps.core.bot.states import CatalogState
from apps.core.database.query_constructor import QueryConstructor
from apps.core.database.db_utils import (db_get_categories_list,
                                         db_get_data_dict_from_table_with_id,
                                         db_get_data_list,
                                         db_get_clean_headers)
from apps.core.bot.handlers.catalog.catalog_support import (check_dataframe,
                                                            notify_user_for_choice)
from apps.core.settyngs import get_sett


@MyBot.dp.callback_query_handler(lambda call: 'catalog_normative_documents' in call.data)
async def call_catalog_normative_documents_answer(call: types.CallbackQuery, user_id: int | str = None,
                                                  state: FSMContext = None) -> None:
    """Обработка ответов
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {call.data = }')

    if not get_sett(cat='enable_features', param='use_catalog_normative_documents').get_set():
        msg_text: str = f"{await msg(hse_user_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=hse_user_id, text=msg_text, disable_web_page_preview=True)
        return

    reply_markup = await add_catalog_inline_keyboard_with_action()
    text: str = 'Выберите действие'

    await bot_send_message(chat_id=hse_user_id, text=text, reply_markup=reply_markup)


async def add_catalog_inline_keyboard_with_action():
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """

    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            text='Текстовый запрос',
            callback_data=posts_cb.new(id='-', action='cat_normative_documents_text'))
    )
    markup.add(
        types.InlineKeyboardButton(
            text='Открыть справочник',
            callback_data=posts_cb.new(id='-', action='cat_normative_documents_catalog'))
    )
    return markup


@MyBot.dp.callback_query_handler(lambda call: 'cat_normative_documents_text' in call.data)
async def call_catalog_normative_documents_catalog_answer(call: types.CallbackQuery, user_id: int | str = None,
                                                          state: FSMContext = None) -> None:
    """Обработка ответов
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {call.data = }')

    await notify_user_for_choice(call, data_answer=call.data)

    if not get_sett(cat='enable_features', param='use_catalog_normative_documents_text').get_set():
        msg_text: str = f"{await msg(hse_user_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=hse_user_id, text=msg_text, disable_web_page_preview=True)
        return

    await CatalogState.inquiry.set()
    item_txt: str = 'введите простой текстовый зарос'
    await bot_send_message(chat_id=hse_user_id, text=item_txt)


@MyBot.dp.message_handler(filter_is_private, state=CatalogState.all_states)
async def catalog_data_all_states_answer(message: types.Message, state: FSMContext, user_id: int | str = None):
    """Обработка изменений

    :param user_id:
    :param message:
    :param state:
    :return:
    """
    hse_user_id = message.chat.id if message else user_id
    logger.debug(f'{hse_user_id = } {message.text = }')
    logger.info(f'{hse_user_id = } {message.text = }')

    await state.finish()

    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "lazy_query": f"`title` LIKE '%{message.text}%'",
        },
    }
    query: str = await QueryConstructor(None, 'core_normativedocuments', **query_kwargs).prepare_data()

    v_df: DataFrame = await create_lite_dataframe_from_query(query=query, table_name='core_normativedocuments')
    if not await check_dataframe(v_df, hse_user_id):
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены dataframe')
        return

    text = await text_processor_for_text_query(v_df)
    for item_txt in await text_processor(text=text):
        await bot_send_message(chat_id=hse_user_id, text=item_txt)


async def text_processor_for_text_query(table_dataframe: DataFrame) -> str:
    """Формирование текста для отправки пользователю

    """

    items_text_list: list = []
    for index, row in table_dataframe.iterrows():
        category_title = ''
        category_id = row.get("category_id")

        if category_id:
            category_data: dict = await db_get_data_dict_from_table_with_id(
                table_name='core_category', post_id=category_id)
            category_title = category_data.get('title')

        normative_id = row.get("id")
        title = row.get("title")
        normative = row.get("normative")
        procedure = row.get("procedure")
        hashtags = row.get("hashtags")

        item_info: str = f'{index}: id записи: {normative_id} ::: {title}\nКатегория: {category_title}\nНД: {normative}\nУстранение: {procedure}\nhashtag: {hashtags}\n'
        items_text_list.append(item_info)

    items_text: str = '\n'.join([item for item in items_text_list if item is not None])

    return items_text


@MyBot.dp.callback_query_handler(lambda call: 'cat_normative_documents_catalog' in call.data)
async def call_catalog_normative_documents_catalog_answer(call: types.CallbackQuery, user_id: int | str = None,
                                                          state: FSMContext = None) -> None:
    """Обработка ответов
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {call.data = }')

    await notify_user_for_choice(call, data_answer=call.data)

    if not get_sett(cat='enable_features', param='use_catalog_normative_documents_catalog').get_set():
        msg_text: str = f"{await msg(hse_user_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=hse_user_id, text=msg_text, disable_web_page_preview=True)
        return

    clean_categories: list = await db_get_categories_list()

    title_list: list = [f"norm_doc__{num}" for num, item in enumerate(clean_categories, start=1)]

    menu_level = await board_config(state, "menu_level", 1).set_data()
    menu_list = await board_config(state, "menu_list", title_list).set_data()
    count_col = await board_config(state, "count_col", 2).set_data()

    categories_df: DataFrame = DataFrame.from_dict(clean_categories)
    text = await text_processor_categories(categories_df, level=1)

    for item_txt in await text_processor(text=text):
        await bot_send_message(chat_id=hse_user_id, text=item_txt)

    reply_markup = await build_inlinekeyboard(some_list=menu_list, num_col=count_col, level=menu_level, )
    await bot_send_message(chat_id=hse_user_id, text=Messages.Choose.choose_value, reply_markup=reply_markup)


@MyBot.dp.callback_query_handler(lambda call: 'norm_doc__' in call.data)
async def call_level_1_answer(call: types.CallbackQuery, user_id: int | str = None, state: FSMContext = None) -> None:
    """Обработка ответов
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {call.data = }')

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    clean_categories: list = await db_get_categories_list()
    categories_df: DataFrame = DataFrame.from_dict(clean_categories)
    if not await check_dataframe(categories_df, hse_user_id=hse_user_id):
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены dataframe')
        return

    level_1_num: str = call.data
    level_1_list_dicts: list = await get_level_1_list_dict(hse_user_id, categories_df)
    level_1_name: str = [item[level_1_num] for item in level_1_list_dicts if level_1_num in item][0]

    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "category_id": level_1_name,
        },
    }
    query: str = await QueryConstructor(None, 'core_normativedocuments', **query_kwargs).prepare_data()

    v_df: DataFrame = await create_lite_dataframe_from_query(query=query, table_name='core_normativedocuments')
    if not await check_dataframe(v_df, hse_user_id):
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены dataframe')
        return

    text = await text_processor_level_2(v_df)

    for item_txt in await text_processor(text=text):
        await bot_send_message(chat_id=hse_user_id, text=item_txt)


async def get_level_1_list_dict(hse_user_id, dataframe: DataFrame = None):
    """

    :param dataframe:
    :param hse_user_id:
    :return:
    """

    level_1: list = dataframe[dataframe.columns[0]].unique().tolist()
    if not level_1:
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены level_1')
        return

    d_list: list = [{f"norm_doc__{num}": item} for num, item in enumerate(level_1, start=1) if item is not None]
    return d_list


async def text_processor_categories(table_dataframe: DataFrame, level: int = 0) -> str:
    """Формирование текста для отправки пользователю

    """
    unique_items_titles: list = table_dataframe[table_dataframe.columns[level]].unique().tolist()

    items_text_list: list = []
    for i, (item_title) in enumerate(unique_items_titles, 1):
        item_info: str = f'catlevel_{level}__{i} : {item_title}'
        items_text_list.append(item_info)

    items_text: str = '\n'.join(items_text_list)

    header_text: str = Messages.Choose.choose_value
    footer_text: str = 'Нажмите на кнопку с номером выбранного значения'

    fin_list: list = [header_text, items_text, footer_text]
    final_text = '\n\n'.join([item for item in fin_list if item])
    return final_text


async def text_processor_level_2(table_dataframe: DataFrame) -> str:
    """Формирование текста для отправки пользователю

    """

    items_text_list: list = []
    for index, row in table_dataframe.iterrows():
        normative_id = row.get("id")
        title = row.get("title")
        normative = row.get("normative")
        procedure = row.get("procedure")
        hashtags = row.get("hashtags")

        item_info: str = f'{index}: id записи: {normative_id} ::: {title}\nНД: {normative}\nУстранение: {procedure}\nhashtag: {hashtags}\n'
        items_text_list.append(item_info)

    items_text: str = '\n'.join([item for item in items_text_list if item is not None])

    return items_text


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


async def test():
    """test"""

    call: types.CallbackQuery = None
    user_id = 373084462
    await call_catalog_normative_documents_answer(call=call, user_id=user_id)


if __name__ == '__main__':
    asyncio.run(test())
