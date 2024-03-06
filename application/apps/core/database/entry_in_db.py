import asyncio
import os
import traceback
from pathlib import Path
from pprint import pprint
from sqlite3 import OperationalError

from loader import logger
from apps.core.utils.json_worker.read_json_file import read_json_file
from apps.core.database.db_utils import (db_add_violation,
                                         db_check_violation_exists,
                                         db_get_table_headers,
                                         db_get_id,
                                         db_get_clean_headers)


async def write_data_in_database(*, violation_data_to_db: dict) -> bool:
    """Поиск записи по file_id в database

    :param violation_data_to_db:
    :return: True or False
    """
    if not violation_data_to_db.get('file_id'):
        logger.error(f"Error get file_id for violation_data: {violation_data_to_db}")
        return False

    try:
        if not await db_check_violation_exists(file_id=violation_data_to_db.get('file_id')):
            result, violation_data_to_db = await prepare_violation_data(violation_data_to_db)
            if not result:
                logger.error(f"Error not result {violation_data_to_db = }")
                return False

            violation_data_to_db: dict = await normalize_violation_data(violation_data_to_db)
            violation_data_to_db: dict = await check_violation_data(violation_data_to_db)

            if await db_add_violation(violation_data=violation_data_to_db):
                return True
        else:
            logger.error(f"file_id {violation_data_to_db.get('file_id')} in DB!!")

    except OperationalError as err:
        logger.error(f"Error add_violation in DataBase() : {repr(err)}")
        return False

    except Exception as err:
        logger.error(f"Error add_violation in DataBase() : {repr(err)}")
        return False

    return False


async def check_violation_data(violation_data: dict = None) -> dict:
    """

    :return:
    """
    not_null_values_headers: list = [row[1] for row in await db_get_table_headers('core_violations') if row[3] != 0]

    for key, value in violation_data.items():
        if key not in not_null_values_headers:
            continue

        if violation_data.get(key) is None:
            logger.info(f'{key = } {value = } from violation_data')

    return violation_data


async def normalize_violation_data(violation_data: dict = None) -> dict:
    """

    :return:
    """
    clean_headers: list = await db_get_clean_headers(table_name='core_violations')
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


