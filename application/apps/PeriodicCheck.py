

"""Модуль содержащий класс(-ы) функций периодических проверок по времени"""
import asyncio
import sys

from apps.core.checker.periodic_check_unclosed_points_for_subcontractor import \
    periodic_check_unclosed_points_for_subcontractor
from apps.core.checker.periodic_check_work import periodic_check_work
from apps.core.checker.periodic_check_data_base import periodic_check_data_base
from apps.core.checker.periodic_check_unclosed_points import periodic_check_unclosed_points
from apps.core.checker.periodic_check_indefinite_normative import periodic_check_indefinite_normative
from loader import logger


class PeriodicCheck:
    """Основной класс запуска периодических проверок"""

    __instance = None

    def __new__(cls, val):
        if PeriodicCheck.__instance is None:
            PeriodicCheck.__instance = object.__new__(cls)
        PeriodicCheck.__instance.val = val
        return PeriodicCheck.__instance

    def __repr__(self):
        """"""
        return str(self)

    @classmethod
    async def run(cls):
        """Функция запуска проверок"""
        await cls.start_checks()

    @staticmethod
    async def start_checks() -> None:
        """Запуск указанных поверок"""

        check_data_base_task = asyncio.gather(periodic_check_data_base())
        check_work_task = asyncio.gather(periodic_check_work())
        check_unclosed_points_task = asyncio.gather(periodic_check_unclosed_points())
        check_indefinite_normative = asyncio.gather(periodic_check_indefinite_normative())
        check_unclosed_points_for_subcontractor = asyncio.gather(periodic_check_unclosed_points_for_subcontractor())

        await check_data_base_task
        await check_work_task
        await check_unclosed_points_task
        await check_indefinite_normative
        await check_unclosed_points_for_subcontractor


async def test():
    try:
        periodic_check_task = asyncio.create_task(PeriodicCheck.run(), name='PeriodicCheck.create_qr_code')
        await periodic_check_task

    except KeyboardInterrupt as err:
        logger.error(f'Error run_app {repr(err)}')
        sys.exit(0)


if __name__ == '__main__':
    asyncio.run(test())
