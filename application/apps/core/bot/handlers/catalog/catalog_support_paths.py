from __future__ import annotations
from pathlib import Path


def catalog_check_path(file_path: str | Path) -> bool:
    """

    :param file_path:: str | Path - path to file
    :return: bool True if exists else - False
    """
    if Path(file_path).exists():
        return True
    return False


async def catalog_async_check_path(file_path: str | Path) -> bool:
    """

    :param file_path:: str | Path - path to file
    :return: bool True if exists else - False
    """
    if Path(file_path).exists():
        return True
    return False


async def catalog_check_or_create_dir(file_path: str | Path) -> bool:
    """

    :param file_path:: str | Path - path to file
    :return: bool True if exists else - False
    """
    if not Path(file_path).exists():
        Path(file_path).mkdir()
    return False


async def catalog_get_file_path(*args) -> str:
    """

    :param args:
    :return:
    """
    return str(Path(*args))
