from __future__ import annotations
import asyncio
from datetime import date, datetime

import pandas
from loader import logger


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


async def get_week_message(current_date: datetime | str = None) -> str:
    """Обработчик сообщений с фото
    Получение номер str недели из сообщения в формате dd
    """
    current_date: date = await str_to_datetime(current_date)

    if not current_date:
        current_date: datetime = datetime.now()
    week = current_date.isocalendar()[1]
    return str("0" + str(week) if week < 10 else str(week))


async def get_quarter_message(current_date: datetime | str = None) -> str:
    """Обработчик сообщений с фото
    Получение номер str квартала из сообщения в формате dd
    """
    current_date: date = await str_to_datetime(current_date)

    if not current_date:
        current_date: date = datetime.now()
    quarter = pandas.Timestamp(current_date).quarter
    return str("0" + str(quarter) if quarter < 10 else str(quarter))


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


async def get_day_message(current_date: datetime | str = None) -> str:
    """Обработчик сообщений с фото
    Получение номер str дня из сообщения в формате dd
    """

    current_date: date = await str_to_datetime(current_date)

    if not current_date:
        current_date: datetime = datetime.now()
    return str("0" + str(current_date.day) if current_date.day < 10 else str(current_date.day))


async def get_day_of_year_message(current_date: datetime | str = None) -> str:
    """Возвращает номер дня в году для даты сообщения

    """

    current_date: date = await str_to_datetime(current_date)

    if not current_date:
        current_date: datetime = datetime.now()
    day_of_year = pandas.Timestamp(current_date).day_of_year
    return str("0" + str(day_of_year) if day_of_year < 10 else str(day_of_year))


async def test(current_datetime):
    day = await get_day_message(current_datetime)
    print(f'{day = }')

    week = await get_week_message(current_datetime)
    print(f'{week = }')

    month = await get_month_message(current_datetime)
    print(f'{month = }')

    quarter = await get_quarter_message(current_datetime)
    print(f'{quarter = }')

    year = await get_year_message(current_datetime)
    print(f'{year = }')

    day_of_year = await get_day_of_year_message(current_datetime)
    print(f'{day_of_year = }')


if __name__ == "__main__":
    # act_date: str = datetime.now().strftime("%d.%m.%Y")
    act_date: str = '17.09.2022'

    asyncio.run(
        test(
            current_datetime=act_date
        )
    )
