import asyncio
from datetime import datetime
import os
import traceback
from pathlib import Path
from pprint import pprint
from sqlite3 import OperationalError

from apps.core.bot.handlers.group.group_violations_data_base import GroupDataBase
from loader import logger


async def write_data_in_database(*, violation_data_to_db: dict, table_name: str = None) -> bool:
    """Поиск записи по file_id в database

    :param table_name:
    :param violation_data_to_db:
    :return: True or False
    """
    table_name = table_name if table_name else 'violations'

    if not violation_data_to_db.get('file_id'):
        logger.error(f"Error get file_id for violation_data: {violation_data_to_db}")
        return False

    try:
        if not await db_check_violation_exists(file_id=violation_data_to_db.get('file_id'), table_name=table_name):
            violation_data_to_db: dict = await normalize_type_data(violation_data_to_db)
            result, violation_data_to_db = await prepare_violation_data(violation_data_to_db)
            if not result:
                logger.error(f"Error not result {violation_data_to_db = }")
                return False

            violation_data_to_db: dict = await normalize_violation_data(violation_data_to_db, table_name=table_name)

            violation_data_to_db: dict = await check_violation_data(violation_data_to_db, table_name=table_name)

            if not violation_data_to_db:
                return False

            if await db_add_violation(violation_data=violation_data_to_db, table_name=table_name):
                return True
        else:
            logger.error(f"file_id {violation_data_to_db.get('file_id')} in DB!!")

    except OperationalError as err:
        logger.error(f"Error add_violation in DataBase() : {repr(err)}")
        return False

    except TypeError as err:
        logger.error(f"Error add_violation in DataBase() : {repr(err)}")
        return False

    return False


async def check_violation_data(violation_data: dict, table_name: str) -> dict:
    """

    :return:
    """
    if not violation_data: return {}
    if not table_name: return {}

    not_null_values_headers: list = [row[1] for row in await db_get_table_headers(table_name) if row[3] != 0]

    for key, value in violation_data.items():
        if key not in not_null_values_headers:
            continue

        if violation_data.get(key) is None:
            logger.info(f'{key = } {value = } from violation_data')

    return violation_data


async def normalize_violation_data(violation_data: dict, table_name: str) -> dict:
    """

    :return:
    """
    if not violation_data: return {}
    if not table_name: return {}

    clean_headers: list = await db_get_clean_headers(table_name=table_name)
    keys_to_remove = [item for item in list(violation_data.keys()) if item not in clean_headers]

    for key in keys_to_remove:

        try:
            del violation_data[key]
            logger.info(f'{key = } remove from violation_data')

        except (KeyError, RuntimeError) as err:
            logger.error(f'{key = } err remove from violation_data err {repr(err)}')
            continue

        except Exception as err:
            logger.error(f'{key = } Exception remove from violation_data err {repr(err)}')
            continue

    return violation_data


async def normalize_type_data(violation_data: dict):
    violation_type = {k: str(v) for k, v in violation_data.items()}
    return violation_type


async def prepare_violation_data(violation_dict: dict) -> (bool, dict):
    """Подготовка данных перед записью в БД

    :param violation_dict: 
    :return: 
    """
    this_fanc_name: str = await fanc_name()

    chat_id = violation_dict.get("chat_id", None)
    violation_dict.update({'chat_id': chat_id})

    chat_name = violation_dict.get("chat_name", None)
    violation_dict.update({'chat_name': chat_name})

    start_text_mes_id = violation_dict.get("start_text_mes_id", None)
    violation_dict.update({'start_text_mes_id': start_text_mes_id})

    text = violation_dict.get("text", None)
    violation_dict.update({'text': text})

    description = violation_dict.get("description", None)
    violation_dict.update({'description': description})

    user_id = violation_dict.get('user_id', None)
    violation_dict.update({'user_id': user_id})

    violation_id = violation_dict.get('violation_id', None)
    violation_dict.update({'violation_id': violation_id})

    file_id = violation_dict.get('file_id', None)
    if not file_id:
        logger.error('not found file_id!!!')
        return False, violation_dict

    violation_dict.update({'file_id': file_id})

    media_group: list = violation_dict.get("media_group", [])
    media_group: list = media_group if (isinstance(media_group, list) and media_group) else []

    media_str_list = [[v for k, v in item.items()] for item in media_group if isinstance(item, dict)]
    media_str_for_join: list = list(set(item[0] for item in media_str_list))
    media_str: str = ':::'.join(media_str_for_join)

    violation_dict.update({'media_str': media_str})

    json_file_path = violation_dict.get('json_file_path', None)
    violation_dict.update({'json_file_path': json_file_path})

    json_full_name = violation_dict.get('json_full_name', None)
    violation_dict.update({'json_full_name': json_full_name})

    photo_file_path = violation_dict.get('photo_file_path', '')
    violation_dict.update({'photo_file_path': photo_file_path})

    photo_full_name = violation_dict.get('photo_full_name', '')
    violation_dict.update({'photo_full_name': photo_full_name})

    created_at = violation_dict.get('created_at', await date_now())
    violation_dict.update({'created_at': created_at})

    updated_at = created_at
    violation_dict.update({'updated_at': updated_at})

    update_information: str = f'update by {user_id} at {created_at} ' \
                              f'for first entry in current registry'
    violation_dict.update({'update_information': update_information})

    return True, violation_dict


