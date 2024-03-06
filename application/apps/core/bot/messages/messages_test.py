from __future__ import annotations

import os
import asyncio
import sqlite3
from datetime import datetime

from loader import logger
from config.config import Novolex_MSG_DB
from apps.core.bot.messages.messages import Messages
from apps.core.database.query_constructor import QueryConstructor
from apps.core.database.db_utils import db_get_dict_userdata


class DataBaseMSG:

    def __init__(self):

        if not os.path.exists(Novolex_MSG_DB):
            logger.error(f'Path {Novolex_MSG_DB} is not exists!')

        self.db_file: str = Novolex_MSG_DB
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

        with self.connection:
            result: list = self.cursor.execute(f"PRAGMA table_info('{table_name}')").fetchall()
            clean_headers: list = [item[1] for item in result]
            return clean_headers

    async def get_all_tables_names(self) -> list:
        """Получение всех имен таблиц в БД

        :return:
        """
        with self.connection:
            result: list = self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
            return result

    async def get_data_list(self, query: str = None) -> list:
        """Получение данных из таблицы по запросу 'query'"""
        if not query:
            return []

        with self.connection:
            return self.cursor.execute(query).fetchall()

    async def get_data_list_without_query(self, table_name: str = None) -> list:
        """Получение данных из таблицы table_name"""
        try:
            with self.connection:
                query_kwargs: dict = {
                    "action": 'SELECT', "subject": '*',
                }
                query: str = await QueryConstructor(None, table_name, **query_kwargs).prepare_data()
                result: list = self.cursor.execute(query).fetchall()
                if not result:
                    logger.error(f"no matches found {table_name} in DB "
                                 f"because .cursor.execute is none `table_name`: {table_name}")
                    return []
            return result

        except (ValueError, sqlite3.OperationalError) as err:
            logger.error(f'Invalid query. {repr(err)}')
            return []

        finally:
            self.cursor.close()


