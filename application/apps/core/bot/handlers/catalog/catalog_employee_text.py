from __future__ import annotations

import asyncio
import os
import traceback
from itertools import chain
from pathlib import Path

import pandas as pd
from pandas import DataFrame

from aiogram import types
from aiogram.dispatcher import FSMContext

from apps.MyBot import MyBot, bot_send_message
from apps.core.bot.filters.custom_filters import filter_is_private
from apps.core.bot.handlers.catalog.catalog_support import DataBaseCatalogEmployee
from apps.core.bot.messages.messages import Messages
from apps.core.bot.messages.messages_test import msg
from apps.core.bot.states.CatalogState import CatalogStateEmployee
from apps.core.database.query_constructor import QueryConstructor
from apps.core.settyngs import get_sett
from config.config import Novolex_DB_path
from loader import logger

list_number = 0


@MyBot.dp.message_handler(filter_is_private, state=CatalogStateEmployee.all_states)
async def catalog_data_all_states_answer(message: types.Message = None, state: FSMContext = None,
                                         user_id: int | str = None, text: str = None):
    """Обработка изменений

    :param text:
    :param user_id:
    :param message:
    :param state:
    :return:
    """
    hse_user_id = message.chat.id if message else user_id
    logger.info(f'{hse_user_id = } {message.text = }')

    await state.finish()

    text_too_search: str = message.text if message else text

    result: bool = await send_data_from_query(hse_user_id, text_too_search=text_too_search)
    return result


async def send_data_from_query(hse_user_id: str | int, text_too_search: str) -> bool:
    """Формирование текста для отправки пользователю

    """
    if not text_too_search:
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены text_too_search')
        return False

    try:
        text_too_search: int = int(text_too_search)

    except ValueError as err:
        logger.info(f'{hse_user_id = } {text_too_search = } {repr(err)}')

    dataframe: DataFrame = await get_dataframe(hse_user_id, column_number=list_number)
    if not await check_dataframe(dataframe, hse_user_id=hse_user_id):
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены dataframe')
        return False

    items_text_list: list = []

    if isinstance(text_too_search, int):
        items_text_list, _ = await processor_search_if_int(
            table_dataframe=dataframe, text_too_search=text_too_search, hse_user_id=hse_user_id
        )

    if isinstance(text_too_search, str):
        items_text_list, _ = await processor_search_if_str(
            table_dataframe=dataframe, text_too_search=text_too_search, hse_user_id=hse_user_id
        )

    if not items_text_list:
        await bot_send_message(chat_id=hse_user_id, text='Данные запроса не найдены text_list')
        return False

    result: bool = await prepare_text(hse_user_id, items_text_list)
    return result


async def processor_search_if_int(table_dataframe: DataFrame, text_too_search: int, hse_user_id: int) -> (list, int):
    """Поиск данных text_too_search как числа (по табельному номеру) в table_dataframe и информирование hse_user_id

    :param hse_user_id:
    :param table_dataframe:
    :param text_too_search:
    :return:
    """
    items_text_list_list: list = []
    personnel_id: int = 0

    for col_item in table_dataframe.columns.values.tolist()[0:1]:
        df_res: DataFrame = table_dataframe.loc[table_dataframe[col_item] == int(text_too_search)]
        if not await check_dataframe(df_res, hse_user_id=hse_user_id):
            await bot_send_message(chat_id=hse_user_id, text='Данные не найдены dataframe')
            return [], personnel_id

        try:
            personnel_id: int = df_res['Табельный номер'].iloc[0]

        except IndexError as err:
            logger.error(f'{await fanc_name()} :: {text_too_search = } :: {repr(err)}')
            await bot_send_message(chat_id=hse_user_id,
                                   text=f'Данные для {text_too_search} не найдены dataframe')
            return [], personnel_id

        items_text_list: list = await get_list_text(df_res, col_item, personnel_id, hse_user_id)

        if items_text_list:
            items_text_list_list.append(items_text_list)

    return items_text_list_list, personnel_id


