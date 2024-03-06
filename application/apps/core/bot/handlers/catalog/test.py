from __future__ import annotations

import asyncio
import math

from aiogram import types
from pandas import DataFrame

from apps.MyBot import bot_send_message
from apps.core.bot.handlers.correct_entries.correct_support import check_dataframe, create_lite_dataframe_from_query
from apps.core.database.db_utils import db_get_data_dict_from_table_with_id
from apps.core.database.query_constructor import QueryConstructor


async def test_create(hse_user_id, text_query, query: str = None):
    """

    :param hse_user_id:
    :param text_query:
    :return:
    """

    if not query:
        query_kwargs: dict = {
            "action": 'SELECT', "subject": '*',
            "conditions": {
                "lazy_query": f"`title` LIKE '%{text_query}%'",
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


async def text_processor_level_2(table_dataframe: DataFrame) -> str:
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


async def test():
    """test"""

    call: types.CallbackQuery = None
    hse_user_id = 373084462
    text_query = 'огнетуш'

    quver: str = "SELECT *  FROM core_normativedocuments WHERE title LIKE '%предоставлены%'"
    quver = None

    await test_create(hse_user_id, text_query, query=quver)


if __name__ == '__main__':
    asyncio.run(
        test()
    )