class MSG:
    """Класс возврата сообщений на языке пользователя"""

    def __init__(self, user_id: int | str, *, cat=None, msge: str = None, default: str = None, lang: str = '',
                 now: bool = False):

        """Инициация класса сообщений MSG для определения языка интерфейса пользователя

        :param user_id: int | str : id пользователя
        :param cat: str : optional : категория  в которой идет поиск сообщения
        :param msge: str : optional : сообщение для поиска
        :param default: str : optional : сообщение по умолчанию
        :param now: bool : optional : требование немедленного возврата сообщения (блокирующая функция)
        """
        self.user_id: str | int = user_id
        self.__language: str = ''
        self._user_language: str = lang
        self.__default_lang: str = 'ru'
        self.__default_category: str = 'msg_main'
        self.category: str = f'msg_{cat}' if cat else self.__default_category
        self.message: str = msge
        self.default = default

        if now: self.get_msg()

    def __str__(self) -> str:
        """Возврат строкового значения"""
        return f'str: {self.get_msg(self.message)}'

    async def __check_category_in_db(self, category: str = None) -> str:
        """Проверка наличия категории в базе данных

        :param category:
        :return:
        """

        all_tables: list = await DataBaseMSG().get_all_tables_names()

        if not all_tables:
            logger.error(f'Error get all_tables DB ! '
                         f'Set default_category: {self.__default_category}')
            return self.__default_category

        all_tables: list = [item[0] for item in all_tables if 'msg_' in item[0]]

        if category not in all_tables:
            logger.error(f'Error check {category = } in all_tables DB {all_tables}! '
                         f'Set default_category: {self.__default_category}')
            return self.__default_category

        return category

    async def __check_language_in_db(self, language: str, category: str = None) -> str:
        """Проверка наличия языка в базе данных

        :param category: str категория для поиска в БД
        :param language: str язык интерфейса
        :return: language: str - язык интерфейса после проверки
        """
        check_language = language if language else self.__language

        table_name: str = 'msg_main'
        table_name_category: str = f'{category}' if category is not None else table_name

        clean_headers: list = await DataBaseMSG().get_table_headers(table_name_category)
        if not clean_headers:
            logger.error(f'Error check language in table {table_name_category} in DB! '
                         f'Set default_lang: {self.__default_lang}')
            return self.__default_lang

        lang_list = [row.replace('lang_', '') for row in clean_headers if 'lang_' in row]

        if check_language not in lang_list:
            logger.warning(f'{self.user_id} Lang {language} not in {table_name = }')

        lang: str = check_language if check_language in lang_list else self.__default_lang
        return lang

    async def get_user_lang(self, user_id: int | str = None) -> str:
        """Получение значения языка пользователя пл id

        :param user_id: int | str : id пользователя
        :return:
        """

        result: str = await self.__get_user_lang(user_id=user_id)
        return result

    async def __get_user_lang(self, user_id: int | str = None) -> str:
        """Получение языка интерфейса пользователя по user_id

        :param user_id: int | str : id пользователя
        :return: str hse_language
        """
        user_id = user_id if user_id else self.user_id

        if user_id is None:
            return self.__default_lang

        dict_user: dict = await db_get_dict_userdata(user_id=user_id)
        hse_language: str = dict_user.get('hse_language_code', None)
        return hse_language

    async def get_message_from_db(self, message: str = None, category: str = None, lang: str = None) -> str:
        """Получение сообщение из БД на основе языка lang

        :param message: str сообщение для поиска в БД
        :param category: str категория для поиска в БД
        :param lang: str язык интерфейса
        :return:
        """
        result: str = await self.__get_message_from_db(message=message, category=category, lang=lang)
        return result

    async def __get_message_from_db(self, message: str = None, category: str = None, lang: str = None) -> str:
        """Получение сообщение из БД на основе языка lang

        :param message: str сообщение для поиска в БД
        :param category: str категория для поиска в БД
        :param lang: str язык интерфейса
        :return:
        """
        message: str = message if message else self.message
        table_name: str = category if category else self.category
        lang: str = lang if lang else self.__default_lang

        try:
            datas_list: list = await DataBaseMSG().get_data_list_without_query(table_name=table_name)

        except sqlite3.OperationalError as err:
            logger.error(f'The "{message}" {table_name = } is missing from the database! err: {repr(err)}')
            return f'def msg :{self.user_id} ::: {self.default}'

        if not datas_list:
            logger.error(f'Missing datas_list from the database. Set default value: {self.default}')
            return f'def msg :{self.user_id} ::: {self.default}'

        clean_headers: list = await DataBaseMSG().get_table_headers(table_name)
        list_dicts: list = [dict(zip(clean_headers, data_list)) for data_list in datas_list]

        try:
            f_message: list = [item.get(f'lang_{lang}') for item in list_dicts if item.get('title') == message]

        except IndexError as err:
            logger.error(f'The "{message}" value is missing from the database. '
                         f'Set default value: {self.default} err: {repr(err)}')
            return f'def msg :{self.user_id} ::: {self.default}'

        if len(f_message) >= 2:
            logger.warning(f'The "{message}" have 2 or more values\n used first values {f_message[0] = }')
            return f_message[0]

        if len(f_message) == 0:
            logger.error(f'The "{message}" value is missing from the database. '
                         f'Set default value: {self.default}')
            return self.default

        return f_message[-1]

    @staticmethod
    async def __post_processing_text(text: str) -> str:
        """Пост обработка текста полученного из базы по запросу

        :param text:
        :return:
        """
        if not text:
            return ''

        post_text: str = text.replace('\\n', '\n')
        return post_text

    async def __get_msg(self, message: str = None, category: str = None, use_id: bool = False, lang: str = None) -> str:
        """Асинхронное получение сообщения из БД

        :param message: сообщение для поиска
        :param use_id: использование id пользователя для отображения в теле сообщения
        :param lang: сообщение для поиска
        :param category: 'msg_{category}' - категория для поиска
        :return: str - текст сообщения
        """

        _message: str = message if message else self.message
        _category: str = category if category else self.category
        _user_language = lang if lang else self._user_language

        try:
            _category: str = await self.__check_category_in_db(category=_category)
            _lang: str = _user_language if _user_language else await self.__get_user_lang(user_id=self.user_id)
            _language: str = _lang if _lang else self.__default_lang
            _checked_language: str = await self.__check_language_in_db(
                language=_language, category=_category
            )
            _f_message: str = await self.__get_message_from_db(
                message=_message, category=_category, lang=_checked_language
            )
            _f_message: str = await self.__post_processing_text(text=_f_message)

            if not _f_message:
                _f_message = self.default

            if not use_id:
                return f'{_f_message}'
            return f'id: {self.user_id} ::: {_f_message}'

        except TypeError as err:
            logger.error(f'{repr(err)}')
            if not use_id:
                return f'{self.default}'
            return f'set def msg :{self.user_id} ::: {self.default}'

    async def get_lang_in_main(self, table: str = None) -> list:
        """Проверка наличия языка в базе данных

        :return: language: str - язык интерфейса после проверки
        """

        table_name: str = 'msg_main'
        table_name_category: str = f'{table}' if table is not None else table_name

        clean_headers: list = await DataBaseMSG().get_table_headers(table_name)
        if not clean_headers:
            logger.error(f'Error check language in table {table_name_category} in DB! '
                         f'Set default_lang: {self.__default_lang}')
            return [self.__default_lang]

        lang_list: list = [row.replace('lang_', '') for row in clean_headers if 'lang_' in row]

        if not lang_list:
            logger.error(f'{self.user_id} error get lang_list from table {table_name_category}'
                         f'Set default_lang: {self.__default_lang}')
            return [self.__default_lang]

        return lang_list

    async def g_mas(self, message: str = None, category: str = None, lang: str = None) -> str:
        """Асинхронное получение сообщения из БД

        :param message: сообщение для поиска
        :param category: 'msg_{category}' - категория для поиска
        :param lang: язык пользователя по умолчанию
        :return: str
        """
        message: str = message if message else self.message
        category: str = f'msg_{category}' if category else self.category
        lang: str = lang if lang else self._user_language

        f_message = asyncio.run(self.__get_msg(message, category, lang=lang))
        return f_message

    def get_msg(self, message: str = None, category: str = None, use_id: bool = False, lang: str = None) -> str:
        """Получение языка из БД

        :param use_id: использование user_id в возвращаемом сообщении
        :param message: сообщение для поиска
        :param category: 'msg_{category}' категория для поиска
        :param lang: язык пользователя по умолчанию
        :return: str
        """

        message: str = message if message else self.message
        category: str = f'msg_{category}' if category else self.category
        lang: str = lang if lang else self._user_language

        f_message = asyncio.run(self.__get_msg(message, category, use_id, lang=lang))
        return f_message


