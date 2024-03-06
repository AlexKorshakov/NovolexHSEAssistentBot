from __future__ import annotations
import io
import json

# from apps.core.utils.secondary_functions.get_filepath import BOT_MEDIA_PATH
from loader import logger

SUFFIX: str = ".json"


async def write_json_file(*, data: dict | str = None, name: str = None) -> bool:
    """Запись данных в json

    :param name: полный путь к файлу
    :param data: dict  с данными для записи
    """

    result: bool = await write_json(name=name, data=data)
    return result


async def write_user_registration_data_on_json_on_local_storage(*, user_data: dict = None) -> bool:
    """Запись данных в json
    """
    name: str = user_data['reg_json_full_name']

    result: bool = await write_json(name=name, data=user_data)
    return result


async def write_json_violation_user_file(*, data: dict = None, json_full_name: str = None) -> bool:
    """Запись данных о нарушениях в json

    :param json_full_name: полный путь для записи / сохранения файла включая расширение,
    :param data: данные для записи / сохранения
    :return: True or False
    """
    if not json_full_name:
        json_full_name = str(data.get("json_full_name"))

    if not json_full_name:
        logger.error(f'write_json_violation_user_file error write on {json_full_name}')
        return False

    if await write_json(name=json_full_name, data=data):
        logger.debug(f'Data write on {json_full_name}')
        return True
    return False


async def write_json(name: str, data) -> bool:
    """Запись данных в json

    :param name: полный путь для записи / сохранения файла включая расширение,
    :param data: данные для записи / сохранения
    :return: True or False
    """
    try:
        with io.open(name, 'w', encoding='utf8') as outfile:
            str_ = json.dumps(data,
                              indent=4,
                              sort_keys=True,
                              separators=(',', ': '),
                              ensure_ascii=False)
            outfile.write(str_)
            return True
    except TypeError as err:
        logger.error(f"TypeError: {repr(err)}")
        return False
