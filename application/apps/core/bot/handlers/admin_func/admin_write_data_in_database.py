from __future__ import annotations

import traceback
from datetime import date, datetime
from sqlite3 import OperationalError

from loader import logger
from apps.core.database.db_utils import (db_add_new_user,
                                         db_get_clean_headers,
                                         db_get_table_headers)


async def write_new_user_data_in_database(*, user_data_to_db: dict, admin_id: int | str) -> bool:
    """Добавление, проверка и запись данных нового пользователя user_data_to_db в таблицу `core_hseuser` базы данных

    :param user_data_to_db: dict - dict с данными для записи
    :param admin_id: int - id записи пользователя в`core_hseuser`
    :return: bool True if successfully else False
    """
    if not user_data_to_db.get('user_telegram_id'):
        logger.error(f"Error in () {await fanc_name()} user_data_to_db: {user_data_to_db = }")
        return False

    result, user_data_to_db = await prepare_violation_data(user_data_dict=user_data_to_db, admin_id=admin_id)
    if not result:
        logger.error(f"Error in {await fanc_name()} user_data_to_db: {result = }")
        return False

    user_data_to_db: dict = await normalize_violation_data(user_data_to_db)
    user_data_to_db: dict = await check_violation_data(user_data_to_db)

    try:
        if not await db_add_new_user(hseuser_data=user_data_to_db):
            logger.error(f"Error in {await fanc_name()} db_add_user by {admin_id} "
                         f"user_telegram_id = {user_data_to_db.get('hse_telegram_id')} in DB!!")
            return False

        return True

    except OperationalError as err:
        logger.error(f"Error in {await fanc_name()}  add_violation in DataBase() : {repr(err)}")
        return False

    except Exception as err:
        logger.error(f"Error in {await fanc_name()}  add_violation in DataBase() : {repr(err)}")
        return False


async def normalize_violation_data(user_data: dict = None) -> dict:
    """Нормализация данных и удаление полей dict не содержащихся в Базе данных

    :param user_data: dict - dict с данными
    :return: user_data: dict - dict с данными
    """
    clean_headers: list = await db_get_clean_headers(table_name='core_hseuser')
    keys_to_remove: list = [item for item in list(user_data.keys()) if item not in clean_headers]

    for key in keys_to_remove:
        try:
            del user_data[key]
            logger.info(f'{key = } remove from user_data')

        except (KeyError, RuntimeError) as err:
            logger.error(f'Error in {await fanc_name()} {key = } err remove from user_data err {repr(err)}')
            continue

        except Exception as err:
            logger.error(f'Error in {await fanc_name()} {key = } Exception remove from user_data err {repr(err)}')
            continue

    return user_data


async def check_violation_data(user_data: dict = None) -> dict:
    """Проверка user_data на наличие обязательных для заполнения данных (полей Базы данных)

    :param user_data: dict - dict с данными
    :return: user_data_dict: dict - dict с данными
    """
    not_null_values_headers: list = [row[1] for row in await db_get_table_headers('core_hseuser') if row[3] != 0]

    for key, value in user_data.items():
        if key not in not_null_values_headers:
            continue

        if user_data.get(key) is None:
            logger.info(f'{key = } {value = } from user_data')

    return user_data