async def processor_search_if_str(table_dataframe: DataFrame, text_too_search: str, hse_user_id: int | str) -> (
        list, int):
    """Поиск данных text_too_search как текста (или части) по маске в table_dataframe и информирование hse_user_id

    :param hse_user_id:
    :param table_dataframe:
    :param text_too_search:
    :return:
    """
    items_text_list_list: list = []
    personnel_id: int = 0

    for num_col, col_item in enumerate(table_dataframe):
        if num_col == 7: break

        mask = table_dataframe[col_item].str.contains(f"{text_too_search}", case=False, regex=True, na=False)
        df_res: DataFrame = table_dataframe.loc[mask]
        if not await check_dataframe(df_res, hse_user_id=hse_user_id):
            # await bot_send_message(chat_id=hse_user_id, text='Данные не найдены dataframe')
            continue

        try:
            personnel_id: int = df_res['Табельный номер'].iloc[0]

        except IndexError as err:
            logger.error(f'{await fanc_name()} :: {text_too_search = } :: {repr(err)}')
            await bot_send_message(chat_id=hse_user_id,
                                   text=f'Данные для {text_too_search} не найдены dataframe')
            return [], personnel_id

        items_text_list: list = await get_list_text(df_res, col_item, personnel_id, hse_user_id)

        if items_text_list:
            items_text_list_list.append(items_text_list)

    return items_text_list_list, personnel_id


async def prepare_text(user_id: str | int, data: list) -> bool:
    """Подготовка данных data перед отправкой пользователю user_id

    :param user_id:
    :param data:
    :return:
    """
    if not isinstance(data, list):
        return False

    dat_list: list = list(chain(*data))
    if not dat_list:
        return False

    for num, item in enumerate(dat_list, start=1):
        if num == 10:
            await bot_send_message(chat_id=user_id, text='уточните поиск и повторите')
            return True

        str_msg: str = f"{''.join(list(item.keys())[0])} : {''.join(list(item.values())[0])}"
        await bot_send_message(chat_id=user_id, text=f'Найдено в столбце: {str_msg}')

    return True


async def get_list_text(df_res: DataFrame, col_item: str, personnel_id: int | str, hse_user_id: int | str) -> list[
    dict]:
    """Формирование list[dict] с текстом для отправки

    :param df_res:
    :param col_item:
    :param personnel_id:
    :param hse_user_id
    :return:
    """
    items_text_list: list = []

    for _, row in df_res.iterrows():
        item_info: str = ''
        item_info: str = await get_base_info(item_info, row)

        item_info = await get_base_trainings(
            item_info, employee_id=personnel_id, hse_user_id=hse_user_id
        )
        item_info = await get_base_industrial_safety_trainings(
            item_info, employee_id=personnel_id, hse_user_id=hse_user_id
        )

        items_text_list.append(
            {col_item: item_info}
        )

    return items_text_list


async def get_base_info(item_info: str, row) -> str:
    """

    :return:
    """
    department = row.get("Подразделение полностью", " - ")
    job_title = row.get("Должность", " - ")
    employee = row.get("Сотрудник", " - ")
    personnel_number = row.get("Табельный номер", " - ")
    e_mail = row.get("Почта", " - ")
    phone_number = row.get("Тел", " - ")
    supervisor = row.get("Руководитель", " - ")

    item_info: str = f'{item_info} {department}\n\n{job_title} {employee} \n\nтаб.ном {personnel_number}\n' \
                     f'e-mail {e_mail}\nтел {phone_number}\n\nРуководитель\n{supervisor}'
    return item_info


async def get_base_trainings(item_info, employee_id, hse_user_id) -> str:
    """

    :param item_info:
    :param employee_id:
    :param hse_user_id:
    """
    if not employee_id:
        return item_info

    trainings_list: list = await get_information_training(
        employee_id=employee_id, hse_user_id=hse_user_id
    )

    if not trainings_list:
        return item_info

    trainings_list: list = list(list(chain(*trainings_list))[0].values())
    trainings_str: str = '\n'.join(trainings_list)

    return f"{item_info}\n\n{trainings_str}"


async def get_base_industrial_safety_trainings(item_info, employee_id, hse_user_id):
    """

    :param item_info:
    :param employee_id:
    :param hse_user_id:
    :return:
    """
    if not employee_id:
        return item_info

    industrial_safety_training: list = await get_information_industrial_safety_training(
        employee_id=employee_id, hse_user_id=hse_user_id
    )

    if not industrial_safety_training:
        return item_info

    industrial_safety_training: list = list(list(chain(*industrial_safety_training))[0].values())
    trainings_str: str = '\n'.join(industrial_safety_training)

    return f"{item_info}\n\n{trainings_str}"


