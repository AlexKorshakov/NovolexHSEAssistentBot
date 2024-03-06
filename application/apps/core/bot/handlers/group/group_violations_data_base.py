from __future__ import annotations

import os
import io
import json
import sqlite3
import asyncio
import traceback
from pathlib import Path
from pprint import pprint

from pandas import DataFrame
import datetime

from loader import logger
from apps.core.database.query_constructor import QueryConstructor
from config.config import Novolex_Group_Violations_DB


class GroupDataBase:

    def __init__(self):
        self.db_file = Novolex_Group_Violations_DB
        self.connection = sqlite3.connect(self.db_file)
        self.cursor = self.connection.cursor()
        self.name: str = self.db_file.stem

    async def create_backup(self) -> str | None:
        """Создание бэкапа"""
        backup_file_path: str = str(Path('C:', 'backup', datetime.datetime.now().strftime('%d.%m.%Y')))
        if not os.path.isdir(backup_file_path):
            os.makedirs(backup_file_path)

        query: str = f"vacuum into '{backup_file_path}{os.sep}backup_{datetime.datetime.now().strftime('%d.%m.%Y, %H.%M.%S')}_{self.name}.db'"

        try:
            with self.connection:
                result = self.cursor.execute(query)
                logger.debug(result)
                return self.name

        except (ValueError, sqlite3.OperationalError) as err:
            logger.error(f'Invalid query. {repr(err)}')
            return None

        finally:
            self.cursor.close()

    async def add_data(self, table_name: str, data_dict: dict) -> bool:
        """Добавление данных в БД
        """
        param_list: list = [table_name, data_dict]
        for param in param_list:
            if not param:
                logger.error(f'{__file__} {await fanc_name()} Invalid param. {param = }')
                return False

        if not isinstance(data_dict, dict): return False

        dict_keys = ', '.join(list(data_dict.keys()))
        qs = ', '.join(['?'] * len(data_dict))

        # TODO заменить на вызов конструктора QueryConstructor
        sqlite_insert_with_param: str = "INSERT INTO `" + table_name + "` (" + dict_keys + ") VALUES (" + qs + ");"
        data_tuple: tuple = tuple(data_dict.values())

        try:
            with self.connection:
                result = self.cursor.execute(sqlite_insert_with_param, data_tuple)
                if result:
                    return True

                return False

        except (ValueError, TypeError, sqlite3.IntegrityError, sqlite3.OperationalError) as err:
            logger.error(f'{__file__} {await fanc_name()} Invalid query. {repr(err)}')
            return False

        finally:
            self.cursor.close()

    async def get_id(self, table_name: str, entry, file_id: str = None, calling_function_name: str = None) -> int:
        """Получение id записи по значению title из соответствующий таблицы table

        """
        param_list: list = [table_name, entry]
        for param in param_list:
            if param is None:
                logger.error(f'{__file__} {await fanc_name()} Invalid param. {param = } {calling_function_name =}')
                return 0

        try:
            query_kwargs: dict = {
                "action": 'SELECT', "subject": 'id',
                "conditions": {
                    "title": entry,
                },
            }
            query: str = await QueryConstructor(None, table_name, **query_kwargs).prepare_data()

            with self.connection:
                result = self.cursor.execute(query).fetchall()

            if not result:
                query_kwargs: dict = {
                    "action": 'SELECT', "subject": 'id',
                    "conditions": {
                        "short_title": entry,
                    },
                }
                query: str = await QueryConstructor(None, table_name, **query_kwargs).prepare_data()

                with self.connection:
                    result = self.cursor.execute(query).fetchall()

        except (ValueError, sqlite3.IntegrityError, sqlite3.OperationalError) as err:
            logger.error(f'{__file__} {await fanc_name()} Invalid query. {repr(err)}')
            return 0

        finally:
            self.cursor.close()

        if not result:
            logger.error(
                    f"no matches found {entry = } in {table_name} in title because .cursor.execute is none file_id: {file_id}")
            return 0

        entry_id: int = 0

        if isinstance(result, list) and len(result) >= 2:
            logger.warning(f"Warning!! {await fanc_name()} too many returned values for {file_id = }. get last value!")

        if isinstance(result, list) and len(result) > 0 and len(result[0]) > 0:
            entry_id = int(result[-1][0])

        if entry_id == 0:
            logger.info(f"no matches found {entry = } in {table_name} because entry_id file_id: {file_id}")
            return 0

        return entry_id

    async def get_dict_data_from_table_from_id(self, table_name: str, data_id: int, query: str = None) -> dict:
        """Получение данных из таблицы table_name по id

        :param table_name: str - имя таблицы в БД
        :param data_id: int  id записи
        :param query: str запрос при наличии
        """
        check_result: bool = await self.get_check_param(__file__, await fanc_name(), table_name=table_name, data_id=data_id)
        if not check_result: return {}

        if not query:
            query_kwargs: dict = {
                "action": 'SELECT', "subject": '*',
                "conditions": {
                    "id": data_id,
                },
            }
            query: str = await QueryConstructor(None, table_name, **query_kwargs).prepare_data()

        values: list = await self.get_data_list(query=query)
        headers: list = [item[1] for item in await self.get_table_headers(table_name=table_name)]
        clean_values: list = values[0] if values else []

        return dict((header, item_value) for header, item_value in zip(headers, clean_values))

    async def get_check_param(self, local_file: str, calling_function: str, **kvargs) -> bool:
        """Проверка параметров """
        calling_file: str = f'{os.sep}'.join(local_file.split(os.sep)[-2:])

        result_list: list = []
        print_dict: dict = {}

        for param_num, param in enumerate(kvargs, start=1):

            if kvargs[param] is None:
                logger.error(f'{calling_file} {calling_function} Invalid param. #{param_num} {param = } {kvargs[param]}')

            result_list.append(kvargs[param])
            print_dict[param] = kvargs[param]

        return all(result_list)

    # async def get_id_violation(self, file_id: str = None) -> int:
    #     """Получение id записи по значению file_id из таблицы core_violations"""
    #     param_list: list = [file_id]
    #     for param in param_list:
    #         if not param:
    #             logger.error(f'{__file__} {await fanc_name()} Invalid param. {param = }')
    #             return 0
    #
    #     table_name: str = 'core_violations'
    #     query_kwargs: dict = {
    #         "action": 'SELECT', "subject": 'id',
    #         "conditions": {
    #             "file_id": str(file_id),
    #         },
    #     }
    #     query: str = await QueryConstructor(None, table_name, **query_kwargs).prepare_data()
    #
    #     try:
    #         with self.connection:
    #             result = self.cursor.execute(query).fetchall()
    #
    #     except (ValueError, sqlite3.IntegrityError, sqlite3.OperationalError) as err:
    #         logger.error(f'{__file__} {await fanc_name()} Invalid query. {repr(err)}')
    #         return 0
    #
    #     finally:
    #         self.cursor.close()
    #
    #     if not result:
    #         logger.error(f"no matches found {file_id} in core_violations because "
    #                      f".cursor.execute is none")
    #         return 0
    #
    #     entry_id: int = 0
    #
    #     if isinstance(result, list) and len(result) >= 2:
    #         logger.warning(f"Warning!! {await fanc_name()}  too many returned values for {file_id = }. get last value!")
    #
    #     if isinstance(result, list) and len(result) > 0 and len(result[0]) > 0:
    #         entry_id = int(result[-1][0])
    #
    #     if entry_id == 0:
    #         logger.info(f"no matches found {file_id = } in {table_name} because entry_id file_id: {file_id}")
    #         return 0
    #
    #     return entry_id

    async def get_table_headers(self, table_name: str = None) -> list[str]:
        """Получение всех заголовков таблицы core_violations

        :return: list[ ... ]
        """
        query: str = f"PRAGMA table_info('{table_name}')"

        try:
            with self.connection:
                result: list = self.cursor.execute(query).fetchall()
                return result

        except (ValueError, sqlite3.IntegrityError, sqlite3.OperationalError) as err:
            logger.error(f'{__file__} {await fanc_name()} Invalid query. {repr(err)}')
            return []

        finally:
            self.cursor.close()

    async def get_single_violation(self, file_id: str) -> list:
        """Получение записи по id

        :param file_id: file_id из таблицы core_violations
        :return: list[ ... ] or []
        """
        param_list: list = [file_id]
        for param in param_list:
            if not param:
                logger.error(f'{__file__} {await fanc_name()} Invalid param. {param = }')
                return []

        table_name: str = 'core_violations'
        query_kwargs: dict = {
            "action": 'SELECT', "subject": 'id',
            "conditions": {
                "file_id": file_id,
            },
        }
        query: str = await QueryConstructor(None, table_name, **query_kwargs).prepare_data()

        try:
            with self.connection:
                result: list = self.cursor.execute(query).fetchall()

        except sqlite3.OperationalError as err:
            logger.error(f"sqlite3.OperationalError {err = } {query = }")
            return []

        finally:
            self.cursor.close()

        if isinstance(result, list) and len(result) >= 2:
            logger.warning(f"Warning!! {await fanc_name()}  too many returned values for {file_id = }. get last value!")
            return list(result[-1])

        return result

    async def violation_exists(self, file_id: str, table_name: str) -> bool:
        """Проверка наличия violation_id в базе"""
        param_list: list = [file_id]
        for param in param_list:
            if not param:
                logger.error(f'{__file__} {await fanc_name()} Invalid param. {param = }')
                return False

        table_name: str = table_name if table_name else 'core_violations'
        query_kwargs: dict = {
            "action": 'SELECT', "subject": '*',
            "conditions": {
                "file_id": file_id,
            },
        }
        query: str = await QueryConstructor(None, table_name, **query_kwargs).prepare_data()
        try:
            with self.connection:
                result = self.cursor.execute(query).fetchall()

        except sqlite3.OperationalError as err:
            logger.error(f"sqlite3.OperationalError {err = } {query = }")
            return False

        finally:
            self.cursor.close()

        if isinstance(result, list) and len(result) >= 2:
            logger.warning(f"Warning!! {await fanc_name()}  too many returned values for {file_id = }. get last value!")
            return bool(len(result[-1]))

        return bool(len(result))

    # async def user_exists(self, user_telegram_id: int) -> bool:
    #     """Проверка наличия user_telegram_id в базе"""
    #     param_list: list = [user_telegram_id]
    #     for param in param_list:
    #         if not param:
    #             logger.error(f'{__file__} {await fanc_name()} Invalid param. {param = }')
    #             return False
    #
    #     table_name: str = "core_hseuser"
    #     query_kwargs: dict = {
    #         "action": 'SELECT', "subject": '*',
    #         "conditions": {
    #             "hse_telegram_id": user_telegram_id,
    #         },
    #     }
    #     query: str = await QueryConstructor(None, table_name, **query_kwargs).prepare_data()
    #     try:
    #         with self.connection:
    #             result = self.cursor.execute(query).fetchall()
    #
    #     except sqlite3.OperationalError as err:
    #         logger.error(f"sqlite3.OperationalError {err = } {query = }")
    #         return False
    #
    #     finally:
    #         self.cursor.close()
    #
    #     if isinstance(result, list) and len(result) >= 2:
    #         logger.warning(
    #             f"Warning!! {await fanc_name()}  too many returned values for {user_telegram_id = }. get last value!")
    #         return bool(len(result[-1]))
    #
    #     return bool(len(result))
    #
    # async def delete_single_violation(self, file_id: str) -> bool:
    #     """Удаление записи"""
    #     param_list: list = [file_id]
    #     for param in param_list:
    #         if not param:
    #             logger.error(f'{__file__} {await fanc_name()} Invalid param. {param = }')
    #             return False
    #
    #     # TODO заменить на вызов конструктора QueryConstructor
    #     query: str = "DELETE FROM `core_violations` WHERE `file_id` = ?"
    #     try:
    #         with self.connection:
    #             result = self.cursor.execute(query, (file_id,))
    #             return bool(result)
    #
    #     except sqlite3.OperationalError as err:
    #         logger.error(f"sqlite3.OperationalError {err = } {query = }")
    #         return False
    #
    #     finally:
    #         self.cursor.close()
    #
    # async def delete_item_from_table(self, *, table_name: str, column_name: str, file_id: int) -> bool:
    #     """Удаление записи"""
    #     param_list: list = [table_name, column_name, file_id]
    #     for param in param_list:
    #         if not param:
    #             logger.error(f'{__file__} {await fanc_name()} Invalid param. {param = }')
    #             return False
    #
    #     # TODO заменить на вызов конструктора QueryConstructor
    #     query: str = "DELETE FROM `" + table_name + "` WHERE `" + column_name + "` = ?"
    #     try:
    #         with self.connection:
    #             result = self.cursor.execute(query, (file_id,))
    #             return bool(result)
    #
    #     except sqlite3.OperationalError as err:
    #         logger.error(f"sqlite3.OperationalError {err = } {query = }")
    #         return False
    #
    #     finally:
    #         self.cursor.close()
    #
    # async def get_count_items(self, table_name: str):
    #     """Вывод кол-ва записей из core_violations
    #     """
    #     param_list: list = [table_name, ]
    #     for param in param_list:
    #         if not param:
    #             logger.error(f'{__file__} {await fanc_name()} Invalid param. {param = }')
    #             return 0
    #
    #     # TODO заменить на вызов конструктора QueryConstructor
    #     query: str = "SELECT COUNT(*) FROM `" + table_name + "`"
    #     try:
    #         with self.connection:
    #             result = self.cursor.execute(query).fetchone()
    #             return result
    #
    #     except sqlite3.OperationalError as err:
    #         logger.error(f"sqlite3.OperationalError {err = } {query = }")
    #         return []
    #
    #     finally:
    #         self.cursor.close()

    async def get_data_list(self, query: str = None) -> list:
        """Получение данных из таблицы по запросу query
        """
        param_list: list = [query]
        for param in param_list:
            if not param:
                logger.error(f'{__file__} {await fanc_name()} Invalid param. {param = }')
                return []

        try:
            with self.connection:
                return self.cursor.execute(query).fetchall()

        except sqlite3.OperationalError as err:
            logger.error(f"sqlite3.OperationalError {err = } {query = }")
            return []

        # finally:
        #     self.cursor.close()

    # async def get_dict_data_from_table_from_id(self, table_name: str, data_id: int, query: str = None) -> dict:
    #     """Получение данных из таблицы table_name по id
    #
    #     :param table_name: str - имя таблицы в БД
    #     :param data_id: int  id записи
    #     :param query: str запрос при наличии
    #     """
    #     check_result: bool = await get_check_param(__file__, await fanc_name(), table_name=table_name, data_id=data_id)
    #     if not check_result: return {}
    #
    #     if not query:
    #         query_kwargs: dict = {
    #             "action": 'SELECT', "subject": '*',
    #             "conditions": {
    #                 "id": data_id,
    #             },
    #         }
    #         query: str = await QueryConstructor(None, table_name, **query_kwargs).prepare_data()
    #
    #     values: list = await self.get_data_list(query=query)
    #     headers: list = [item[1] for item in await self.get_table_headers(table_name=table_name)]
    #     clean_values: list = values[0] if values else []
    #
    #     return dict((header, item_value) for header, item_value in zip(headers, clean_values))
    #
    # async def update_hse_user_language(self, *, value: str, hse_id: str):
    #     """Обновление записи id в database
    #
    #     :param hse_id: id записи
    #     :param value:  значение для записи в столбец
    #     """
    #     param_list: list = [value, hse_id]
    #     for param in param_list:
    #         if not param:
    #             logger.error(f'{__file__} {await fanc_name()} Invalid param. {param = }')
    #             return False
    #
    #     table_name: str = 'core_hseuser'
    #     query_kwargs: dict = {
    #         "action": 'UPDATE', "subject": 'hse_language_code', 'value': value,
    #         "conditions": {
    #             "title": hse_id,
    #         },
    #     }
    #     query: str = await QueryConstructor(None, table_name, **query_kwargs).prepare_data()
    #
    #     try:
    #         with self.connection:
    #             result = self.cursor.execute(query)
    #         self.connection.commit()
    #
    #         return bool(result.connection.total_changes)
    #
    #     except sqlite3.OperationalError as err:
    #         logger.error(f"sqlite3.OperationalError {err = } {query = }")
    #         return None
    #
    #     finally:
    #         self.cursor.close()
    #
    # async def update_violation_column_value(self, column_name: str, value: str, row_id: str) -> bool:
    #     """Обновление записи id в database
    #
    #     :param row_id: id записи
    #     :param value:  значение для записи в столбец
    #     :param column_name: столбец
    #     """
    #     param_list: list = [column_name, value, row_id]
    #     for param in param_list:
    #         if not param:
    #             logger.error(f'{__file__} {await fanc_name()} Invalid param. {param = }')
    #             return False
    #
    #     table_name: str = 'core_violations'
    #     query_kwargs: dict = {
    #         "action": 'UPDATE', "subject": column_name, 'value': value,
    #         "conditions": {
    #             "id": row_id,
    #         },
    #     }
    #
    #     query: str = await QueryConstructor(None, table_name, **query_kwargs).prepare_data()
    #     logger.debug(f'{column_name = } {value = }')
    #     try:
    #         with self.connection:
    #             result = self.cursor.execute(query)
    #         self.connection.commit()
    #         return bool(result.connection.total_changes)
    #
    #     except sqlite3.OperationalError as err:
    #         logger.error(f"sqlite3.OperationalError {err = } {query = }")
    #         return False
    #
    #     finally:
    #         self.cursor.close()
    #
    # async def update_column_value_for_query(self, query: str):
    #     """Обновление записи id в database
    #
    #     :param query: str
    #     :return: result
    #     """
    #     param_list: list = [query]
    #     for param in param_list:
    #         if not param:
    #             logger.error(f'{__file__} {await fanc_name()} Invalid param. {param = }')
    #             return False
    #
    #     try:
    #         with self.connection:
    #             result = self.cursor.execute(query)
    #         self.connection.commit()
    #         return bool(result.connection.total_changes)
    #
    #     except sqlite3.OperationalError as err:
    #         logger.error(f"sqlite3.OperationalError {err = } {query = }")
    #         return None
    #
    #     finally:
    #         self.cursor.close()
    #
    async def get_all_tables_names(self) -> list:
        """Получение всех имен таблиц в БД

        :return:
        """
        query: str = "SELECT name FROM sqlite_master WHERE type='table';"

        try:
            with self.connection:
                result: list = self.cursor.execute(query).fetchall()
                return result

        except sqlite3.OperationalError as err:
            logger.error(f"sqlite3.OperationalError {err = } {query = }")
            return []

        finally:
            self.cursor.close()

    # async def update_table_column_value(self, query: str, item_name: str, item_value: str) -> bool:
    #     """Обновление записи id в database
    #
    #     :param query: str
    #     :param item_name: str
    #     :param item_value: str
    #     """
    #     param_list: list = [query, item_name, item_value]
    #     for param in param_list:
    #         if not param:
    #             logger.error(f'{__file__} {await fanc_name()} Invalid param. {param = }')
    #             return False
    #
    #     try:
    #         with self.connection:
    #             result = self.cursor.execute(query, (item_value, item_name,))
    #         self.connection.commit()
    #         return bool(result)
    #
    #     except sqlite3.OperationalError as err:
    #         logger.error(f"sqlite3.OperationalError {err = } {query = }")
    #         return False
    #
    #     finally:
    #         self.cursor.close()
    #
    # async def set_act_value(self, act_data_dict: DataFrame, act_number: int, act_date: str) -> bool:
    #     """Добавление записи в database core_actsprescriptions"""
    #     param_list: list = [act_number, act_date]
    #     for param in param_list:
    #         if not param:
    #             logger.error(f'{__file__} {await fanc_name()} Invalid param. {param = }')
    #             return False
    #
    #     act_number = str(act_number)
    #     act_date = str(act_date)
    #     act_row_count = len(act_data_dict.index)
    #
    #     act_location_id = int(act_data_dict.location_id.unique()[0])
    #     act_week = int(act_data_dict.week_id.unique()[0])
    #     act_month = int(act_data_dict.month.unique()[0])
    #     act_quarter = int(act_data_dict.quarter.unique()[0])
    #     act_year = int(act_data_dict.year.unique()[0])
    #     act_hse_id = int(act_data_dict.hse_id.unique()[0])
    #
    #     act_status_id = int(act_data_dict.status_id.unique()[0])
    #     act_general_contractor_id = int(act_data_dict.general_contractor_id.unique()[0])
    #
    #     try:
    #         with self.connection:
    #             is_add = self.cursor.execute(
    #                 "INSERT INTO `core_actsprescriptions` ("
    #                 "`act_number`, `act_date`, `act_hse_id`, `act_row_count`, `act_location_id`,`act_week`,`act_month`,"
    #                 "`act_quarter`, `act_year`, `act_status_id`, `act_general_contractor_id` "
    #                 ")"
    #                 "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )",
    #                 (
    #                     act_number, act_date, act_hse_id, act_row_count, act_location_id, act_week, act_month,
    #                     act_quarter, act_year, act_status_id, act_general_contractor_id
    #                 )
    #             )
    #             if is_add:
    #                 logger.info(f"act {act_number} date {act_date} complete successfully for act_hse_id {act_hse_id}")
    #                 return True
    #
    #             logger.error(f"ERROR!!! act {act_number} date {act_date} error for act_hse_id {act_hse_id}")
    #             return False
    #
    #     except sqlite3.IntegrityError as err:
    #         logger.error(f"ERROR!!! act {act_number} date {act_date} error for act_hse_id {act_hse_id}")
    #         logger.error(f"sqlite3.IntegrityError {err}")
    #         return False
    #
    # async def get_full_title(self, table_name: str, short_title: str):
    #     """Получение полного имени из короткого
    #
    #     :param short_title: данные для поиска (короткое имя)
    #     :param table_name:имя таблицы для запроса
    #     """
    #     param_list: list = [table_name, short_title]
    #     for param in param_list:
    #         if not param:
    #             logger.error(f'{__file__} {await fanc_name()} Invalid param. {param = }')
    #             return False
    #
    #     query_kwargs: dict = {
    #         "action": 'SELECT', "subject": '*',
    #     }
    #     query: str = await QueryConstructor(None, table_name, **query_kwargs).prepare_data()
    #
    #     datas_query: list = await self.get_data_list(query=query)
    #     full_title = [item[1] for item in datas_query if item[2] == short_title][0]
    #
    #     return full_title
    #
    # async def get_max_number(self) -> int:
    #     """Получение максимального номера акта из Database `core_actsprescriptions`
    #     """
    #     query_kwargs: dict = {
    #         "action": 'SELECT', "subject": 'act_number',
    #     }
    #     query: str = await QueryConstructor(None, table_name='core_actsprescriptions', **query_kwargs).prepare_data()
    #
    #     datas_query: list = await self.get_data_list(query=query)
    #     number_list: list = [data_item[0] for data_item in datas_query]
    #     act_max_number = max(number_list)
    #     return act_max_number


