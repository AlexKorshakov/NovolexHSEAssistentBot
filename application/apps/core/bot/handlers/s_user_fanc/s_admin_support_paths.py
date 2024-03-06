from __future__ import annotations
from pathlib import Path


def sa_check_path(file_path: str | Path) -> bool:
    """

    :param file_path:: str | Path - path to file
    :return: bool True if exists else - False
    """
    if not file_path:
        return False

    if Path(file_path).exists():
        return True
    return False


async def sa_check_or_create_dir(file_path: str | Path) -> bool:
    """

    :param file_path:: str | Path - path to file
    :return: bool True if exists else - False
    """
    if not Path(file_path).exists():
        Path(file_path).mkdir()
    return False


async def sa_get_file_path(*args) -> Path:
    """

    :param args:
    :return:
    """

    return Path(*args)


async def sa_get_iterdir(dir_path: str | Path) -> list:
    """

    :param dir_path:
    :return:
    """
    if not Path(dir_path).exists():
        return []

    return [Path(dir_path).iterdir()]
