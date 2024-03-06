from __future__ import annotations

from loader import logger

logger.debug(f"{__name__} start import")

import traceback
import asyncio

import os
import sqlite3
from datetime import datetime

from config.config import Udocan_HSE_Check_Lists

logger.debug(f"{__name__} finish import")


class DataBaseCheckLists:

    def __init__(self):

        self.db_file = Udocan_HSE_Check_Lists
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

        try:
            str_time: str = datetime.now().strftime('%d.%m.%Y, %H.%M.%S')
            query: str = f"vacuum into '{backup_file_path}backup_{str_time}_{self.name}.db'"
            with self.connection:
                result = self.cursor.execute(query)
                logger.info(f'{await fanc_name()}. {result = }')
                return self.name

        except (ValueError, sqlite3.OperationalError) as err:
            logger.error(f'{__file__} {await fanc_name()} Invalid query. {repr(err)}')
            return None

        finally:
            self.cursor.close()

    async def add_data(self, table_name: str, data_dict: dict) -> bool:
        """Добавление данных в БД
        """
        if not table_name: return False
        if not data_dict: return False

        dict_keys = ', '.join(list(data_dict.keys()))
        qs = ', '.join(['?'] * len(data_dict))
        sqlite_insert_with_param: str = "INSERT INTO `" + table_name + "` (" + dict_keys + ") VALUES (" + qs + ");"
        data_tuple: tuple = tuple(data_dict.values())

        try:
            with self.connection:
                result = self.cursor.execute(sqlite_insert_with_param, data_tuple)
                logger.info(f'{await fanc_name()}. {result = }')
                if result:
                    return True

                return False

        except (ValueError, sqlite3.IntegrityError, sqlite3.OperationalError) as err:
            logger.error(f'{__file__} {await fanc_name()} Invalid query. {repr(err)}')
            return False

        finally:
            self.cursor.close()

    async def get_table_headers(self, table_name: str) -> list[str]:
        """Получение всех заголовков таблицы core_violations

        :return: list[ ... ]
        """
        if not table_name:
            return []

        try:
            query: str = f"PRAGMA table_info('{table_name}')"
            with self.connection:
                result = self.cursor.execute(query).fetchall()
                logger.info(f'{await fanc_name()}. {result = }')
                return result

        except (ValueError, sqlite3.IntegrityError, sqlite3.OperationalError) as err:
            logger.error(f'{__file__} {await fanc_name()} Invalid query. {repr(err)}')
            return []

        finally:
            self.cursor.close()

    async def get_count_items(self, table_name: str) -> tuple :
        """Вывод кол-ва записей из table_name
        """
        if not table_name:
            return ()

        try:
            query: str = 'SELECT COUNT(*) FROM `' + table_name + '`'
            with self.connection:
                result = self.cursor.execute(query).fetchone()
                logger.info(f'{await fanc_name()}. {result = }')
                return result

        except (ValueError, sqlite3.IntegrityError, sqlite3.OperationalError) as err:
            logger.error(f'{__file__} {await fanc_name()} Invalid query. {repr(err)}')
            return ()

        finally:
            self.cursor.close()

    async def get_all_tables_names(self):
        """Получение всех имен таблиц в БД

        :return:
        """
        try:
            query: str = "SELECT name FROM sqlite_master WHERE type='table';"
            with self.connection:
                result = self.cursor.execute(query).fetchall()
                logger.info(f'{await fanc_name()}. {result = }')
                return result

        except (ValueError, sqlite3.IntegrityError, sqlite3.OperationalError) as err:
            logger.error(f'{__file__} {await fanc_name()} Invalid query. {repr(err)}')
            return False

        finally:
            self.cursor.close()


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])


async def test():
    result = await DataBaseCheckLists().get_all_tables_names()
    result = [item[0] for item in result if 'checklists_' in item[0]]

    # clean_result = [item[0].replace('checklists_', '') for item in result if 'checklists_' in item[0]]
    # print(f'{clean_result = }')

    for item in result:
        result = await DataBaseCheckLists().get_count_items(table_name=item)
        clean_result = result[0] if result else 0
        print(f'{item}: {clean_result = }')

    # result = await DataBaseCheckLists().create_backup()
    # logger.info(f'{result = }')


if __name__ == '__main__':
    asyncio.run(test())