#
#
# async def get_check_param(local_file: str, calling_function: str, **kvargs) -> bool:
#     """Проверка параметров """
#     calling_file: str = f'{os.sep}'.join(local_file.split(os.sep)[-2:])
#
#     result_list: list = []
#     print_dict: dict = {}
#
#     for param_num, param in enumerate(kvargs, start=1):
#
#         if kvargs[param] is None:
#             logger.error(f'{calling_file} {calling_function} Invalid param. #{param_num} {param = } {kvargs[param]}')
#         result_list.append(kvargs[param])
#         print_dict[param] = kvargs[param]
#
#     pprint(f'{await fanc_name()} :: {calling_function = } check_param: {print_dict}', width=200)
#     return all(result_list)
#
#
# async def upload_from_local(*, params: dict = None):
#     """Проверка валидация и загрузка файлов в database из local storage
#
#     :param params: dict с путями к файлам для загрузки
#
#     params{
#         'file_path': '...',
#         'user_file': '...'
#         }
#     """
#
#     json_file_list = await get_files(params['file_path'], endswith=".json")
#
#     len_err = 0
#     for counter, violation_file in enumerate(json_file_list, start=1):
#
#         error_counter, violation_data = await data_violation_completion(violation_file=violation_file, params=params)
#
#         if not await GroupDataBase().violation_exists(violation_data.get('file_id')):
#
#             is_add = await GroupDataBase().add_data(table_name='core_violations', data_dict=violation_data)
#             if is_add:
#                 logger.debug(f"{counter} file {violation_data.get('file_id')} add in db")
#
#             len_err += error_counter
#     logger.info(f"errors {len_err} in {len(json_file_list)} items")
#
#
# async def data_violation_completion(violation_file: str, params: dict) -> tuple[int, dict]:
#     """ """
#     error_counter: int = 0
#     # comment_counter: int = 0
#     # act_required_counter: int = 0
#     # elimination_time_counter: int = 0
#     # general_contractor_counter: int = 0
#     # incident_level_counter: int = 0
#
#     violation = await read_json_file(file=violation_file)
#     user_data_json_file = await read_json_file(file=params['user_file'])
#     file_id = violation.get('file_id')
#
#     if not violation.get("work_shift"):
#         violation["work_shift"] = user_data_json_file.get("work_shift")
#
#     if not violation.get("function"):
#         violation["function"] = user_data_json_file.get("function")
#
#     if not violation.get("name"):
#         violation["name"] = user_data_json_file.get("name")
#
#     if not violation.get("parent_id"):
#         violation["parent_id"] = user_data_json_file.get("parent_id")
#
#     if not violation.get("location"):
#         violation["location"] = user_data_json_file.get("name_location")
#
#     if not violation.get("status"):
#         logger.error(f"ERROR file: {file_id} don't get 'status' parameter")
#         error_counter += 1
#         violation["status"] = 'Завершено'
#
#     if not violation.get("violation_id"):
#         logger.error(f"ERROR file: {file_id} don't get 'violation_id' parameter")
#         error_counter += 1
#         violation["violation_id"] = violation['file_id'].split('___')[-1]
#
#     if not violation.get("json_folder_id"):
#         logger.error(f"ERROR file: {file_id} don't get 'json_folder_id' parameter")
#         error_counter += 1
#         violation["json_folder_id"] = '0'
#
#     if not violation.get('general_contractor'):
#         logger.error(f"ERROR file: {file_id} don't get 'general_contractor' parameter")
#         error_counter += 1
#
#         # general_contractor_counter += 1
#         # os.remove(violation_file)
#         # logger.info(f"file: {violation_file} is remove")
#
#     if not violation.get('elimination_time'):
#         logger.error(f"ERROR file: {file_id} don't get 'elimination_time' parameter")
#         error_counter += 1
#         # elimination_time_counter += 1
#         violation['elimination_time'] = '1 день'
#
#     if not violation.get('incident_level'):
#         logger.error(f"ERROR file: {file_id} don't get 'incident_level' parameter")
#         error_counter += 1
#         # incident_level_counter += 1
#         violation['incident_level'] = 'Без последствий'
#         await write_json(violation=violation)
#
#     if not violation.get('act_required'):
#         logger.error(f"ERROR file: {file_id} don't get 'act_required' parameter")
#         error_counter += 1
#         # act_required_counter += 1
#         violation['act_required'] = 'Не требуется*'
#
#     if not violation.get('comment'):
#         logger.error(f"ERROR file: {file_id} don't get 'comment' parameter")
#         error_counter += 1
#         # comment_counter += 1
#
#     # logger.info(f"general_contractor_counter {general_contractor_counter} in {error_counter} items")
#     # logger.info(f"elimination_time_counter {elimination_time_counter} in {error_counter} items")
#     # logger.info(f"act_required_counter {act_required_counter} in {error_counter} items")
#     # logger.info(f"incident_level_counter {incident_level_counter} in {error_counter} items")
#     # logger.info(f"comment_counter {comment_counter} in {error_counter} items")
#
#     await write_json(violation=violation)
#
#     return error_counter, violation
#
#
# async def write_json(violation):
#     """Запись в файл
#     """
#     if not os.path.isfile(violation['json_full_name']):
#         logger.info(f"FileNotFoundError {violation['json_full_name']} ")
#
#     date_violation = violation['file_id'].split('___')[0]
#
#     violation['json_full_name'] = \
#         f"C:\\Users\\KDeusEx\\PycharmProjects\\SWTS\\application\\media\\{violation['user_id']}\\data_file" \
#         f"\\{date_violation}\\json\\report_data___{violation['file_id']}.json"
#
#     await create_file_path(
#         f"C:\\Users\\KDeusEx\\PycharmProjects\\SWTS\\application\\media\\{violation['user_id']}\\data_file"
#         f"\\{date_violation}\\json\\"
#     )
#     violation['photo_full_name'] = \
#         f"C:\\Users\\KDeusEx\\PycharmProjects\\SWTS\\application\\media\\{violation['user_id']}\\data_file" \
#         f"\\{date_violation}\\photo\\report_data___{violation['file_id']}.jpg"
#
#     await create_file_path(
#         f"C:\\Users\\KDeusEx\\PycharmProjects\\SWTS\\application\\media\\{violation['user_id']}\\data_file"
#         f"\\{date_violation}\\photo\\"
#     )
#
#     await write_json_file(data=violation, name=violation['json_full_name'])
#
#
# async def get_files(main_path: str, endswith: str = ".json") -> list:
#     """Получение списка файлов c расширением endswith из main_path
#
#     :type main_path: str
#     :param main_path: директория для поиска файлов
#     :type endswith: str
#     :param endswith: расширение файлов для обработки и формирования списка
#     """
#     json_files = []
#     for subdir, _, files in os.walk(main_path):
#         for file in files:
#             filepath = subdir + os.sep + file
#             if filepath.endswith(endswith):
#                 json_files.append(filepath)
#     return json_files
#
#
# async def read_json_file(file: str):
#     """Получение данных из json.
#
#     :param file: полный путь к файлу
#     """
#     try:
#         with open(file, 'r', encoding='utf8') as data_file:
#             data_loaded = json.load(data_file)
#         return data_loaded
#
#     except FileNotFoundError:
#         return None
#
#
# async def write_json_file(name: str, data) -> bool:
#     """Запись данных в json
#
#     :param name: полный путь для записи / сохранения файла включая расширение,
#     :param data: данные для записи / сохранения
#     :return: True or False
#     """
#     try:
#         with io.open(name, 'w', encoding='utf8') as outfile:
#             str_ = json.dumps(data,
#                               indent=4,
#                               sort_keys=True,
#                               separators=(',', ': '),
#                               ensure_ascii=False)
#             outfile.write(str_)
#             return True
#     except TypeError as err:
#         logger.error(f"TypeError: {repr(err)}")
#         return False
#
#
# async def create_file_path(path: str):
#     """Проверка и создание путей папок и файлов
#
#     :param path:
#     :return:
#     """
#     if not os.path.isdir(path):
#         # logger.info(f"user_path{path} is directory")
#         try:
#             os.makedirs(path)
#
#         except Exception as err:
#             logger.info(f"makedirs err {repr(err)}")


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])