async def get_information_training(employee_id: int | str = None, hse_user_id: int | str = None) -> list:
    """Получение информации по обучениям

    :param employee_id:
    :param hse_user_id:
    :return:
    """
    if employee_id is None: return []
    if not employee_id: return []

    dataframe: DataFrame = await get_dataframe_with_training(column_number=list_number, hse_user_id=hse_user_id)
    if not await check_dataframe(dataframe, hse_user_id=hse_user_id):
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены dataframe')
        return []

    items_text_list_list: list = []
    for col_item in dataframe.columns.values.tolist()[2:3]:
        df_res: DataFrame = dataframe.loc[dataframe[col_item] == str(employee_id)]
        df_res: DataFrame = df_res[~df_res[col_item].isna()]

        df_headers: list = list(df_res.columns)[6:]
        items_text_list: list = await get_list_text_with_training(df_res, df_headers, col_item)

        if items_text_list:
            items_text_list_list.append(items_text_list)

    return items_text_list_list


async def get_information_industrial_safety_training(
        employee_id: int | str = None, hse_user_id: int | str = None) -> list:
    """Получение информации по обучениям

    :param employee_id:
    :param hse_user_id:
    :return:
    """
    if employee_id is None: return []
    if not employee_id: return []

    dataframe: DataFrame = await get_dataframe_with_industrial_safety_training(
        column_number=list_number, hse_user_id=hse_user_id
    )
    if not await check_dataframe(dataframe, hse_user_id=hse_user_id):
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены dataframe')
        return []

    items_text_list_list: list = []
    for col_item in dataframe.columns.values.tolist()[2:3]:
        df_res: DataFrame = dataframe.loc[dataframe[col_item] == str(employee_id)]
        df_res: DataFrame = df_res[~df_res[col_item].isna()]

        df_headers: list = list(df_res.columns)[6:]
        items_text_list: list = await get_list_text_industrial_safety_training(df_res, df_headers, col_item)

        if not items_text_list:
            continue

        items_text_list_list.append(items_text_list)

    return items_text_list_list


async def get_df_from_database_with_training(hse_user_id) -> DataFrame | None:
    """

    :return:
    """

    if not get_sett(cat='enable_features', param='use_catalog_employee_catalog').get_set():
        msg_text: str = f"{await msg(hse_user_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=hse_user_id, text=msg_text, disable_web_page_preview=True)
        return

    db_table_name: str = 'employee_trainings'
    kwargs: dict = {
        "action": 'SELECT',
        "subject": '*',
    }
    query: str = await QueryConstructor(table_name=db_table_name, **kwargs).prepare_data()

    datas_query: list = await DataBaseCatalogEmployee().get_data_list(query=query)

    if not datas_query:
        return None

    if not isinstance(datas_query, list):
        return None

    clean_headers: list = [
        item[1] for item in await DataBaseCatalogEmployee().get_table_headers(table_name=db_table_name)
    ]
    if not clean_headers:
        return None

    try:
        dataframe: DataFrame = DataFrame(datas_query, columns=clean_headers)

    except Exception as err:
        logger.error(f"create_dataframe {repr(err)}")
        return None

    return dataframe


async def get_df_from_database_with_industrial_safety_training(hse_user_id) -> DataFrame | None:
    """

    :return:
    """

    if not get_sett(cat='enable_features', param='use_catalog_industrial_safety_training').get_set():
        msg_text: str = f"{await msg(hse_user_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=hse_user_id, text=msg_text, disable_web_page_preview=True)
        return

    db_table_name: str = 'employee_industrial_safety_trainings'
    kwargs: dict = {
        "action": 'SELECT',
        "subject": '*',
    }
    query: str = await QueryConstructor(table_name=db_table_name, **kwargs).prepare_data()

    datas_query: list = await DataBaseCatalogEmployee().get_data_list(query=query)

    if not datas_query:
        return None

    if not isinstance(datas_query, list):
        return None

    clean_headers: list = [item[1] for item in
                           await DataBaseCatalogEmployee().get_table_headers(table_name=db_table_name)]
    if not clean_headers:
        return None

    try:
        dataframe: DataFrame = DataFrame(datas_query, columns=clean_headers)

    except Exception as err:
        logger.error(f"create_dataframe {repr(err)}")
        return None

    return dataframe


async def get_df_from_xlsx_with_training(hse_user_id, column_number=0) -> DataFrame | None:
    """

    :param hse_user_id:
    :param column_number:
    :return:
    """
    file_list: list = await get_file_xlsx_with_training()
    if not file_list:
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены file_list')
        return None

    datadict: dict = pd.read_excel(file_list[-1], sheet_name=None)
    if not datadict:
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены datadict')
        return None

    dataframe: DataFrame = datadict[list(datadict.keys())[column_number]]
    return dataframe


async def get_df_from_xlsx_with_industrial_safety_training(hse_user_id, column_number=0) -> DataFrame | None:
    """

    :param hse_user_id:
    :param column_number:
    :return:
    """
    file_list: list = await get_file_xlsx_with_industrial_safety_training()
    if not file_list:
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены file_list')
        return None

    datadict: dict = pd.read_excel(file_list[-1], sheet_name=None)
    if not datadict:
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены datadict')
        return None

    dataframe: DataFrame = datadict[list(datadict.keys())[column_number]]
    return dataframe