async def prepare_violation_data(user_data_dict: dict, admin_id: int | str = None) -> (bool, dict):
    """Подготовка и преобразование данных user_data_dict нового пользователя перед записью в базу

    :param user_data_dict: dict - dict с данными
    :param admin_id: int | str - id  пользователя, заносящего запись
    :return: (bool, dict) - (результат преобразования данных, dict с данными)
    """
    user_telegram_id: int | str = user_data_dict.get('user_telegram_id', None)

    if not user_telegram_id:
        logger.error(f'Error in {await fanc_name()} not found user_telegram_id!!!')
        return False, user_data_dict

    user_data_dict.update({'user_telegram_id': user_data_dict})

    title: str = user_data_dict.get('title', None)
    user_data_dict.update({'title': title})

    hse_telegram_id: str = user_data_dict.get('hse_telegram_id', None)
    user_data_dict.update({'hse_telegram_id': hse_telegram_id})

    hse_tab_number: str = user_data_dict.get('hse_tab_number', None)
    user_data_dict.update({'hse_tab_number': hse_tab_number})

    hse_full_name: str = user_data_dict.get('hse_full_name', None)
    user_data_dict.update({'hse_full_name': hse_full_name})

    hse_full_name_dative: str = user_data_dict.get('hse_full_name_dative', None)
    user_data_dict.update({'hse_full_name_dative': hse_full_name_dative})

    hse_short_name: str = user_data_dict.get('hse_short_name', None)
    user_data_dict.update({'hse_short_name': hse_short_name})

    hse_full_name_telegram: str = user_data_dict.get('hse_full_name_telegram', None)
    user_data_dict.update({'hse_full_name_telegram': hse_full_name_telegram})

    hse_function: str = user_data_dict.get('hse_function', None)
    user_data_dict.update({'hse_function': hse_function})

    hse_function_dative: str = user_data_dict.get('hse_function_dative', None)
    user_data_dict.update({'hse_function_dative': hse_function_dative})

    hse_department: str = user_data_dict.get('hse_department', None)
    user_data_dict.update({'hse_department': hse_department})

    hse_department_dative: str = user_data_dict.get('hse_department_dative', None)
    user_data_dict.update({'hse_department_dative': hse_department_dative})

    hse_language_code: str = user_data_dict.get('hse_language_code', None)
    user_data_dict.update({'hse_language_code': hse_language_code})

    hse_is_work: str = user_data_dict.get('hse_is_work', None)
    user_data_dict.update({'hse_is_work': hse_is_work})

    hse_status: str = user_data_dict.get('hse_status', None)
    user_data_dict.update({'hse_status': hse_status})

    hse_status_comment: str = user_data_dict.get('hse_status_comment', None)
    user_data_dict.update({'hse_status_comment': hse_status_comment})

    hse_organization: str = user_data_dict.get('hse_organization', None)
    user_data_dict.update({'hse_organization': hse_organization})

    hse_role_is_author: str = user_data_dict.get('hse_role_is_author', None)
    user_data_dict.update({'hse_role_is_author': hse_role_is_author})

    hse_role_is_developer: str = user_data_dict.get('hse_role_is_developer', None)
    user_data_dict.update({'hse_role_is_developer': hse_role_is_developer})

    hse_role_is_admin: str = user_data_dict.get('hse_role_is_admin', None)
    user_data_dict.update({'hse_role_is_admin': hse_role_is_admin})

    hse_role_is_coordinating_person: str = user_data_dict.get('hse_role_is_coordinating_person', None)
    user_data_dict.update({'hse_role_is_coordinating_person': hse_role_is_coordinating_person})

    hse_role_is_super_user: str = user_data_dict.get('hse_role_is_super_user', None)
    user_data_dict.update({'hse_role_is_super_user': hse_role_is_super_user})

    hse_role_is_user: str = user_data_dict.get('hse_role_is_user', None)
    user_data_dict.update({'hse_role_is_user': hse_role_is_user})

    hse_role_is_subcontractor: str = user_data_dict.get('hse_role_is_subcontractor', None)
    user_data_dict.update({'hse_role_is_subcontractor': hse_role_is_subcontractor})

    hse_role_receive_notifications: str = user_data_dict.get('hse_role_receive_notifications', None)
    user_data_dict.update({'hse_role_receive_notifications': hse_role_receive_notifications})

    hse_role_is_user_bagration: str = user_data_dict.get('hse_role_is_user_bagration', None)
    user_data_dict.update({'hse_role_is_user_bagration': hse_role_is_user_bagration})

    hse_role_is_emploee_tc: str = user_data_dict.get('hse_role_is_emploee_tc', None)
    user_data_dict.update({'hse_role_is_emploee_tc': hse_role_is_emploee_tc})

    hse_location: str = user_data_dict.get('hse_location', None)
    user_data_dict.update({'hse_location': hse_location})

    hse_work_shift: str = user_data_dict.get('hse_work_shift', None)
    user_data_dict.update({'hse_work_shift': hse_work_shift})

    hse_contact_main_phone_number: str = user_data_dict.get('hse_contact_main_phone_number', None)
    user_data_dict.update({'hse_contact_main_phone_number': hse_contact_main_phone_number})

    hse_contact_second_phone_number: str = user_data_dict.get('hse_contact_second_phone_number', None)
    user_data_dict.update({'hse_contact_second_phone_number': hse_contact_second_phone_number})

    hse_contact_main_email: str = user_data_dict.get('hse_contact_main_email', None)
    user_data_dict.update({'hse_contact_main_email': hse_contact_main_email})

    hse_contact_second_email: str = user_data_dict.get('hse_contact_second_email', None)
    user_data_dict.update({'hse_contact_second_email': hse_contact_second_email})

    hse_folder_parent_id: str = user_data_dict.get('hse_folder_parent_id', None)
    user_data_dict.update({'hse_folder_parent_id': hse_folder_parent_id})

    hse_folder_json_id: str = user_data_dict.get('hse_folder_json_id', None)
    user_data_dict.update({'hse_folder_json_id': hse_folder_json_id})

    hse_folder_report_id: str = user_data_dict.get('hse_folder_report_id', None)
    user_data_dict.update({'hse_folder_report_id': hse_folder_report_id})

    hse_folder_photo_id = user_data_dict.get('hse_folder_photo_id', None)
    user_data_dict.update({'hse_folder_photo_id': hse_folder_photo_id})

    day: str = await get_day_message()
    month: str = await get_month_message()
    year: str = await get_year_message()
    created_at: str = '.'.join([day, month, year])
    user_data_dict.update({'created_at': created_at})

    updated_at: str = created_at
    user_data_dict.update({'updated_at': updated_at})

    update_information: str = f'update by {admin_id = } hse_telegram_id {hse_telegram_id} at {created_at} ' \
                              f'for first entry in current registry'

    user_data_dict.update({'update_information': update_information})

    return True, user_data_dict


async def str_to_datetime(date_str: str) -> date:
    """Преобразование str даты в datetime
    """
    current_date: datetime = datetime.now()
    try:
        if isinstance(date_str, str):
            current_date: date = datetime.strptime(date_str, "%d.%m.%Y").date()

    except ValueError as err:
        logger.error(f"{repr(err)}")

    return current_date


async def get_day_message(current_date: datetime | str = None) -> str:
    """Обработчик сообщений с фото
    Получение номер str дня из сообщения в формате dd
    """
    current_date: date = await str_to_datetime(current_date)

    if not current_date:
        current_date: datetime = datetime.now()

    return str("0" + str(current_date.day) if current_date.day < 10 else str(current_date.day))


async def get_month_message(current_date: datetime | str = None) -> str:
    """Получение номер str месяца из сообщения в формате mm
    """
    current_date: date = await str_to_datetime(current_date)

    if not current_date:
        current_date: datetime = datetime.now()

    return str("0" + str(current_date.month) if int(current_date.month) < 10 else str(current_date.month))


async def get_year_message(current_date: datetime | str = None) -> str:
    """Обработчик сообщений с фото
    Получение полного пути файла
    """
    current_date: date = await str_to_datetime(current_date)

    if not current_date:
        current_date: datetime = datetime.now()

    return str(current_date.year)


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])
