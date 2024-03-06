from __future__ import annotations

from itertools import chain

from aiogram import types
from aiogram.dispatcher import FSMContext
from pandas import DataFrame

from apps.MyBot import MyBot, bot_send_message
from apps.core.bot.data.board_config import BoardConfig as board_config
from apps.core.bot.filters.custom_filters import filter_is_private
from apps.core.bot.handlers.catalog.catalog_support import (list_number,
                                                            get_dataframe_from_local_files,
                                                            notify_user_for_choice)
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import (build_inlinekeyboard,
                                                                        build_text_for_inlinekeyboard)
from apps.core.bot.handlers.catalog.catalog_support import check_dataframe
from apps.core.bot.states.CatalogState import CatalogStateLNA
from loader import logger


@MyBot.dp.message_handler(filter_is_private, state=CatalogStateLNA.all_states)
async def catalog_data_all_states_answer(message: types.Message = None, user_id: int | str = None, text: str = None,
                                         state: FSMContext = None):
    """Обработка изменений

    :param text:
    :param user_id:
    :param message:
    :param state:
    :return:
    """
    hse_user_id = message.chat.id if message else user_id
    logger.debug(f'{hse_user_id = } {message.text = }')
    logger.info(f'{hse_user_id = } {message.text = }')

    await state.finish()

    text_too_search: str = message.text if message else text

    await notify_user_for_choice(message, data_answer=text_too_search)

    dataframe: DataFrame = await get_dataframe_from_local_files(hse_user_id, column_number=list_number)
    if not await check_dataframe(dataframe, hse_user_id=hse_user_id):
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены dataframe')
        return

    await text_processor_for_text_query(hse_user_id, dataframe, text_too_search=text_too_search, state=state)


async def text_processor_for_text_query(hse_user_id: str | int, table_dataframe: DataFrame,
                                        text_too_search: str, state: FSMContext = None) -> str:
    """Формирование текста для отправки пользователю

    """
    items_text_list: list = []

    if not text_too_search:
        return 'данные не найдены'

    # try:
    #     text_too_search: int = int(text_too_search)

    # except ValueError as err:
    #     logger.info(f'{hse_user_id = } {text_too_search = } {repr(err)}')

    # if isinstance(text_too_search, int):
    #     items_text_list: list = await processor_search_if_int(table_dataframe, text_too_search)

    if isinstance(text_too_search, str):
        items_text_list: list = await processor_search_if_str(table_dataframe, text_too_search)

    if not items_text_list:
        return await no_results_answer(chat_id=hse_user_id, state=state)

    dat_list: list = await prepare_text(items_text_list, condition='file')
    if not dat_list:
        return await no_results_answer(chat_id=hse_user_id, state=state)

    result = await sent_message(hse_user_id, dat_list, state=state)
    if not result:
        return await no_results_answer(chat_id=hse_user_id, state=state)

    return result


async def no_results_answer(chat_id, state) -> str:
    """

    :param chat_id:
    :return:
    """
    previous_level: str = 'call_catalog_lna_catalog_answer'
    await board_config(state, "previous_level", ).set_data()

    reply_markup = await build_inlinekeyboard(
        previous_level=previous_level
    )
    await bot_send_message(chat_id=chat_id, text='Данные запроса не найдены', reply_markup=reply_markup)
    return ''


async def sent_message(user_id, dat_list: list, state: FSMContext = None):
    """

    :param state:
    :param user_id:
    :param dat_list:
    :return:
    """
    commands_action_list: list = [command.get('file') for command in dat_list if isinstance(command.get('file'), str)]
    commands_action_list = await check_list_bytes_len(commands_action_list, target_parameter=45)

    menu_level: int = await board_config(state, "menu_level", 1).set_data()
    menu_list: list = await board_config(state, "menu_list", commands_action_list).set_data()
    count_col: int = await board_config(state, "count_col", 2).set_data()

    previous_level: str = 'call_catalog_lna_catalog_answer'
    await board_config(state, "previous_level", ).set_data()

    data_list = [command for command in dat_list if command is not None]
    zipped_list: list = list(zip(commands_action_list, data_list))
    text_list: list = [f"{await get_character_text(item)}" for item in zipped_list]
    menu_text_list = await board_config(state, "menu_text_list", text_list).set_data()

    reply_markup = await build_inlinekeyboard(
        some_list=menu_list, num_col=count_col, previous_level=previous_level, called_prefix='_lna_file_',
        level=menu_level, state=state
    )
    reply_text = await build_text_for_inlinekeyboard(
        some_list=menu_text_list, level=menu_level
    )

    text = f'Choose action\n\n{reply_text}'
    await bot_send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
    return text


