from __future__ import annotations

import math
import os
import sqlite3
from datetime import datetime

import pandas as pd
from aiogram import types
from pandas import DataFrame

from apps.MyBot import bot_send_message
from apps.core.bot.handlers.catalog.catalog_support_paths import catalog_check_path, catalog_get_file_path, \
    catalog_async_check_path
from apps.core.bot.handlers.catalog.catalog_func_handler import catalog_spot_data
from apps.core.bot.messages.messages import Messages
from apps.core.bot.messages.messages_test import msg
from apps.core.database.query_constructor import QueryConstructor
from apps.core.settyngs import get_sett
from config.config import Novolex_Catalog_DB, Novolex_Catalog_Employee_DB, Novolex_LNA_path
from loader import logger

list_number = 0
level_1_column = 3
level_2_column = 4
level_3_column = 5
level_4_column = 6


class DataBaseCatalogEmployee:

    def __init__(self):

        if not catalog_check_path(Novolex_Catalog_Employee_DB):
            logger.error(f'path {Novolex_Catalog_Employee_DB} is not exists!')

        self.db_file = Novolex_Catalog_Employee_DB
        self.connection = sqlite3.connect(self.db_file)
        self.cursor = self.connection.cursor()

        self.name: str = self.db_file.stem

    async def create_backup(self) -> str | None:
        """

        :return:
        """
        backup_file_path: str = f"C:\\backup\\{datetime.now().strftime('%d.%m.%Y')}\\"
        if not os.path.isdir(backup_file_path):
            os.makedirs(backup_file_path)

        query: str = f"vacuum into '{backup_file_path}backup_{datetime.now().strftime('%d.%m.%Y, %H.%M.%S')}_{self.name}.db'"

        try:
            with self.connection:
                result = self.cursor.execute(query)
                return self.name

        except (ValueError, sqlite3.OperationalError) as err:
            logger.error(f'Invalid query. {repr(err)}')
            return None

        finally:
            self.cursor.close()

    async def get_table_headers(self, table_name: str = None) -> list[str]:
        """Получение всех заголовков таблицы core_violations

        :return: list[ ... ]
        """
        if not table_name:
            return []
        try:

            with self.connection:
                result: list = self.cursor.execute(f"PRAGMA table_info('{table_name}')").fetchall()
                clean_headers: list = [item[1] for item in result]
                return clean_headers

        except (ValueError, sqlite3.OperationalError) as err:
            logger.error(f'{repr(err)}')
            logger.error(f"Invalid query. {type(err).__name__} {err}")
            return []

        finally:
            self.cursor.close()

    async def get_all_tables_names(self) -> list:
        """Получение всех имен таблиц в БД

        :return:
        """
        try:
            with self.connection:
                result: list = self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
                return result

        except (ValueError, sqlite3.OperationalError) as err:
            logger.error(f'{repr(err)}')
            logger.error(f"Invalid query. {type(err).__name__} {err}")
            return []

        finally:
            self.cursor.close()

    async def get_data_list(self, query: str = None) -> list:
        """Получение данных из таблицы по запросу 'query'"""
        if not query:
            return []
        try:
            with self.connection:
                return self.cursor.execute(query).fetchall()
        except (ValueError, sqlite3.OperationalError) as err:
            logger.error(f'{repr(err)}')
            logger.error(f"Invalid query. {type(err).__name__} {err}")
            return []

        finally:
            self.cursor.close()

    async def get_data_list_without_query(self, table_name: str = None) -> list:
        """Получение данных из таблицы table_name"""
        try:
            with self.connection:
                query_kwargs: dict = {
                    "action": 'SELECT',
                    "subject": '*',
                }
                query: str = await QueryConstructor(None, table_name, **query_kwargs).prepare_data()
                result: list = self.cursor.execute(query).fetchall()
                if not result:
                    logger.error(f"no matches found {table_name} in DB "
                                 f"because .cursor.execute is none `table_name`: {table_name}")
                    return []
            return result

        except (ValueError, sqlite3.OperationalError) as err:
            logger.error(f'{repr(err)}')
            logger.error(f"Invalid query. {type(err).__name__} {err}")
            return []

        finally:
            self.cursor.close()

    async def update_column_value(self, query: str):
        """Обновление записи id в database

        :param query: str
        :return: result
        """
        try:
            with self.connection:
                result = self.cursor.execute(query)
            self.connection.commit()
            return result

        except (ValueError, sqlite3.OperationalError) as err:
            logger.error(f'{repr(err)}')
            logger.error(f"Invalid query. {type(err).__name__} {err}")
            return []

        finally:
            self.cursor.close()


