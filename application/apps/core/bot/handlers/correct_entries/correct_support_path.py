from __future__ import annotations

import asyncio
from datetime import date, datetime
import os
from pathlib import Path
from pprint import pprint

from apps.core.database.db_utils import (db_get_dict_userdata,
                                         db_get_data_dict_from_table_with_id)
from apps.core.utils.secondary_functions.get_part_date import get_year_message, get_month_message
from config.config import REPORT_NAME, Novolex_media_path
from loader import logger

REGISTRY_NAME = 'registry'

REGISTRY_NAME = 'registry'


async def get_report_full_name(*args):
    """

    :param args:
    :return:
    """
    return str(Path(*args))


async def get_full_act_prescription_path(chat_id, act_number, act_date, constractor_id) -> str:
    """Получение и создание полного пути акта предписания

    """

    contractor_data: dict = await get_general_constractor_data(
        constractor_id=constractor_id, type_constractor='general'
    )
    if not contractor_data:
        return ''

    param: dict = {
        'act_number': act_number,
        'act_date': act_date,
        'general_contractor': contractor_data.get('title'),
        'short_title': contractor_data.get('short_title'),
    }
    full_act_prescription_path: str = await get_and_create_full_act_prescription_name(chat_id=chat_id, param=param)

    return full_act_prescription_path


async def get_and_create_full_act_prescription_name(chat_id: int, param: dict) -> str:
    """Формирование и получение полного имение пути к акту

    :param param:
    :param chat_id:
    :return:
    """
    if not param:
        return ''

    act_number = param.get('act_number', None)
    if not act_number:
        act_number = (datetime.datetime.now()).strftime("%d.%m.%Y")

    act_date = param.get('act_date', None)
    if not act_date:
        act_date = (datetime.datetime.now()).strftime("%d.%m.%Y")

    short_title = param.get('short_title', None)
    if not short_title:
        short_title = ''

    main_location = param.get('main_location', None)
    if not main_location:
        main_location = ''

    try:
        report_full_name = f'Акт-предписание № {act_number} от {act_date} {short_title} {main_location}.xlsx'
        report_path = await get_report_full_filepath(str(chat_id), actual_date=act_date)

        await create_file_path(report_path)
        full_report_path: str = await get_report_full_name(report_path, report_full_name)

        return full_report_path

    except Exception as err:
        logger.error(f"get_report_path {repr(err)}")
        return ''


async def get_report_full_filepath(user_id: str = None, actual_date: str = None):
    """Обработчик сообщений с reports
    Получение полного пути файла

    :param actual_date:
    :param user_id: id пользователя
    """
    if not actual_date:
        actual_date = await date_now()

    return str(Path(Novolex_media_path, "HSE", str(user_id), 'data_file', actual_date, 'reports'))


async def get_and_create_full_act_prescription_name_in_registry(chat_id: int, param: dict) -> str:
    """Формирование и получение полного имение пути к акту  в реестре (хранилище)

    :param param:
    :param chat_id:
    :return:
    """
    if not param:
        return ''

    act_number = param.get('act_number', None)
    if not act_number:
        act_number = (datetime.datetime.now()).strftime("%d.%m.%Y")

    act_date = param.get('act_date', None)
    if not act_date:
        act_date = (datetime.datetime.now()).strftime("%d.%m.%Y")

    short_title = param.get('short_title', None)
    if not short_title:
        short_title = ''

    main_location = param.get('main_location', '')

    try:
        report_full_name = f'Акт-предписание № {act_number} от {act_date} {short_title}'
        report_path_in_registry = await get_report_full_filepath_in_registry(chat_id, actual_date=act_date)
        await create_file_path(report_path_in_registry)
        full_report_path_in_registry: str = await get_report_full_name(report_path_in_registry, report_full_name)
        await create_file_path(full_report_path_in_registry)

        return full_report_path_in_registry

    except Exception as err:
        logger.error(f"get_report_path {repr(err)}")
        return ''


async def get_general_constractor_data(constractor_id: int, type_constractor: str) -> dict:
    """Получение данных из таблицы `core_generalcontractor` по constractor_id

    :return:
    """
    contractor: dict = {}

    if type_constractor == 'general':
        contractor = await db_get_data_dict_from_table_with_id(
            table_name='core_generalcontractor',
            post_id=constractor_id)

    if type_constractor == 'sub':
        contractor = await db_get_data_dict_from_table_with_id(
            table_name='core_subcontractor',
            post_id=constractor_id)

    if not contractor:
        return {}

    return contractor


async def get_report_full_filepath_in_registry(hse_user_id: int = None, actual_date: str = None):
    """Обработчик сообщений с reports
    Получение полного пути файла

    :param actual_date:
    :param hse_user_id: int id пользователя
    """
    if not actual_date:
        actual_date = await date_now()

    year: str = await get_year_message(current_date=actual_date)
    month: str = await get_month_message(current_date=actual_date)

    if not hse_user_id:
        logger.error(f'hse_id is {hse_user_id}')
        return ''

    hse_user_dict: dict = await db_get_dict_userdata(hse_user_id)
    hse_organization_id: int = hse_user_dict.get('hse_organization', None)

    hse_organization_dict: dict = await db_get_data_dict_from_table_with_id(
        table_name='core_generalcontractor', post_id=hse_organization_id)
    hse_organization_name = hse_organization_dict.get('title', '')

    return str(Path(Novolex_media_path, "HSE", REGISTRY_NAME, hse_organization_name, year, month))


async def create_file_path(path: str):
    """Проверка и создание директории если не существует

    :param path: полный путь к директории,
    :return:
    """
    if not os.path.isdir(path):
        logger.debug(f"user_path: {path} is directory")
        try:
            os.makedirs(path)

        except Exception as err:
            logger.error(f"makedirs err {repr(err)}")


async def date_now() -> str:
    """Возвращает текущую дату в формате дд.мм.гггг
    :return:
    """
    return str((datetime.datetime.now()).strftime("%d.%m.%Y"))

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


async def str_to_datetime(date_str: str) -> date:
    """Преобразование str даты в datetime

    :param
    """

    current_date = None
    try:
        if isinstance(date_str, str):
            current_date: date = datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError as err:
        logger.error(f"{repr(err)}")

    return current_date