async def test():
    result = GroupDataBase().get_all_tables_names()
    for item in result:
        logger.info(f"'{item}'")

    act_num: int = GroupDataBase().get_max_number()
    logger.info(f"{act_num = }")

    table_name = 'core_generalcontractor'
    short_title = 'ООО УМ'
    full_title = GroupDataBase().get_full_title(table_name=table_name, short_title=short_title)
    logger.info(f'{full_title = }')

    table_name = 'core_sublocation'
    post_id = 10
    data_exists: dict = GroupDataBase().get_dict_data_from_table_from_id(
            table_name=table_name,
            id=post_id,
    )
    logger.info(f'{data_exists = }')

    result = GroupDataBase().create_backup()
    logger.info(f'{result = }')


async def test_2():
    file_id: str = '10.01.2024___373084462___9229'
    result = await GroupDataBase().get_id_violation(file_id=file_id)
    pprint(f'{await fanc_name()} ::: {file_id = } ::: {result = }', width=160)


async def test_3():
    file_id: str = '10.01.2024___373084462___9229'
    result = await GroupDataBase().get_single_violation(file_id=file_id)
    pprint(f'{await fanc_name()} ::: {file_id = } ::: {result = }', width=160)


async def test_4():
    file_id: str = '10.01.2024___373084462___9229'
    result = await GroupDataBase().violation_exists(file_id=file_id)
    pprint(f'{await fanc_name()} ::: {file_id = } ::: {result = }', width=160)


