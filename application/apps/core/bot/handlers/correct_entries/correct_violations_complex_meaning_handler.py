from __future__ import annotations

import math

from aiogram.dispatcher import FSMContext
from pandas import DataFrame

from apps.MyBot import bot_send_message
from apps.core.bot.data.board_config import BoardConfig as board_config
from apps.core.bot.handlers.correct_entries.correct_non_act_item_item_correct import RESULT_DICT, COLUMNS_DICT
from apps.core.bot.handlers.correct_entries.correct_support import spotter_data, check_dataframe, \
    create_lite_dataframe_from_query
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import build_inlinekeyboard
from apps.core.database.db_utils import db_get_data_dict_from_table_with_id
from apps.core.database.query_constructor import QueryConstructor
from loader import logger


async def complex_meaning_handler(hse_user_id: int | str, character: str, item_number: int | str,
                                  violations_dataframe: DataFrame, state: FSMContext = None) -> bool:
    """Обработка комплексных характеристик

    :param hse_user_id: int | str id пользователя.
    :param violations_dataframe: DataFrame - DataFrame с данными записи
    :param item_number:  int | str номер записи в база данных
    :param character: str - название изменяемой характеристики записи.
    :return: bool - True если успешно or False
    """
    character_table_name = RESULT_DICT.get(character, None)

    if not character_table_name:
        logger.error(f'{hse_user_id = } {item_number = } {character = } not character in character_table_name')
        await bot_send_message(chat_id=hse_user_id, text=f'Ошибка при изменении показателя {character = }')
        return False

    if character == 'sub_location_id':
        condition: dict = {'main_location_id': violations_dataframe.main_location_id.values[0]}
    elif character == 'normative_documents_id':
        condition: dict = {"category_id": violations_dataframe.category_id.values[0]}
    else:
        condition: dict = {}

    if character_table_name:

        query_kwargs: dict = {
            "action": 'SELECT', "subject": '*',
            "conditions": condition
        }
        query: str = await QueryConstructor(None, character_table_name, **query_kwargs).prepare_data()
        table_dataframe: DataFrame = await create_lite_dataframe_from_query(
            query=query, table_name=character_table_name
        )
        if not await check_dataframe(table_dataframe, hse_user_id):
            return False

        if 'title' not in table_dataframe.columns.values.tolist():
            return False

        title_list: list = table_dataframe['id'].tolist()
        title_list: list = [f"item_{item}" for item in title_list if item is not None]

        # menu_level = board_config.menu_level = 1
        # menu_list = board_config.menu_list = title_list
        # count_col = board_config.count_col = 2

        menu_level = await board_config(state, "menu_level", 1).set_data()
        menu_list = await board_config(state, "menu_list", title_list).set_data()
        count_col = await board_config(state, "count_col", 2).set_data()

        reply_markup = await build_inlinekeyboard(
            some_list=menu_list, num_col=count_col, level=menu_level, called_prefix=f"corr_{character_table_name}_"
        )
        character_text: str = await text_processor_character_text(
            table_dataframe, character, item_number, hse_user_id
        )

        for item_txt in await text_processor(text=character_text):
            await bot_send_message(chat_id=hse_user_id, text=item_txt)

        await bot_send_message(
            chat_id=hse_user_id, text='Выберите значение', reply_markup=reply_markup
        )

        spotter_data['calld_prefix'] = f"corr_{character_table_name}_"
        spotter_data['character_table_name'] = f"{character_table_name}"
        spotter_data['hse_user_id'] = f"{hse_user_id}"
        spotter_data['item_number_text'] = f"{item_number}"
        spotter_data['character'] = f"{character}"

    # await bot_delete_message(chat_id=hse_user_id, message_id=call.message.message_id, sleep_sec=15)


async def text_processor_character_text(table_dataframe: DataFrame, character: str, item_number_text: str | int,
                                        hse_user_id: str | int) -> str:
    """Формирование текста для отправки пользователю

    """
    unique_items_ids: list = table_dataframe.id.unique().tolist()
    unique_items_titles: list = table_dataframe.title.unique().tolist()

    items_text_list: list = []
    for _, (item_id, item_title) in enumerate(zip(unique_items_ids, unique_items_titles), 1):
        item_info: str = f'item_{item_id} : {item_title}'
        items_text_list.append(item_info)

    items_text: str = '\n'.join(items_text_list)

    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "id": item_number_text,
        },
    }
    query: str = await QueryConstructor(None, 'core_violations', **query_kwargs).prepare_data()

    violations_dataframe: DataFrame = await create_lite_dataframe_from_query(query=query, table_name='core_violations')
    if not await check_dataframe(violations_dataframe, hse_user_id):
        return ''

    if character == 'sub_location_id':
        main_table_name = 'core_mainlocation'
        sub_table_name = 'core_sublocation'
        main_character: str = 'main_location_id'
        sub_character: str = 'sub_location_id'

    elif character == 'normative_documents_id':
        main_table_name = 'core_category'
        sub_table_name = 'core_normativedocuments'
        main_character: str = 'category_id'
        sub_character: str = 'normative_documents_id'
    else:
        main_table_name = ''
        sub_table_name = ''
        main_character = ''
        sub_character = ''

    main_character_text: str = await get_item_title_for_id(
        table_name=main_table_name, item_id=violations_dataframe[main_character].values[0]
    )
    sub_character_text: str = await get_item_title_for_id(
        table_name=sub_table_name, item_id=violations_dataframe[sub_character].values[0]
    )

    character_title: str = COLUMNS_DICT.get(character, None)

    header_text: str = f'Выберите значение для показателя Изменить "{character_title}" для ' \
                       f'записи item_number_{item_number_text}'
    old_text: str = f'Значение в базе: {main_character_text} ::: {sub_character_text}'
    footer_text: str = 'Нажмите на кнопку с номером выбранного значения'

    text_list: list = [header_text, old_text, items_text, footer_text]
    final_text: str = '\n\n'.join(text_list)
    return final_text


async def get_item_title_for_id(table_name: str, item_id: int, item_name: str = None) -> str:
    """Получение значения столбца item_name (`title`) по номеру item_id в таблице table_name

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