async def prepare_violation_data(violation_dict: dict) -> (bool, dict):
    """Подготовка данных перед записью в БД
    
    :param violation_dict: 
    :return: 
    """

    this_fanc_name: str = await fanc_name()

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

    violation_dict.update({'media_group': media_str})

    location_id = await db_get_id(
        table='core_location',
        entry=violation_dict.get("location", None),
        file_id=file_id,
        calling_function_name=f'{this_fanc_name}: location'
    )
    violation_dict.update({'location_id': location_id})

    main_location_id = await db_get_id(
        table='core_mainlocation',
        entry=violation_dict.get("main_location", None),
        file_id=file_id,
        calling_function_name=f'{this_fanc_name}: main_location'
    )
    violation_dict.update({'main_location_id': main_location_id})

    sub_location_id = await db_get_id(
        table='core_sublocation',
        entry=violation_dict.get("sub_location", None),
        file_id=file_id,
        calling_function_name=f'{this_fanc_name}: sub_location'
    )
    violation_dict.update({'sub_location_id': sub_location_id})

    work_shift_id = await db_get_id(
        table='core_workshift',
        entry=violation_dict.get("work_shift", None),
        file_id=file_id,
        calling_function_name=f'{this_fanc_name}: work_shift'
    )
    violation_dict.update({'work_shift_id': work_shift_id})

    general_contractor_id = await db_get_id(
        table='core_generalcontractor',
        entry=violation_dict.get("general_contractor", None),
        file_id=file_id,
        calling_function_name=f'{this_fanc_name}: general_contractor'
    )
    violation_dict.update({'general_contractor_id': general_contractor_id})

    main_category_id = await db_get_id(
        table='core_maincategory',
        entry=violation_dict.get("main_category", None),
        file_id=file_id,
        calling_function_name=f'{this_fanc_name}: main_category'
    )
    violation_dict.update({'main_category_id': main_category_id})

    category_id = await db_get_id(
        table='core_category',
        entry=violation_dict.get("category", None),
        file_id=file_id,
        calling_function_name=f'{this_fanc_name}: category'
    )
    violation_dict.update({'category_id': category_id})

    normative_documents_id = await db_get_id(
        table='core_normativedocuments',
        entry=violation_dict.get("normative_documents", None),
        file_id=file_id,
        calling_function_name=f'{this_fanc_name}: normative_documents'
    )
    violation_dict.update({'normative_documents_id': normative_documents_id})

    act_required_id = await db_get_id(
        table='core_actrequired',
        entry=violation_dict.get("act_required", None),
        file_id=file_id,
        calling_function_name=f'{this_fanc_name}: act_required'
    )
    violation_dict.update({'act_required_id': act_required_id})

    elimination_time_id = await db_get_id(
        table='core_eliminationtime',
        entry=violation_dict.get("elimination_time", None),
        file_id=file_id,
        calling_function_name=f'{this_fanc_name}: elimination_time'
    )
    violation_dict.update({'elimination_time_id': elimination_time_id})

    incident_level_id = await db_get_id(
        table='core_incidentlevel',
        entry=violation_dict.get("incident_level", None),
        file_id=file_id,
        calling_function_name=f'{this_fanc_name}: incident_level'
    )
    violation_dict.update({'incident_level_id': incident_level_id})

    violation_category_id = await db_get_id(
        table='core_violationcategory',
        entry=violation_dict.get("violation_category", None),
        file_id=file_id,
        calling_function_name=f'{this_fanc_name}: violation_category'
    )
    violation_dict.update({'violation_category_id': violation_category_id})

    status_id = await db_get_id(
        table='core_status',
        entry=violation_dict.get("status", None),
        file_id=file_id,
        calling_function_name=f'{this_fanc_name}: status'
    )
    violation_dict.update({'status_id': status_id})

    finished_id = await db_get_id(
        table='core_finished',
        entry=violation_dict.get("finished", None),
        file_id=file_id,
        calling_function_name=f'{this_fanc_name}: finished'
    )
    violation_dict.update({'finished_id': finished_id})

    agreed_id = await db_get_id(
        table='core_agreed',
        entry=violation_dict.get("agreed", None),
        file_id=file_id,
        calling_function_name=f'{this_fanc_name}: agreed'
    )
    violation_dict.update({'agreed_id': agreed_id})

    hse_id = violation_dict.get("hse_id", None)
    violation_dict.update({'hse_id': hse_id})

    act_number = ''
    violation_dict.update({'act_number': act_number})

    if status_id == 1:
        finished_id = 1
        violation_dict.update({'finished_id': finished_id})

    description = violation_dict.get('description', None)
    violation_dict.update({'description': description})

    is_published = True
    violation_dict.update({'is_published': is_published})

    user_function = violation_dict.get("function", None)
    violation_dict.update({'function': user_function})

    name = violation_dict.get("name", None)
    violation_dict.update({'name': name})

    parent_id = violation_dict.get("parent_id", None)
    violation_dict.update({'parent_id': parent_id})

    violation_id = violation_dict.get('violation_id', None)
    violation_dict.update({'violation_id': violation_id})

    user_fullname = violation_dict.get('user_fullname', None)
    violation_dict.update({'user_fullname': user_fullname})

    report_folder_id = violation_dict.get('report_folder_id', None)
    violation_dict.update({'report_folder_id': report_folder_id})

    day = violation_dict.get('day', None)
    violation_dict.update({'day': day})

    month = violation_dict.get('month', None)
    violation_dict.update({'month': month})

    year = violation_dict.get('year', None)
    violation_dict.update({'year': year})

    week_id = violation_dict.get("week", None)
    violation_dict.update({'week_id': week_id})

    quarter = violation_dict.get("quarter", None)
    violation_dict.update({'quarter': quarter})

    day_of_year = violation_dict.get("day_of_year", None)
    violation_dict.update({'day_of_year': day_of_year})

    title = violation_dict.get('comment', None)
    violation_dict.update({'title': title})

    comment = violation_dict.get('comment', None)
    violation_dict.update({'comment': comment})

    coordinates = violation_dict.get('coordinates', None)
    violation_dict.update({'coordinates': coordinates})

    latitude = violation_dict.get('latitude', None)
    violation_dict.update({'latitude': latitude})

    longitude = violation_dict.get('longitude', None)
    violation_dict.update({'longitude': longitude})

    json_folder_id = violation_dict.get('json_folder_id', None)
    violation_dict.update({'json_folder_id': json_folder_id})

    json_file_path = violation_dict.get('json_file_path', None)
    violation_dict.update({'json_file_path': json_file_path})

    json_full_name = violation_dict.get('json_full_name', None)
    violation_dict.update({'json_full_name': json_full_name})

    user_id = violation_dict.get('user_id', None)
    violation_dict.update({'user_id': user_id})

    photo = f'/{user_id}/data_file/{file_id.split("___")[0]}/photo/report_data___{file_id}.jpg'
    violation_dict.update({'photo': photo})

    json = f'/{user_id}/data_file/{file_id.split("___")[0]}/json/report_data___{file_id}.json'
    violation_dict.update({'json': json})

    photo_file_path = violation_dict.get('photo_file_path', None)
    violation_dict.update({'photo_file_path': photo_file_path})

    photo_folder_id = violation_dict.get('photo_folder_id', None)
    violation_dict.update({'photo_folder_id': photo_folder_id})

    photo_full_name = violation_dict.get('photo_full_name', None)
    violation_dict.update({'photo_full_name': photo_full_name})

    created_at = violation_dict.get('file_id', None).split('___')[0].split('.')

    created_at = '.'.join(created_at[::-1])
    violation_dict.update({'created_at': created_at})

    updated_at = created_at
    violation_dict.update({'updated_at': updated_at})

    update_information: str = f'update by {user_id} hse_id _{hse_id}_ at {created_at} ' \
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


async def test_1():
    clean_headers: list = await db_get_clean_headers(table_name='core_violations')
    pprint(clean_headers)

    media_path: str = 'C:\\Users\\KDeusEx\\PycharmProjects\\!media\\373084462\\data_file\\07.10.2023\\json'
    matrix_folder_path: str = await qr_get_file_path(media_path)
    files: list = await get_files(str(matrix_folder_path))

    violations_data = []
    for file in files:
        data_dict = await read_json_file(f'{media_path}\\{file}')
        data_dict['general_contractor'] = 'ООО Ренейссанс Хэви Индастрис'

        violations_data.append(data_dict)

    for data_dict in violations_data:
        result: bool = await write_data_in_database(violation_data_to_db=data_dict)
        pprint(result)


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])


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


if __name__ == "__main__":
    # asyncio.run(test_1())
    # asyncio.run(test_2())
    asyncio.run(test_3())
