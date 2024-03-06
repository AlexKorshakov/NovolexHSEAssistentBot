import asyncio
import traceback

from apps.core.checker.check_utils import get_now
from apps.core.settyngs import get_sett
from loader import logger


async def periodic_check_work():
    """Периодическое напоминание о работе"""

    while True:

        work_period: int = get_sett(cat='param', param='check_work').get_set()

        await asyncio.sleep(1)

        if not get_sett(cat='check', param='check_work').get_set():
            logger.warning(f'{await fanc_name()} not access')
            await asyncio.sleep(work_period)
            continue

        logger.info(f"i'm work ::: {await get_now()}")
        await asyncio.sleep(work_period)


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])
