from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from config.config import Novolex_media_path
from loader import logger


async def get_image_name(*args) -> str:
    """

    :param args:
    :return:
    """
    return str(Path(*args))


async def get_report_full_name(*args):
    """

    :param args:
    :return:
    """
    return str(Path(*args))


async def text_get_file_path(*args) -> str:
    """

    :param args:
    :return:
    """
    return str(Path(*args))


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


async def get_photo_full_name(chat_id, image_name):
    return await get_image_name(Novolex_media_path, "HSE", str(chat_id), f"{image_name}.jpg")


async def get_report_full_filepath(user_id: str = None, actual_date: str = None):
    """Обработчик сообщений с reports
    Получение полного пути файла

    :param actual_date:
    :param user_id: id пользователя
    """
    if not actual_date:
        actual_date = await date_now()

    return str(Path(Novolex_media_path, "HSE", str(user_id), 'data_file', actual_date, 'reports'))


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
        act_number = (datetime.now()).strftime("%d.%m.%Y")

    act_date = param.get('act_date', None)
    if not act_date:
        act_date = (datetime.now()).strftime("%d.%m.%Y")

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


async def get_dop_photo_full_filename(user_id: str = None, name=None, date=None):
    """Получение полного пути с расширением дополнительных фото материалов"""
    if not date:
        date = await date_now()
    return str(
        Path(Novolex_media_path, "HSE", str(user_id), 'data_file', date, 'photo', f"dop_report_data___{name}.jpg"))


async def date_now() -> str:
    """Возвращает текущую дату в формате дд.мм.гггг
    :return:
    """
    return str((datetime.now()).strftime("%d.%m.%Y"))
