from __future__ import annotations

from loader import logger
logger.debug(f"{__name__} start import")

import os
import asyncio
from datetime import date, datetime, timedelta
import traceback
from pandas import DataFrame
from sqlite3 import OperationalError

from apps.core.database.ViolationsDataBase import DataBaseViolations
from apps.core.database.query_constructor import QueryConstructor

logger.debug(f"{__name__} finish import")


async def db_check_violation_exists(file_id: str) -> bool:
    """Проверка наличия записи в БД

    :param file_id: int - id записи
    :return: bool is_exists
    """
    is_exists: bool = await DataBaseViolations().violation_exists(file_id=file_id)
    return bool(is_exists)


async def db_check_user_record_existence(user_telegram_id: int) -> bool:
    """Проверка наличия пользователя user_telegram_id в таблице `core_hseuser`

    :param user_telegram_id: int - id записи пользователя в `core_hseuser`
    :return: bool True if is_exists else False
    """
    is_exists: bool = await DataBaseViolations().user_exists(user_telegram_id=user_telegram_id)
    return bool(is_exists)


async def db_add_violation(violation_data: dict) -> bool:
    """Добавление записи в БД

    :param violation_data: dict - dict с данными для записи в БД
    :return: bool violation_exists
    """

    if not violation_data: return False

    is_added: bool = await DataBaseViolations().add_data(
        table_name='core_violations', data_dict=violation_data
    )
    return bool(is_added)


async def db_add_new_user(hseuser_data: dict) -> bool:
    """Добавление записи в БД

    :param hseuser_data: dict - dict с данными для записи в БД
    :return: bool violation_exists
    """

    if not hseuser_data: return False

    is_added: bool = await DataBaseViolations().add_data(
        table_name='core_hseuser', data_dict=hseuser_data
    )
    return bool(is_added)


async def db_get_data_dict_from_table_with_id(table_name: str, post_id: int, query: str = None) -> dict:
    """Получение данных из table_name с помощью post_id

    :return: dict - dict с данными
    """

    check_result: bool = await get_check_param(__file__, await fanc_name(), table_name=table_name, post_id=post_id)
    if not check_result: return {}

    data_exists: dict = await DataBaseViolations().get_dict_data_from_table_from_id(
        table_name=table_name, data_id=post_id, query=query
    )

    return data_exists


async def db_get_categories() -> list:
    """

    :return:
    """
    query_kwargs: dict = {
        "action": 'SELECT', "subject": 'title',
    }
    query: str = await QueryConstructor(None, 'core_category', **query_kwargs).prepare_data()

    categories: list = await db_get_data_list(query=query)
    clean_categories: list = [item[0] for item in categories]

    return clean_categories


async def db_get_categories_list() -> list:
    """

    :return:
    """
    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
    }
    query: str = await QueryConstructor(None, 'core_category', **query_kwargs).prepare_data()
    categories: list = await db_get_data_list(query=query)
    clean_headers = await db_get_clean_headers(table_name='core_category')
    categories_list = [dict(zip(clean_headers, cat)) for cat in categories]
    return categories_list


async def db_get_elimination_time() -> list:
    """

    :return:
    """
    query_kwargs: dict = {
        "action": 'SELECT', "subject": 'title',
    }
    query: str = await QueryConstructor(None, 'core_eliminationtime', **query_kwargs).prepare_data()
    elimination_time: list = await db_get_data_list(query=query)
    clean_elimination_time: list = [item[0] for item in elimination_time]

    return clean_elimination_time


async def db_del_violations(violation: dict) -> bool:
    """Удаление данных violation из Database

    :param violation dict данные записи для удаления
    :return: bool
    """

    file_id: str = violation.get('file_id', '')
    result: bool = await DataBaseViolations().delete_single_violation(file_id=file_id)
    return bool(result)


async def db_del_item_from_table(*, table_name: str, table_column_name: str, file_id: str | int) -> bool:
    """Удаление данных violation из Database

    :param table_name: имя таблицы
    :param table_column_name: имя столбца в таблице
    :param file_id: id записи
    :return: list
    """

    result = await DataBaseViolations().delete_item_from_table(
        table_name=table_name,
        column_name=table_column_name,
        file_id=file_id
    )
    return bool(result)


async def db_get_all_tables_names() -> list:
    """Получение всех имен таблиц в БД

    :return:
    """
    result = await DataBaseViolations().get_all_tables_names()
    clean_result: list = [item[0] for item in result]
    return clean_result


async def db_get_data_list(query: str) -> list:
    """Получение list с данными по запросу query

    :return: list
    """
    try:
        datas_query: list = await DataBaseViolations().get_data_list(query=query)

    except OperationalError as err:
        logger.error(f'{repr(err)} {query = }')
        return []

    return datas_query


async def db_get_single_violation(file_id: str) -> list:
    """Получение данных нарушения по file_id из core_violations

    :return: list
    """

    violation_list: list = await DataBaseViolations().get_single_violation(file_id=file_id)
    return violation_list