async def check_list_bytes_len(list_for_check: list, target_parameter: int = 60) -> list:
    """Проверка длинны записи в байтах для формирования надписей кнопок
    текст длиннее 64 байт обрезается, добавляются точки
    """
    processed_values: len = []
    for item in list_for_check:
        if len(item.encode('utf-8')) > target_parameter:
            logger.debug(f" {item} : {len(item.encode('utf-8'))}")

            while int(len(item.encode('utf-8'))) > target_parameter - 1:
                item = item[:-1]
                logger.debug(f" {item} : {len(item.encode('utf-8'))}")

            item = item[:-2] + '...'
            logger.debug(f" {item} : {len(item.encode('utf-8'))}")

        processed_values.append(item)

    return processed_values


async def get_character_text(param: list | str) -> list | str:
    """

    :return:
    """
    if not param:
        return ''

    if isinstance(param, list):
        if not param: return []

        text_list: list = [
            f"item {item.get('id')} {item.get('title')} " for item in param if
            item.get('id') is not None
        ]
        return text_list

    if isinstance(param, dict):
        if not param: return ''

        key_list: list = [f'{k}: {v}' for k, v in param.items()]
        text_list: str = f"item {param.get('title')}\n\n{', '.join(key_list)}"
        return text_list

    if isinstance(param, tuple):
        if not param: return ''

        text_list: str = f"{param[0]}:\n{', '.join([f'{k}: {v}' for k, v in param[1].items()])}"
        return text_list

    return ''


async def processor_search_if_int(table_dataframe: DataFrame, text_too_search: int) -> list:
    """

    :param table_dataframe:
    :param text_too_search:
    :return:
    """
    items_text_list_list: list = []

    for col_item in table_dataframe.columns.values.tolist()[1:2]:
        df_res: DataFrame = table_dataframe[table_dataframe[col_item].isin([text_too_search])]

        # df_headers: list = list(df_res.columns)[12:]
        items_text_list: list = await get_list_text(df_res, col_item)

        if items_text_list:
            items_text_list_list.append(items_text_list)

    return items_text_list_list


async def processor_search_if_str(table_dataframe: DataFrame, text_too_search: str) -> list:
    """

    :param table_dataframe:
    :param text_too_search:
    :return:
    """
    items_text_list_list: list = []

    for num_col, col_item in enumerate(table_dataframe):
        if num_col <= 0: continue

        mask = table_dataframe[col_item].str.contains(f"{text_too_search}", case=False, regex=True, na=False)

        df_res: DataFrame = table_dataframe.loc[mask]

        # df_headers: list = list(df_res.columns)[1:]
        items_text_list: list = await get_list_text(df_res, col_item)

        if items_text_list:
            items_text_list_list.append(items_text_list)

    return items_text_list_list


async def get_list_text(df_res, col_item) -> list:
    """

    :param df_res:
    :param col_item:
    :return:
    """
    items_text_list = []
    for _, row in df_res.iterrows():
        # file = row.get("file", " - ")
        # item_info: str = f'{file}'
        items_text_list.append(
            {
                col_item: row.get("file", " - ")
            }
        )

    return items_text_list


async def prepare_text(data: list, condition: str) -> list:
    """

    :param condition:
    :param data:
    :return:
    """
    if not isinstance(data, list):
        return []

    dat_list: list = list(chain(*data))
    if not dat_list:
        return []

    dat_list: list = [item for item in dat_list if condition in item.keys()]

    return dat_list
