from pandas import DataFrame
import json

from loader import logger
from apps.MyBot import bot_send_message
from apps.core.bot.messages.messages import Messages
from apps.core.utils.generate_report.generator_report import create_dataframe_from_data
from apps.core.utils.goolgedrive_processor.GoogleDriveUtils.download_file_for_google_drive import \
    upload_files_from_google_drive

from apps.core.utils.secondary_functions.get_filepath import (create_file_path,
                                                              get_json_full_filepath,
                                                              get_photo_full_filepath,
                                                              get_report_full_filepath)


async def get_data_report(chat_id: int, file_list: list = None):
    """Подготовка путей сохранения путей файлов и скачивание файлов из google_drive

    :param file_list:
    :param chat_id:
    :return:
    """

    # await save_merged_file_on_pc(merge_file_list)
    if not file_list:
        logger.warning('error! file_list not found!')
        await bot_send_message(chat_id=chat_id, text=Messages.Error.file_list_not_found)

        photo_full_filepath: str = await get_photo_full_filepath(user_id=str(chat_id))
        json_full_filepath: str = await get_json_full_filepath(user_id=str(chat_id))
        report_full_filepath: str = await get_report_full_filepath(user_id=str(chat_id))

        await create_file_path(path=photo_full_filepath)
        await create_file_path(path=json_full_filepath)
        await create_file_path(path=report_full_filepath)

        await upload_files_from_google_drive(
            chat_id=chat_id, file_path=json_full_filepath, photo_path=photo_full_filepath)

    dataframe = await create_dataframe(file_list=file_list)

    return dataframe


async def create_dataframe(file_list: list) -> DataFrame:
    """Подготовка и создание dataframe для записи в отчет

    :param file_list: list с файлами для создания dataframe
    :return: dataframe
    """
    merge_file_list: list = await merge_json(file_list)

    headers: list = await create_headers()

    data_list: list = await read_json_files(files=merge_file_list, data=headers)

    dataframe: DataFrame = await create_dataframe_from_data(data=data_list)

    return dataframe


async def create_headers() -> list[dict]:
    """Подготовка заголовков таблицы отчета

    """
    data = [
        {
            "violation_id": "id записи",
            "main_category": "Основное направление",
            "category": "Категория нарушения",
            "violation_category": "Категория нарушений",
            "general_contractor": "Подрядная организация",
            "description": "Описание нарушения",
            "comment": "Комментарий",
            "incident_level": "Уровень происшествия",
            "elimination_time": "Дней на устранение",
            "act_required": "Оформление акта",
            "coordinates": "Координаты",
        }
    ]

    return data


async def read_json_files(files: list, data: list) -> list:
    """Получение данных множества jsons и запись данных в data

    :param files: список полных имён / путей к файлам
    :param data: входящий list
    :return: data
    """

    for item in files:
        data.append(await read_json_file(item))

    return data


async def merge_json(json_list) -> list:
    """Объединение json в один файл
    """
    merged_json = []
    for item in json_list:
        merged_json.append(item)

    return merged_json


async def read_json_file(file: str):
    """Получение данных из json.

    :param file: полный путь к файлу
    """
    try:
        with open(file, 'r', encoding='utf8') as data_file:
            data_loaded = json.load(data_file)
        return data_loaded
    except FileNotFoundError:
        return None
