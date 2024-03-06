from loader import logger

logger.debug(f"{__name__} start import")
import asyncio
from datetime import datetime
from pprint import pprint

from pandas import DataFrame

from apps.MyBot import bot_send_message
from apps.core.bot.messages.messages import Messages
from apps.core.database.db_utils import db_get_period_for_current_week
from apps.core.database.query_constructor import QueryConstructor
from apps.core.bot.handlers.generate.generate_report.convert_xlsx_to_pdf import convert_report_to_pdf
from apps.core.bot.handlers.generate.generate_report.generate_daily_report.create_daily_report import create_daily_report
from apps.core.bot.handlers.generate.generate_report.get_report_path import get_full_daily_report_name
from apps.core.bot.handlers.generate.generate_report.send_report_from_user import send_report_from_user
from apps.core.utils.reports_processor.report_worker_utils import format_data_db, create_lite_dataframe_from_query, \
    get_clean_headers
from apps.core.utils.secondary_functions.get_part_date import get_week_message, get_year_message

logger.debug(f"{__name__} finish import")


async def create_and_send_daily_report(chat_id, query_period: list = None, **daily_report_kwargs) -> bool:
    """Формирование и отправка отчета

    :param query_period:
    :param chat_id:
    :return:
    """

    daily_report_date: str = datetime.now().strftime("%d.%m.%Y")  # '28.10.2022'  #

    if not query_period:
        query_period = await format_data_db(daily_report_date)

    table_name: str = 'core_violations'
    clean_headers: list = await get_clean_headers(table_name=table_name)

    full_daily_report_path: str = await get_full_daily_report_name(chat_id=chat_id)

    kwargs: dict = {
        "type_query": 'query_statistic',
        "action": 'SELECT',
        "subject": '*',
        "conditions": {
            "period": query_period,
            "period_description": 'Период для формирования запроса. Может состоять из одной или двух дат',

            "is_admin": daily_report_kwargs.get('is_admin', None),
            "is_admin_description": 'Является ли пользователь админом.'
                                    'Если является - в запросе опускается часть с id пользователя',

            "location": daily_report_kwargs.get('location', None),
            "location_description": 'location_id локации по которой выполняется запрос'
                                    'Если отсутствует или None - в запросе опускается часть с location_id',
        }
    }

    query: str = await QueryConstructor(chat_id, table_name='core_violations', **kwargs).prepare_data()
    print(f'get_stat_dataframe {query = }')

    daily_report_dataframe: DataFrame = await get_daily_report_dataframe_with_query(
        chat_id=chat_id, query=query, headers=clean_headers,
    )

    if daily_report_dataframe.empty:
        logger.error(Messages.Error.dataframe_not_found)
        await bot_send_message(chat_id=chat_id, text=Messages.Error.dataframe_not_found)
        return False

    act_is_created: bool = await create_daily_report(
        chat_id=chat_id,
        dataframe=daily_report_dataframe,
        full_daily_report_report_path=full_daily_report_path
    )

    if not act_is_created:
        return False

    # try:
    #     await bot_send_message(chat_id=chat_id, text=f'{Messages.Report.done} \n')
    # except Exception as err:
    #     logger.error(f'create_and_send_daily_report Exception {repr(err)}')

    await send_daily_report(chat_id=chat_id, full_report_path=full_daily_report_path)

    return True


async def get_daily_report_dataframe_with_query(chat_id, query, headers):
    """Получение dataframe с данными акта - предписания

    :return:
    """

    act_dataframe: DataFrame = await create_lite_dataframe_from_query(
        chat_id=chat_id, query=query, clean_headers=headers
    )
    return act_dataframe


async def send_daily_report(chat_id: str, full_report_path: str):
    """Отправка отчета пользователю в заданных форматах

    :return:
    """

    await convert_report_to_pdf(
        chat_id=chat_id, path=full_report_path
    )
    await send_report_from_user(
        chat_id=chat_id, full_report_path=full_report_path
    )
    full_act_prescription_path = full_report_path.replace(".xlsx", ".pdf")

    await send_report_from_user(
        chat_id=chat_id, full_report_path=full_act_prescription_path
    )


async def test():
    chat_id = 373084462

    now = datetime.now()

    current_week: str = await get_week_message(current_date=now)
    current_year: str = await get_year_message(current_date=now)

    act_date_period = await db_get_period_for_current_week(current_week, current_year)
    pprint(f"{act_date_period = }")

    await create_and_send_daily_report(chat_id, act_date_period)


if __name__ == "__main__":
    asyncio.run(test())
