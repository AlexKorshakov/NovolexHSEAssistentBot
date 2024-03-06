from __future__ import annotations

import os
from pathlib import Path

from loader import logger


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