async def db_get_clean_headers(table_name: str) -> list:
    """Получение заголовков таблицы по имени table_name

    :param table_name: str - имя таблицы для получения заголовков
    :return: list[str] or []
    """

    if not table_name:
        return []

    clean_headers: list = [item[1] for item in await db_get_table_headers(table_name=table_name)]
    return clean_headers


async def db_get_table_headers(table_name: str = None) -> list:
    """Получение заголовков таблицы

    :return:
    """

    table_headers: list = await DataBaseViolations().get_table_headers(table_name)
    return table_headers


async def db_get_id_violation(file_id) -> int:
    """Получение id записи

    :return: int
    """

    vi_id: int = await DataBaseViolations().get_id_violation(file_id=file_id)
    return vi_id


async def db_get_id(table: str, entry: str, file_id: str = None, calling_function_name: str = None) -> int:
    """Получение id записи по значению title из соответствующий таблицы table

    :param file_id: str id  файла формата dd.mm.gggg___user_id___msg_id (26.09.2022___373084462___24809)
    :param entry: str - информация для записи в БД
    :param table: str - имя таблицы
    :param calling_function_name: - имя вызвавшей функции (для отладки)
    :return: int - id из БД
    """
    try:
        value: int = await DataBaseViolations().get_id(
            table_name=table, entry=entry, file_id=file_id, calling_function_name=calling_function_name
        )
        return value

    except OperationalError as err:
        logger.error(f'{repr(err)} {table = }, {entry = }, {file_id = }, {calling_function_name = }')
        return 0


async def db_update_hse_user_language(*, value: str, hse_id: str) -> bool:
    """

    :return:
    """

    result: bool = await DataBaseViolations().update_hse_user_language(
        value=str(value), hse_id=str(hse_id)
    )
    return bool(result)


async def db_update_column_value_for_query(*, table_name: str, hse_telegram_id: str, table_column_name: str,
                                           item_value: str | int) -> bool:
    """Обновление значений item_value в столбце table_column_name строки item_number таблицы table_name

    :param hse_telegram_id:
    :param table_name: str  - имя таблицы для изменений
    :param table_column_name: str  - имя столбца таблицы table_name для изменений
    :param item_value: str  - значение для внесения изменений

    :return: bool true если удачно or false если не удачно
    """
    # TODO заменить на вызов конструктора QueryConstructor
    query: str = f"UPDATE {table_name} SET `{table_column_name}` = {bool(item_value)} WHERE `hse_telegram_id` = {hse_telegram_id}"

    result: bool = await DataBaseViolations().update_column_value_for_query(query=query)
    return bool(result)


async def db_update_column_value(column_name: str, value: None | int | str, violation_id: int | str) -> bool:
    """

    :return:
    """

    result: bool = await DataBaseViolations().update_violation_column_value(
        column_name=column_name,
        value=value,
        row_id=str(violation_id)
    )
    return bool(result)


async def db_update_table_column_value(*, table_name: str, table_column_name_for_update: str, table_column_name: str,
                                       item_value: str, item_name: str) -> bool:
    """
    :param item_name:
    :param table_column_name_for_update:
    :param table_name: str  - имя таблицы для изменений
    :param table_column_name: str  - имя столбца таблицы table_name для изменений
    :param item_value: str  - значение для внесения изменений

    :return: bool true если удачно or false если не удачно
    """
    # TODO заменить на вызов конструктора QueryConstructor
    query: str = f"UPDATE {table_name} SET {table_column_name_for_update} = ? WHERE {table_column_name} = ?"
    logger.debug(f'{table_name = } {table_column_name = } {item_name = } {item_value = }')

    result: bool = await DataBaseViolations().update_table_column_value(
        query=query,
        item_name=item_name,
        item_value=str(item_value)
    )
    return bool(result)


async def db_get_full_title(table_name: str, short_title: str) -> str:
    """

    :return:
    """
    full_title: str = await  DataBaseViolations().get_full_title(table_name=table_name, short_title=short_title)
    return full_title


async def db_get_max_number() -> int:
    """Получение номера акта из Database `core_reestreacts`

    :return: int act_num: номер акта - предписания
    """
    act_num: int = await DataBaseViolations().get_max_number()
    return act_num


async def db_set_act_value(act_data_dict: DataFrame, act_number: int, act_date: str) -> bool:
    """

    :return:
    """
    act_is_created: bool = await DataBaseViolations().set_act_value(
        act_data_dict=act_data_dict, act_number=act_number, act_date=act_date
    )
    return bool(act_is_created)


async def db_get_username(user_id: int) -> str:
    """Получение username из core_hseuser по user_id

    :return:
    """
    if not user_id:
        logger.error('ERROR: No user_id for db_get_username')

    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "hse_telegram_id": user_id,
        },
    }
    query: str = await QueryConstructor(None, 'core_hseuser', **query_kwargs).prepare_data()
    datas_query: list = await DataBaseViolations().get_data_list(query=query)
    username = datas_query[0][4]

    return username


