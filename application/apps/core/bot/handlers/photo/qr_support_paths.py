from __future__ import annotations

import os
from pathlib import Path


def qr_check_path(file_path: str | Path) -> bool:
    """

    :param file_path:: str | Path - path to file
    :return: bool True if exists else - False
    """
    if Path(file_path).exists():
        return True
    return False


async def qr_check_or_create_dir(file_path: str | Path) -> bool:
    """Проверка и создание пути file_path

    :param file_path:: str | Path - path to file
    :return: bool True if exists else - False
    """
    if not Path(file_path).exists():
        try:
            os.makedirs(file_path)

        except FileExistsError as err:
            return False
        # Path(file_path).makedirs()
    return True


async def qr_get_file_path(*args) -> str:
    """

    :param args:
    :return:
    """
    return str(Path(*args))