async def get_list_text_with_training(df_res, df_headers, col_item) -> list:
    """

    :param df_res:
    :param df_headers:
    :param col_item:
    :return:
    """
    items_text_list = []

    for _, row in df_res.iterrows():

        headers_list_str: list = []
        # if admin:
        for header in df_headers:
            i_char = row.get(header) if not isinstance(row.get(header), float) else None
            if i_char:
                headers_list_str.append(f"{header}: {row.get(header, '')}")

        headers_str: str = ' \n'.join(item for item in headers_list_str if item)

        item_info: str = 'Обучения и аттестации:'
        if headers_str:
            item_info = f'{item_info}\n\n{headers_str}'

        items_text_list.append(
            {col_item: item_info}
        )
    return items_text_list


async def get_list_text_industrial_safety_training(df_res, df_headers, col_item) -> list:
    """

    :param df_res:
    :param df_headers:
    :param col_item:
    :return:
    """
    items_text_list = []

    for _, row in df_res.iterrows():

        headers_list_str: list = []
        # if admin:
        for header in df_headers:
            i_char = row.get(header) if not isinstance(row.get(header), float) else None
            if not pd.isnull(i_char) and i_char is not None:
                headers_list_str.append(f"{header}: {row.get(header, '')}")

        headers_str: str = ' \n'.join(item for item in headers_list_str if item)

        item_info: str = 'Аттестации по промышленной безопасности:'
        if headers_str:
            item_info = f'{item_info}\n\n{headers_str}'

        items_text_list.append(
            {col_item: item_info}
        )
    return items_text_list


async def get_dataframe(hse_user_id: str | int, column_number: int = None) -> DataFrame | None:
    """

    :return:
    """
    dataframe: DataFrame = await get_df_from_database(hse_user_id)
    if await check_dataframe(dataframe, hse_user_id=hse_user_id):
        return dataframe

    dataframe: DataFrame = await get_df_from_excel(hse_user_id, column_number)
    if await check_dataframe(dataframe, hse_user_id=hse_user_id):
        return dataframe

    # dataframe: DataFrame = await get_dataframe_from_local_files(hse_user_id, column_number)
    # if await check_dataframe(dataframe, hse_user_id=hse_user_id):
    #     return dataframe

    return None


async def get_dataframe_with_training(column_number, hse_user_id) -> DataFrame | None:
    """

    :param column_number:
    :param hse_user_id:
    :return:
    """
    dataframe: DataFrame = await get_df_from_database_with_training(hse_user_id)
    if await check_dataframe(dataframe, hse_user_id=hse_user_id):
        return dataframe

    dataframe: DataFrame = await get_df_from_xlsx_with_training(hse_user_id, column_number)
    if await check_dataframe(dataframe, hse_user_id=hse_user_id):
        return dataframe

    # dataframe: DataFrame = await get_dataframe_from_local_files(hse_user_id, column_number)
    # if await check_dataframe(dataframe, hse_user_id=hse_user_id):
    #     return dataframe

    return None


async def get_dataframe_with_industrial_safety_training(column_number, hse_user_id) -> DataFrame | None:
    """

    :param column_number:
    :param hse_user_id:
    :return:
    """
    dataframe: DataFrame = await get_df_from_database_with_industrial_safety_training(hse_user_id)
    if await check_dataframe(dataframe, hse_user_id=hse_user_id):
        return dataframe

    dataframe: DataFrame = await get_df_from_xlsx_with_industrial_safety_training(hse_user_id, column_number)
    if await check_dataframe(dataframe, hse_user_id=hse_user_id):
        return dataframe

    # dataframe: DataFrame = await get_dataframe_from_local_files(hse_user_id, column_number)
    # if await check_dataframe(dataframe, hse_user_id=hse_user_id):
    #     return dataframe

    return None