async def db_get_dict_userdata(user_id: int) -> dict:
    """Получение userdata из core_hseuser по user_id

    :return: dict
    """
    if not user_id:
        logger.error('ERROR: No user_id foe db_get_username ')
        return {}

    clean_headers: list = await db_get_clean_headers(table_name='core_hseuser')

    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "hse_telegram_id": user_id,
        },
    }
    query: str = await QueryConstructor(None, 'core_hseuser', **query_kwargs).prepare_data()

    datas_query: list = await DataBaseViolations().get_data_list(query=query)
    try:
        clean_values: list = datas_query[0]

    except IndexError:
        return {}

    return dict((header, item_value) for header, item_value in zip(clean_headers, clean_values))


async def db_get_period_for_current_week(current_week: str, current_year: str = None) -> list:
    """Получение данных из core_week по week_number

    :return:
    """
    if not current_week:
        logger.error('ERROR: No user_id foe db_get_username ')

    if not current_year:
        current_year = await get_year_message(current_date=datetime.now())

    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "week_number": current_week,
        },
    }
    query: str = await QueryConstructor(None, 'core_week', **query_kwargs).prepare_data()

    logger.debug(f'{__name__} {await fanc_name()} {query}')

    datas_query: list = await DataBaseViolations().get_data_list(query=query)
    period_data = datas_query[0]

    table_headers: list = await DataBaseViolations().get_table_headers(table_name='core_week')
    headers = [row[1] for row in table_headers]
    period_dict = dict(zip(headers, period_data))
    return [
        period_dict.get(f'start_{current_year}', None),
        period_dict.get(f'end_{current_year}', None)
    ]


async def db_get_period_for_current_month(current_month: str = None, current_year: str = None) -> list:
    """Получение данных из core_week по week_number

    :return:
    """

    if not current_month:
        current_month = await get_month_message(current_date=datetime.now())

    if not current_year:
        current_year = await get_year_message(current_date=datetime.now())

    last_day_month = await last_day_of_month(current_date=datetime.now())
    last_day_month = last_day_month.strftime("%d.%m.%Y")

    period = [
        f'01.{current_month}.{current_year}',
        f'{last_day_month}',
    ]
    return period


async def last_day_of_month(current_date: datetime):
    if current_date.month == 12:
        return current_date.replace(day=31)
    return current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)


async def get_week_message(current_date: datetime | str = None) -> str:
    """Обработчик сообщений с фото
    Получение номер str недели из сообщения в формате dd
    """
    current_date: date = await str_to_datetime(current_date)

    if not current_date:
        current_date: datetime = datetime.now()
    week = current_date.isocalendar()[1]
    return str("0" + str(week) if week < 10 else str(week))


async def get_month_message(current_date: datetime = None) -> str:
    """Получение номер str месяца из сообщения в формате mm
    """
    current_date: date = await str_to_datetime(current_date)

    if not current_date:
        current_date: datetime = datetime.now()
    return str("0" + str(current_date.month) if int(current_date.month) < 10 else str(current_date.month))


async def get_year_message(current_date: datetime = None) -> str:
    """Обработчик сообщений с фото
    Получение полного пути файла
    """
    current_date: date = await str_to_datetime(current_date)

    if not current_date:
        current_date: datetime = datetime.now()

    return str(current_date.year)


async def str_to_datetime(date_str: str | datetime) -> date:
    """Преобразование str даты в datetime

    :param
    """

    current_date: date = None
    try:
        if isinstance(date_str, str):
            current_date: date = datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError as err:
        logger.error(f"{repr(err)}")

    return current_date


async def get_check_param(local_file: str, calling_function: str, **kvargs) -> bool:
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


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])


async def test():
    res: list = await db_get_all_tables_names()
    for item in res:
        logger.info(f'{item}')

    now = datetime.now()
    current_week: str = await get_week_message(current_date=now)
    # current_month: str = await get_month_message(current_date=now)
    current_year: str = await get_year_message(current_date=now)

    stat_date_period: list = await db_get_period_for_current_week(current_week, current_year)
    print(f"{stat_date_period = }")

    user_id: int = 373084462
    res: dict = await db_get_dict_userdata(user_id=user_id)
    print(f"{res = }")

    res: str = await db_get_username(user_id=user_id)
    print(f"{res = }")

    res: list = await db_get_elimination_time()
    print(f"{res = }")

    res: list = await db_get_categories_list()
    print(f"{res = }")

    res: list = await db_get_categories()
    print(f"{res = }")


async def test_2():
    table_name = 'core_violations'
    post_id = 10211

    result = await db_get_data_dict_from_table_with_id(table_name, post_id)
    print(f'{result = }')


if __name__ == '__main__':
    # asyncio.run(test())
    asyncio.run(test_2())