async def qr_get_file_path(*args) -> str:
    """

    :param args:
    :return:
    """
    return str(Path(*args))


async def get_files(folder_path: str) -> list:
    """

    :param folder_path:
    :return:
    """
    if not folder_path:
        return []

    for _, _, files in os.walk(folder_path):
        return files


async def date_now() -> str:
    """Возвращает текущую дату в формате дд.мм.гггг
    :return:
    """
    return str((datetime.now()).strftime("%d.%m.%Y"))


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])


async def db_add_violation(violation_data: dict, table_name: str) -> bool:
    """Добавление записи в БД

    :param table_name:
    :param violation_data: dict - dict с данными для записи в БД
    :return: bool violation_exists
    """

    if not violation_data: return False
    if not table_name: return False

    is_added: bool = await GroupDataBase().add_data(
        table_name=table_name, data_dict=violation_data
    )
    return bool(is_added)


async def db_check_violation_exists(file_id: str, table_name: str) -> bool:
    """Проверка наличия записи в БД

    :param table_name:
    :param file_id: int - id записи
    :return: bool is_exists
    """
    is_exists: bool = await GroupDataBase().violation_exists(file_id=file_id, table_name=table_name)
    return bool(is_exists)


async def db_get_table_headers(table_name: str = None) -> list:
    """Получение заголовков таблицы

    :return:
    """

    table_headers: list = await GroupDataBase().get_table_headers(table_name)
    return table_headers


async def db_get_id(table: str, entry: str, file_id: str = None, calling_function_name: str = None) -> int:
    """Получение id записи по значению title из соответствующий таблицы table

    :param file_id: str id  файла формата dd.mm.gggg___user_id___msg_id (26.09.2022___373084462___24809)
    :param entry: str - информация для записи в БД
    :param table: str - имя таблицы
    :param calling_function_name: - имя вызвавшей функции (для отладки)
    :return: int - id из БД
    """
    try:
        value: int = await GroupDataBase().get_id(
            table_name=table, entry=entry, file_id=file_id, calling_function_name=calling_function_name
        )
        return value

    except OperationalError as err:
        logger.error(f'{repr(err)} {table = }, {entry = }, {file_id = }, {calling_function_name = }')
        return 0


async def db_get_clean_headers(table_name: str) -> list:
    """Получение заголовков таблицы по имени table_name

    :param table_name: str - имя таблицы для получения заголовков
    :return: list[str] or []
    """

    if not table_name:
        return []

    clean_headers: list = [item[1] for item in await db_get_table_headers(table_name=table_name)]
    return clean_headers


async def test_2():
    media_group = [
        {
            "media": "22.11.2023___373084462___6450___6476"
        },
        {
            "media": "22.11.2023___373084462___6450___6477"
        },
        {
            "media": "22.11.2023___373084462___6450___6476"
        },
        {
            "media": "22.11.2023___373084462___6450___6477"
        },
    ]

    media_group = media_group if (isinstance(media_group, list) and media_group) else []

    media_str_list = [[v for k, v in item.items()] for item in media_group if isinstance(item, dict)]
    media_str_for_join = list(set(item[0] for item in media_str_list))
    media_str: str = ':::'.join(media_str_for_join)
    pprint(media_str)


async def test_3():
    category_id = await db_get_id(
        table='core_category',
        entry='СИЗ',
        file_id='10.01.2024___373084462___9229',
        calling_function_name=f'{await fanc_name()}: category'
    )
    pprint(category_id)


async def test_4():
    violation_data_to_db = {
        "chat_id": -1002132341489,
        "chat_name": "Багратион-2 Контроль ГМЗ+ОФ",
        "file_id": 11362,
        "json_file_path": "C:\\Users\\KDeusEx\\PycharmProjects\\!media\\BAGRATION\\group\\Багратион-2 Контроль ГМЗ+ОФ"
                          "\\26.02.2024\\json",
        "json_full_name": "C:\\Users\\KDeusEx\\PycharmProjects\\!media\\BAGRATION\\group\\Багратион-2 Контроль ГМЗ+ОФ\\"
                          "26.02.2024\\json\\group_report_data___-1002132341489___26.02.2024___373084462___11362.json",
        "media_group": [],
        "photo": "",
        "start_text_mes_id": 11362,
        "text": "#нарушение тестовое сообщение",
        "user_id": 373084462,
        "violation_id": 11362
    }

    result, violation_data_to_db = await prepare_violation_data(violation_data_to_db)

    pprint(result)
    pprint(violation_data_to_db)


if __name__ == "__main__":
    # asyncio.run(test_2())
    # asyncio.run(test_3())
    asyncio.run(test_4())