async def notify_user_for_choice(call_msg: types.CallbackQuery | types.Message, user_id: int | str = None,
                                 data_answer: str = None) -> bool:
    """Уведомление пользователя о выборе + логирование

    :param data_answer:
    :param user_id: int | str id пользователя
    :param call_msg:
    :return None :
    """

    if isinstance(call_msg, types.CallbackQuery):

        for i in ('previous_paragraph', 'move_up', 'move_down'):
            if i in call_msg.data: return True

        mesg_text: str = f"Выбрано: {data_answer}"
        if call_msg.data in call_msg.message.text:
            mesg_list: list = [item for item in call_msg.message.text.split('\n\n') if call_msg.data in item]
            mesg_text = f"Выбрано: {mesg_list[0]}"

        try:
            hse_user_id = call_msg.message.chat.id if call_msg else user_id
            logger.debug(f"{hse_user_id = } Выбрано: {data_answer} {call_msg.data}")
            await call_msg.message.edit_text(text=mesg_text, reply_markup=None)
            return True

        except Exception as err:
            logger.debug(f"{call_msg.message.chat.id = } {repr(err)}")

    if isinstance(call_msg, types.Message):

        for i in ('previous_paragraph', 'move_up', 'move_down'):
            if i in call_msg.text: return True

        mesg_text: str = f"Выбрано: {data_answer}"
        if call_msg.text in call_msg.text:
            mesg_list: list = [item for item in call_msg.text.split('\n\n') if call_msg.text in item]
            mesg_text = f"Выбрано: {mesg_list[0] if mesg_list else ''}"

        try:
            hse_user_id = call_msg.chat.id if call_msg else user_id
            logger.debug(f"{hse_user_id = } Выбрано: {data_answer} {call_msg.text}")
            await call_msg.edit_text(text=mesg_text, reply_markup=None)
            return True

        except Exception as err:
            logger.debug(f"{call_msg.chat.id = } {repr(err)}")


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


async def get_dataframe_from_local_files(hse_user_id: str | int, column_number: int = None) -> DataFrame | None:
    """

    :return:
    """

    file_list: list = await get_lna_files(lna_path=str(Novolex_LNA_path))
    if not file_list:
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены file_list')
        return None

    parts_with_number: list = []
    list_dict: list = []
    for num, file_path in enumerate(file_list):
        if not os.path.isfile(file_path):
            continue

        file_name: str = file_path.split(os.sep)[-1]
        list_parts: list = file_name.split('_')

        part_with_number: list = [item for item in list_parts if item.isnumeric()]
        parts_with_number = parts_with_number + part_with_number

        list_parts: list = file_name.split(' ')
        part_with_number: list = [item for item in list_parts if item.isnumeric()]
        parts_with_number = parts_with_number + part_with_number

        list_parts: list = file_name.split('.')
        part_with_number: list = [item for item in list_parts if item.isnumeric()]
        parts_with_number = parts_with_number + part_with_number

        parts_with_number: list = list(set(parts_with_number))

        list_dict.append(
            {
                "num": num,
                "num_parts": ', '.join(parts_with_number),
                # "num_parts": parts_with_number,
                "file_path": file_path,
                "file": file_name,
            }
        )
        parts_with_number = []

    if not list_dict:
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены file_list')
        return None

    dataframe: DataFrame = pd.DataFrame(list_dict)
    return dataframe


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


async def get_df_from_excel(hse_user_id: str | int, column_number: int = None) -> DataFrame | None:
    """

    :param hse_user_id:
    :param column_number:
    :return:
    """
    file_list: list = await get_file_xlsx()
    if not file_list:
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены file_list')
        return None

    datadict: dict = pd.read_excel(file_list[-1], sheet_name=None)
    if not datadict:
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены datadict')
        return None

    dataframe: DataFrame = datadict[list(datadict.keys())[column_number]]
    return dataframe


async def get_level_1_list_dict(hse_user_id, dataframe: DataFrame = None):
    """

    :param dataframe:
    :param hse_user_id:
    :return:
    """
    if not await check_dataframe(dataframe, hse_user_id=hse_user_id):
        dataframe = await get_dataframe(hse_user_id, column_number=list_number)
        if not await check_dataframe(dataframe, hse_user_id=hse_user_id):
            await bot_send_message(chat_id=hse_user_id, text='Данные не найдены dataframe')
            return

    level_1: list = dataframe[dataframe.columns[level_1_column]].unique().tolist()
    if not level_1:
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены level_1')
        return

    d_list: list = [{f"level_1__{num}": item} for num, item in enumerate(level_1, start=1) if item is not None]
    return d_list


async def get_level_2_list_dict(hse_user_id, dataframe: DataFrame = None):
    """

    :param dataframe:
    :param hse_user_id:
    :return:
    """
    if not await check_dataframe(dataframe, hse_user_id=hse_user_id):
        dataframe = await get_dataframe(hse_user_id, column_number=list_number)
        if not await check_dataframe(dataframe, hse_user_id=hse_user_id):
            await bot_send_message(chat_id=hse_user_id, text='Данные не найдены dataframe')
            return

    df_level_2: DataFrame = dataframe.loc[
        dataframe[dataframe.columns[level_1_column]] == catalog_spot_data['level_1_name']]

    level_2: list = df_level_2[df_level_2.columns[level_2_column]].unique().tolist()
    if not level_2:
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены level_2')
        return []

    d_list: list = [{f"level_2__{num}": item} for num, item in enumerate(level_2, start=1) if item is not None]
    return d_list