async def test_5():
    user_telegram_id: int = 373084462
    result = await GroupDataBase().user_exists(user_telegram_id=user_telegram_id)
    pprint(f'{await fanc_name()} ::: {user_telegram_id = } ::: {result = }', width=160)


async def test_6():
    user_telegram_id: str = str(373084462)
    language_value = 'ru'
    result = await GroupDataBase().update_hse_user_language(value=language_value, hse_id=user_telegram_id)
    pprint(f'{await fanc_name()} ::: {user_telegram_id = } ::: {result = }', width=160)


async def test_7():
    row_id: str = str(10767)
    value = '373084462'
    column_name = 'user_id'

    result = await GroupDataBase().update_violation_column_value(
            column_name=column_name, value=value, row_id=row_id
    )

    pprint(f'{await fanc_name()} ::: {row_id = } ::: {result = }', width=160)


async def test_8():
    table_name = 'core_violations'
    data_id = 12121

    result = await GroupDataBase().get_dict_data_from_table_from_id(table_name, data_id)
    pprint(f'{await fanc_name()} ::: {table_name = } ::: {result = }', width=160)
    pprint(f'{await fanc_name()} ::: {table_name = } ::: {data_id = }', width=160)


if __name__ == '__main__':
    # asyncio.run(test_2())
    # asyncio.run(test_3())
    # asyncio.run(test_4())
    # asyncio.run(test_5())
    # asyncio.run(test_6())
    # asyncio.run(test_7())
    asyncio.run(test_8())