msg = MSG


async def test(user_hse_id: int | str):
    """Тестовая функция"""
    message: str = await msg(
        user_hse_id, cat='', msge="acts_generated", default=Messages.Report.acts_generated_successfully
    ).g_mas()
    logger.info(f'{message}')

    message: str = str(await msg(hse_id, cat='msg_main', msge="acts_generated_successfully").g_mas())
    logger.info(f'{message}')

    message: str = str(msg(hse_id, msge="acts_generated_successfully"))
    logger.info(f'{hse_id = } ::: {message}')

    message: str = str(msg(hse_id, msge="acts_generated_successfully", now=True))
    logger.info(f'{hse_id = } ::: {message}')

    message: str = "acts_generated_successfully"
    category: str = 'msg_main'

    lang: str = await msg(hse_id).get_user_lang()
    message = await msg(hse_id, msge=message, cat=category).get_message_from_db(lang=lang)
    print(message)


if __name__ == '__main__':
    hse_id: int = 373084462

    for i in range(1, 10 + 1):
        default_msg = Messages.Report.acts_generated_successfully
        logger.info(f'{msg(hse_id, cat="main", msge="acts_generated_successfully", default=default_msg).get_msg()}')

    logger.info(msg(hse_id, cat="main", msge="acts_generated_successfully",
                    default=Messages.Report.acts_generated_successfully).get_msg())
    logger.info(f'{str(msg(hse_id, cat="main", msge="acts_generated_successfully", now=True))}')

    asyncio.run(test(hse_id), debug=True)
