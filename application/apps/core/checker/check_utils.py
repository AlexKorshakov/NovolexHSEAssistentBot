from __future__ import annotations

from sqlite3 import Cursor

"""Модуль со вспомогательными функциями класса DataBaseForCheck"""

from loader import logger
logger.debug(f"{__name__} start import")

import os
from pathlib import Path
import sqlite3
from datetime import datetime, timedelta
import traceback

from apps.core.bot.messages.messages import LogMessage
from apps.core.database.query_constructor import QueryConstructor
from config.config import Novolex_main_data_base_dir

logger.debug(f"{__name__} finish import")


class DataBaseForCheck:
    """Основной класс работы с базой данных для класса PeriodicCheck
    """

    def __init__(self):
        self.db_file: str | Path = Novolex_main_data_base_dir
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

    async def get_data_list(self, query: str = None) -> list:
        """Получение данных из таблицы по запросу 'query'"""
        if not query:
            return []
        try:
            with self.connection:
                return self.cursor.execute(query).fetchall()
        except sqlite3.OperationalError as err:
            logger.error(f"error {repr(err)}")
            return []

    async def get_table_headers(self, table_name: str = None) -> list[str]:
        """Получение всех заголовков таблицы core_violations

        :param table_name: имя таблицы в которой осуществляется поиск
        :return: list[ ... ]
        """

        if table_name:
            # TODO заменить на вызов конструктора QueryConstructor
            query: str = f"PRAGMA table_info('{table_name}')"
            print(f'{__name__} {say_fanc_name()} {query}')
            with self.connection:
                result = self.cursor.execute(query).fetchall()
                return result

        with self.connection:
            result = self.cursor.execute("PRAGMA table_info('core_violations')").fetchall()
            return result

    async def get_dict_data_from_table_from_id(self, table_name: str, violation_id: int) -> dict:
        """Получение данных dict из таблицы table_name по id
        :param table_name: имя таблицы в которой осуществляется поиск
        :param violation_id: id записи
        :return dict('header': item_value, ...)
        """

        query_kwargs: dict = {
            "action": 'SELECT',
            "subject": '*',
            "conditions": {
                "violation_id": violation_id,
            },
        }
        query: str = await QueryConstructor(None, table_name, **query_kwargs).prepare_data()

        val: list = await self.get_data_list(query=query)
        values: list = val[0] if val else []
        headers: list = [item[1] for item in await self.get_table_headers(table_name)]

        return dict((header, item_value) for header, item_value in zip(headers, values))

    async def update_column_value(self, column_name: str, value: str, violation_id: str):
        """Обновление записи id в database

        :param violation_id: id записи
        :param value:  значение для записи в столбец
        :param column_name: столбец
        """
        # TODO заменить на вызов конструктора QueryConstructor
        query: str = f"UPDATE `core_violations` SET {column_name} = ? WHERE `id` = ?"
        print(f'{__name__} {say_fanc_name()} {query}')

        logger.debug(f'{column_name = } {value = }')
        with self.connection:
            self.cursor.execute(query, (value, violation_id,))
        self.connection.commit()


async def check_violations_final_date_elimination() -> bool:
    """Проверка записей в core_violations с истекшей датой устранения

    :return:
    """
    query_kwargs: dict = {
        "action": 'SELECT',
        "subject": '*',
        "conditions": {
            "finished_id": "0",
            "status_id": "== 2"
        },
    }
    query: str = await QueryConstructor(None, 'core_violations', **query_kwargs).prepare_data()

    list_violations: list = await get_list_violations_for_query(query=query)

    counter: int = 0
    for violation in list_violations:

        created_at, final_date = await get_dates_violation(violation)
        if created_at is None or final_date is None:
            continue

        if datetime.now() >= final_date:
            violation_id = violation.get('id', None)
            logger.info(f'{violation_id = }  now >= final_date_elimination')
            await DataBaseForCheck().update_column_value(column_name='finished_id',
                                                         value=str(2),
                                                         violation_id=str(violation_id)
                                                         )
            counter += 1

    if not counter:
        logger.debug(f"{LogMessage.Check.no_violations} ::: {await get_now()}")

    return True


async def check_violations_status():
    """Проверка поля status

    :return:
    """
    query_kwargs: dict = {
        "action": 'SELECT',
        "subject": '*',
        "conditions": {
            "finished_id": "1",
            "status_id": "!= 1"
        },
    }
    query: str = await QueryConstructor(None, 'core_violations', **query_kwargs).prepare_data()

    list_violations: list = await get_list_violations_for_query(query=query)

    if not list_violations:
        logger.debug(f"{LogMessage.Check.no_violations} ::: {await get_now()}")
        return []

    counter: int = 0
    for violation in list_violations:
        violation_id = violation.get('id', None)
        status_id = violation.get('status_id', None)
        finished_id = violation.get('finished_id', None)

        if finished_id == 1 and status_id != 1:
            logger.info(f'{violation_id= } ::: {finished_id = } ::: {status_id = }')
            await DataBaseForCheck().update_column_value(
                column_name='status_id',
                value=str(1),
                violation_id=str(violation_id)
            )
            counter += 1

    if not counter:
        logger.debug(f"{LogMessage.Check.no_violations} ::: {await get_now()}")


async def get_list_violations_for_query(query: str) -> list:
    """Возвращает list с нарушениями

    :return: list
    """

    if not query:
        logger.error(f"{LogMessage.Check.no_query} ::: {await get_now()}")
        return []

    list_violations: list = []
    table_name = 'core_violations'

    violations_data: list = await DataBaseForCheck().get_data_list(query=query)

    if not violations_data:
        logger.debug(f"{LogMessage.Check.no_violations} ::: {await get_now()}")
        return []

    headers = await DataBaseForCheck().get_table_headers(table_name=table_name)
    clean_headers: list = [item[1] for item in headers]

    for violation in violations_data:
        item_dict: dict = dict((header, item_value) for header, item_value in zip(clean_headers, violation))
        list_violations.append(item_dict)

    return list_violations


async def get_clean_headers(table_name: str) -> list:
    """Получение заголовков таблицы

    :param table_name: имя таблицы в которой осуществляется поиск
    """

    if not table_name:
        return []

    headers = await DataBaseForCheck().get_table_headers(table_name=table_name)
    clean_headers: list = [item[1] for item in headers]

    logger.debug(f'{clean_headers = }')
    return clean_headers


async def get_dates_violation(violation: dict):
    """Возвращает дату регистрации и конечную даты акта

    """
    created_at = violation.get('created_at', None)

    if created_at is None:
        logger.debug(f"{LogMessage.Check.date_created_at} ::: {await get_now()}")
        return None, None

    elimination_days: int = await get_elimination_days(e_time=violation.get('elimination_time_id', None))

    date_now: datetime = datetime.strptime(created_at, '%Y-%m-%d')
    final_date_elimination = date_now + timedelta(days=elimination_days)

    return created_at, final_date_elimination


async def get_elimination_days(e_time: int) -> int:
    """Получение количества дней на устранение

    :return:
    """
    if e_time is None:
        return 0

    elimination_time: dict = await DataBaseForCheck().get_dict_data_from_table_from_id(
        table_name='core_eliminationtime',
        violation_id=e_time
    )
    elimination_days = elimination_time.get('days', None)
    return elimination_days


async def get_now() -> str:
    """Возвращает текущую дату и время.
    :return: str
    """
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")


def say_fanc_name():
    stack = traceback.extract_stack()
    return str(stack[-2][2])


# if __name__ == '__main__':
#     asyncio.create_qr_code(periodic_check_data_base())