async def get_df_from_database(hse_user_id: str | int) -> DataFrame | None:
    """

    :param hse_user_id:
    :return:
    """

    if not get_sett(cat='enable_features', param='use_catalog_employee_catalog').get_set():
        msg_text: str = f"{await msg(hse_user_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=hse_user_id, text=msg_text, disable_web_page_preview=True)
        return

    db_table_name: str = 'employee_user'
    kwargs: dict = {
        "action": 'SELECT',
        "subject": '*',
    }
    query: str = await QueryConstructor(table_name=db_table_name, **kwargs).prepare_data()

    datas_query: list = await DataBaseCatalogEmployee().get_data_list(query=query)
    if not datas_query:
        return None

    if not isinstance(datas_query, list):
        return None

    clean_headers: list = [
        item[1] for item in await DataBaseCatalogEmployee().get_table_headers(table_name=db_table_name)
    ]
    if not clean_headers:
        return None

    try:
        dataframe: DataFrame = DataFrame(datas_query, columns=clean_headers)

    except Exception as err:
        logger.error(f"create_dataframe {repr(err)}")
        return None

    return dataframe


async def get_df_from_excel(hse_user_id: str | int, column_number: int = None) -> DataFrame | None:
    """

    :param hse_user_id:
    :param column_number:
    :return:
    """

    file_list: list = await get_file_xlsx_with_constractor()
    if not file_list:
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены file_list')
        return None

    datadict: dict = pd.read_excel(file_list[-1], sheet_name=None)
    if not datadict:
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены datadict')
        return None

    dataframe: DataFrame = datadict[list(datadict.keys())[column_number]]
    return dataframe


async def get_file_xlsx_with_constractor(*, xls_name: str = None, xls_path: str = None,
                                         extension: str = '.xlsx') -> list:
    """Получение файлов со штатным расписанием в текущей директории

    """
    xls_path: str = xls_path if xls_path else str(Path(Novolex_DB_path))
    xls_name: str = xls_name if xls_name else str('constractor')

    file_list: list = await get_file_xlsx(xls_name, xls_path, extension=extension)
    return file_list


async def get_file_xlsx_with_training(*, xls_name: str = None, xls_path: str = None,
                                      extension: str = '.xlsx') -> list:
    """Получение файлов со штатным расписанием в директории

    """
    xls_path: str = xls_path if xls_path else str(Path(Novolex_DB_path, 'TRAININGS'))
    xls_name: str = xls_name if xls_name else str('реестр')

    file_list: list = await get_file_xlsx(xls_name, xls_path, extension=extension)
    return file_list


async def get_file_xlsx_with_industrial_safety_training(*, xls_name: str = None, xls_path: str = None,
                                                        extension: str = '.xlsx') -> list:
    """Получение файлов со штатным расписанием в директории

    """
    xls_path: str = xls_path if xls_path else str(Path(Novolex_DB_path, 'TRAININGS'))
    xls_name: str = xls_name if xls_name else str('Реестр аттестации по ПБ')

    file_list: list = await get_file_xlsx(xls_name, xls_path, extension=extension)
    return file_list


async def get_file_xlsx(xls_name: str = None, xls_path: str = None, extension: str = '.xlsx') -> list:
    """Получение файлов имя которых содержи xls_name с расширением extension из директории xls_path
    """
    file_list: list = []

    if not xls_name:
        logger.error(f'path {xls_name} is not exists!')
        return []

    if not xls_path:
        logger.error(f'path {xls_path} is not exists!')
        return []

    if not await catalog_async_check_path(xls_path):
        logger.error(f'path {xls_path} is not exists!')
        return []

    for root, _, files in os.walk(xls_path):
        for filename in files:

            if not filename: continue
            if '~' in filename: continue
            if filename.endswith('.py'): continue
            if filename.endswith('.jpg'): continue
            if filename.endswith('.tmp'): continue
            if filename.endswith('.db'): continue

            if extension in filename and xls_name in filename:
                file_list.append(await catalog_get_file_path(root, filename))
    return file_list


async def catalog_get_file_path(*args) -> str:
    """

    :param args:
    :return:
    """
    return str(Path(*args))


async def check_dataframe(dataframe: DataFrame, hse_user_id: str | int) -> bool:
    """Проверка dataframe на наличие данных

    :param dataframe:
    :param hse_user_id: id пользователя
    :return:
    """
    if dataframe is None:
        text_violations: str = 'не удалось получить данные!'
        logger.error(f'{hse_user_id = } {text_violations}')
        return False

    if dataframe.empty:
        logger.error(f'{hse_user_id = } {Messages.Error.dataframe_is_empty}')
        return False

    return True


async def catalog_async_check_path(file_path: str | Path) -> bool:
    """

    :param file_path:: str | Path - path to file
    :return: bool True if exists else - False
    """
    if Path(file_path).exists():
        return True
    return False


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])


async def test():
    message: types.Message = None
    state: FSMContext = {}
    user_id: int | str = 373084462
    text: str = '3526'

    await catalog_data_all_states_answer(message, state, user_id, text)


if __name__ == '__main__':
    asyncio.run(test())