async def text_processor_level(table_dataframe: DataFrame, nan_value: str = None, level: int = 0,
                               level_name: str = None) -> str:
    """Формирование текста для отправки пользователю

    """
    unique_items_titles: list = table_dataframe[table_dataframe.columns[level]].unique().tolist()

    items_text_list: list = []
    for i, (item_title) in enumerate(unique_items_titles, 1):
        item_info: str = f'level_{level + 1}__{i} : {item_title}'
        items_text_list.append(item_info)

    items_text: str = '\n'.join(items_text_list)

    header_text: str = Messages.Choose.choose_value
    footer_text: str = 'Нажмите на кнопку с номером выбранного значения'

    fin_list: list = [header_text, level_name, nan_value, items_text, footer_text]
    final_text = '\n\n'.join([item for item in fin_list if item])
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


async def get_file_xlsx() -> list:
    """Получение файлов со штатным расписанием в текущей директории

    """
    file_list: list = []

    if not await catalog_async_check_path(Novolex_Catalog_DB):
        logger.error(f'path {Novolex_Catalog_DB} is not exists!')
        return []

    for root, _, files in os.walk(Novolex_Catalog_DB):
        for filename in files:

            if not filename: continue
            if '~' in filename: continue
            if filename.endswith('.py'): continue
            if filename.endswith('.jpg'): continue
            if filename.endswith('.tmp'): continue
            if filename.endswith('.db'): continue

            if '.xlsx' in filename and 'constractor' in filename:
                file_list.append(await catalog_get_file_path(root, filename))
    return file_list


async def get_lna_files(lna_path: str) -> list:
    """Получение файлов со штатным расписанием в текущей директории

    """
    file_list: list = []

    if not await catalog_async_check_path(lna_path):
        logger.error(f'path {lna_path} is not exists!')
        return []

    for root, _, files in os.walk(lna_path):
        for filename in files:

            if not filename: continue
            if '~' in filename: continue
            if filename.endswith('.py'): continue
            if filename.endswith('.jpg'): continue
            if filename.endswith('.tmp'): continue
            if filename.endswith('.db'): continue

            # if '.pdf' in filename:
            file_list.append(await catalog_get_file_path(root, filename))

    return file_list


async def get_nan_value_text(hse_user_id, dataframe: DataFrame, column_nom: int = 0, level: int = 1) -> str:
    """

    :return:
    """

    nan_value_df: DataFrame = dataframe.loc[dataframe[dataframe.columns[column_nom]].isna()]
    if not await check_dataframe(nan_value_df, hse_user_id=hse_user_id):
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены dataframe')
        return ''

    items_text_list: list = []
    for index, row in nan_value_df.iterrows():
        department = row.get("Подразделение полностью", " - ")
        job_title = row.get("Должность")
        employee = row.get("Сотрудник")
        personnel_number = row.get("Табельный номер")
        e_mail = row.get("Почта")
        phone_number = row.get("Тел")

        item_info: str = f'{department}\n{job_title} {employee} \nтаб.ном {personnel_number}\ne-mail {e_mail}\nтел {phone_number}'
        await bot_send_message(chat_id=hse_user_id, text=item_info)

        items_text_list.append(item_info)

    items_text: str = '\n\n'.join([item for item in items_text_list if item is not None])

    return items_text


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


async def notify_user_for_choice(call_msg: types.CallbackQuery | types.Message, user_id: int | str = None,
                                 data_answer: str = None) -> bool:
    """Уведомление пользователя о выборе + логирование

    :param data_answer:
    :param user_id: int | str id пользователя
    :param call_msg:
    :return None :
    """

    if isinstance(call_msg, types.CallbackQuery):

        for i in ('previous_paragraph', 'move_up', 'move_down'):
            if i in call_msg.data: return True

        mesg_text: str = f"Выбрано: {data_answer}"
        if call_msg.data in call_msg.message.text:
            mesg_list: list = [item for item in call_msg.message.text.split('\n\n') if call_msg.data in item]
            mesg_text = f"Выбрано: {mesg_list[0]}"

        try:
            hse_user_id = call_msg.message.chat.id if call_msg else user_id
            logger.debug(f"{hse_user_id = } Выбрано: {data_answer} {call_msg.data}")
            await call_msg.message.edit_text(text=mesg_text, reply_markup=None)
            return True

        except Exception as err:
            logger.debug(f"{call_msg.message.chat.id = } {repr(err)}")

    if isinstance(call_msg, types.Message):

        for i in ('previous_paragraph', 'move_up', 'move_down'):
            if i in call_msg.text: return True

        mesg_text: str = f"Выбрано: {data_answer}"
        if call_msg.text in call_msg.text:
            mesg_list: list = [item for item in call_msg.text.split('\n\n') if call_msg.text in item]
            mesg_text = f"Выбрано: {mesg_list[0] if mesg_list else ''}"

        try:
            hse_user_id = call_msg.chat.id if call_msg else user_id
            logger.debug(f"{hse_user_id = } Выбрано: {data_answer} {call_msg.text}")
            await call_msg.edit_text(text=mesg_text, reply_markup=None)
            return True

        except Exception as err:
            logger.debug(f"{call_msg.chat.id = } {repr(err)}")
