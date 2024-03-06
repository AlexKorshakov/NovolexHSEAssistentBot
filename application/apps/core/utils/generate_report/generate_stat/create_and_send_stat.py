import asyncio
from datetime import datetime
from pprint import pprint

from apps.core.bot.messages.messages import Messages
from apps.core.database.query_constructor import QueryConstructor
# from apps.core.bot.handlers.generate.generate_report.convert_xlsx_to_pdf import \
#     convert_report_to_pdf
from apps.core.bot.handlers.generate.generate_report.generate_stat.create_stat import \
    create_stat
from apps.core.bot.handlers.generate.generate_report.get_report_path import get_full_stat_name
from apps.core.bot.handlers.generate.generate_report.send_report_from_user import \
    send_report_from_user
from apps.core.utils.reports_processor.report_worker_utils import (
    create_lite_dataframe_from_query, format_data_db, get_clean_headers)
from apps.core.utils.secondary_functions.get_part_date import (
    get_month_message, get_week_message, get_year_message)
from apps.MyBot import bot_send_message
from loader import logger
from pandas import DataFrame


async def create_and_send_stat(chat_id, query_period: [list, str] = None, **stat_kwargs) -> bool:
    """Формирование и отправка отчета

    :param query_period:
    :param chat_id:
    :return:
    """

    if not query_period:
        stat_date: str = datetime.now().strftime("%d.%m.%Y")  # '28.10.2022'  #
        query_period = await format_data_db(stat_date)

    table_name: str = 'core_violations'
    clean_headers: list = await get_clean_headers(table_name=table_name)

    if not clean_headers:
        logger.error(f'create_and_send_stat: No clean headers in {table_name}')
        return False

    kwargs: dict = {
        "type_query": 'query_statistic',
        "action": 'SELECT',
        "subject": '*',
        "conditions": {
            "period": query_period,
            "period_description": 'Период для формирования запроса. Может состоять из одной или двух дат',

            "is_admin": stat_kwargs.get('is_admin', None),
            "is_admin_description": 'Является ли пользователь админом.'
                                    'Если является - в запросе опускается часть с id пользователя',

            "location": stat_kwargs.get('location', None),
            "location_description": 'location_id локации по которой выполняется запрос'
                                    'Если отсутствует или None - в запросе опускается часть с location_id',

            'act_number': 'not',
            "act_number_description": 'Если отсутствует или None - в запросе опускается часть с location_id',
        }
    }

    query: str = await QueryConstructor(chat_id, table_name='core_violations', **kwargs).prepare_data()
    print(f'get_stat_dataframe {query = }')

    stat_dataframe: DataFrame = await get_stat_dataframe_with_query(
        chat_id, query=query, header_list=clean_headers,
    )

    if stat_dataframe.empty:
        logger.error(Messages.Error.dataframe_not_found)
        await bot_send_message(chat_id=chat_id, text=Messages.Error.dataframe_not_found)
        return False

    full_stat_path: str = await get_full_stat_name(chat_id=chat_id)

    stat_is_created: bool = await create_stat(
        chat_id=chat_id,
        dataframe=stat_dataframe,
        full_stat_path=full_stat_path,
        query_period=query_period
    )

    if not stat_is_created:
        return False

    await bot_send_message(chat_id=chat_id, text=f'{Messages.Report.done} \n')

    await send_stat(chat_id=chat_id, full_report_path=full_stat_path)

    return True


async def get_stat_dataframe_with_query(chat_id, query: str, header_list: list = None):
    """Получение dataframe с данными статистики

    :return:
    """

    stat_dataframe: DataFrame = await create_lite_dataframe_from_query(
        chat_id=chat_id, query=query, clean_headers=header_list
    )
    return stat_dataframe


# async def get_stat_dataframe(chat_id, stat_period, headers):
#     """Получение dataframe с данными статистики
#
#     :return:
#     """
#     table_name: str = 'core_violations'
#
#     query: str = await get_query(
#         type_query='query_stat', table_name=table_name, query_date=stat_period, user_id=chat_id
#     )
#
#     print(f'get_stat_dataframe {query = }')
#
#     stat_dataframe: DataFrame = await create_lite_dataframe_from_query(
#         chat_id=chat_id, query=query, clean_headers=headers
#     )
#     return stat_dataframe


async def send_stat(chat_id: str, full_report_path: str):
    """Отправка отчета пользователю в заданных форматах

    :return:
    """

    # await convert_report_to_pdf(
    #     chat_id=chat_id, path=full_report_path
    # )
    await send_report_from_user(
        chat_id=chat_id, full_report_path=full_report_path
    )
    # full_stat_path = full_report_path.replace(".xlsx", ".pdf")
    #
    # await send_report_from_user(
    #     chat_id=chat_id, full_report_path=full_stat_path
    # )


async def test():
    chat_id = 373084462  #

    now = datetime.now()

    current_week: str = await get_week_message(current_date=now)
    current_month: str = await get_month_message(current_date=now)
    current_year: str = await get_year_message(current_date=now)

    # stat_date_period: list = await db_get_period_for_current_week(current_week, current_year)
    # pprint(f"{stat_date_period = }")
    # stat_date_period: list = await db_get_period_for_current_month(current_month, current_year)
    # pprint(f"{stat_date_period = }")
    # stat_date_period: str = datetime.now().strftime("%d.%m.%Y")  # '28.10.2022'  #
    # pprint(f"{stat_date_period = }")

    stat_date_period: list = ['01.01.2022', datetime.now().strftime("%d.%m.%Y")]
    pprint(f"{stat_date_period = }")

    # now = datetime.now()
    # stat_date_period: list = [now.strftime("%d.%m.%Y"), now.strftime("%d.%m.%Y"), ]

    kwargs = {
        'is_admin': 0,
        'location': 2
    }

    await create_and_send_stat(chat_id, stat_date_period, **kwargs)


if __name__ == "__main__":
    asyncio.run(test())
