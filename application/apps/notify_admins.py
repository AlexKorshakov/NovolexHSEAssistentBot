from __future__ import annotations
import asyncio
import os
import sqlite3
from datetime import datetime

from aiogram import Dispatcher
from pandas import DataFrame

from apps.core.bot.messages.messages import Messages
from apps.core.database.query_constructor import QueryConstructor
from config.config import DEVELOPER_ID, Novolex_HSE_Violations_DB
from loader import logger


class DataBaseAccessToAdmins:

    def __init__(self):

        self.db_file = Novolex_HSE_Violations_DB
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
                # clean_headers: list = [item[1] for item in result]
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


async def db_get_data_list(query: str) -> list:
    """Получение list с данными по запросу query

    :return: list
    """
    datas_query: list = await DataBaseAccessToAdmins().get_data_list(query=query)
    return datas_query


async def db_get_table_headers(table_name: str = None) -> list:
    """Получение заголовков таблицы

    :return:
    """
    table_headers: list = await DataBaseAccessToAdmins().get_table_headers(table_name)
    return table_headers


async def on_startup_notify_admins(dp: Dispatcher) -> bool:
    """

    :param dp:
    :return:
    """
    logger.info(f"{dp.bot._me.first_name} Оповещение администрации...")

    hse_dataframe: DataFrame = await get_hse_dataframe()
    if not await check_dataframe(hse_dataframe, hse_user_id=DEVELOPER_ID):
        await dp.bot.send_message(chat_id=DEVELOPER_ID, text=f'{dp.bot._me.first_name} Данные не найдены hse_dataframe')
        return False

    hse_role_is_admins_list: list = await get_hse_role_is_admins_list(
        hse_dataframe=hse_dataframe
    )
    if not hse_role_is_admins_list:
        logger.error(f"{dp.bot._me.first_name} {hse_role_is_admins_list = } ")
        return False

    hse_role_receive_notifications_list: list = await get_hse_role_receive_notifications_list(
        hse_dataframe=hse_dataframe
    )
    if not hse_role_receive_notifications_list:
        logger.error(f"{dp.bot._me.first_name} {hse_role_receive_notifications_list = } ")
        return False

    for num, hse_telegram_id in enumerate(hse_role_is_admins_list, start=1):

        if not hse_telegram_id:
            logger.debug(
                f"{dp.bot._me.first_name} Значение не найдено {num = } for {len(hse_role_is_admins_list)} {hse_telegram_id = }")
            continue

        if hse_telegram_id not in hse_role_receive_notifications_list:
            logger.debug(
                f"{dp.bot._me.first_name} Значение не найдено {num = } for {len(hse_role_is_admins_list)} {hse_telegram_id = }")
            continue

        try:
            await dp.bot.send_message(hse_telegram_id, f"{dp.bot._me.first_name} Бот был успешно запущен",
                                      disable_notification=True)
            logger.info(f"{dp.bot._me.first_name} Сообщение отправлено {hse_telegram_id}")
            await asyncio.sleep(0.5)

        except Exception as err:
            logger.error(f"{dp.bot._me.first_name} Чат {num = } с админом {hse_telegram_id} не найден {err = } ")

    return True


async def get_hse_role_is_admins_list(hse_dataframe: DataFrame) -> list:
    """Получение списка админов
    """

    current_hse_role_is_admin_df: DataFrame = hse_dataframe.loc[
        hse_dataframe['hse_role_is_admin'] == 1
        ]
    unique_hse_telegram_id: list = current_hse_role_is_admin_df.hse_telegram_id.unique().tolist()
    return unique_hse_telegram_id


async def get_hse_role_receive_notifications_list(hse_dataframe: DataFrame) -> list:
    """Получение списка пользователей кому отправляются уведомления
    """

    current_hse_role_receive_df: DataFrame = hse_dataframe.loc[
        hse_dataframe['hse_role_receive_notifications'] == 1
        ]
    unique_hse_telegram_id: list = current_hse_role_receive_df.hse_telegram_id.unique().tolist()
    return unique_hse_telegram_id


async def get_hse_dataframe() -> DataFrame or None:
    """Получение данных пользователей
    """

    table_name: str = 'core_hseuser'
    kwargs: dict = {
        "action": 'SELECT',
        "subject": '*',
    }
    query: str = await QueryConstructor(table_name=table_name, **kwargs).prepare_data()
    datas_query: list = await db_get_data_list(query=query)

    if not datas_query:
        return None

    if not isinstance(datas_query, list):
        return None

    clean_headers: list = [item[1] for item in await db_get_table_headers(table_name=table_name)]
    if not clean_headers:
        return None

    try:
        hse_role_receive_df: DataFrame = DataFrame(datas_query, columns=clean_headers)
        return hse_role_receive_df

    except Exception as err:
        logger.error(f"create_dataframe {repr(err)}")
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


async def test():
    dp: Dispatcher = None
    await on_startup_notify_admins(dp)


if __name__ == '__main__':
    asyncio.run(test())
