from datetime import datetime
from pandas import DataFrame

from loader import logger
from apps.MyBot import bot_send_message
from apps.core.bot.messages.messages import Messages
from apps.core.database.db_utils import (db_get_data_dict_from_table_with_id,
                                         db_get_data_list,
                                         db_get_clean_headers)


async def get_clear_list_value(chat_id: int, query: str, clean_headers: list) -> list[dict]:
    """Получение данных с заголовками

    :return: clear_list : list
    """

    datas_query: list = await db_get_data_list(query=query)

    if not datas_query:
        logger.info(Messages.Error.data_not_found)
        await bot_send_message(chat_id=chat_id, text=Messages.Error.data_not_found)
        return []

    clear_list_value: list = []
    for items_value in datas_query:
        item_dict: dict = dict((header, item_value) for header, item_value in zip(clean_headers, items_value))
        clear_list_value.append(item_dict)

    return clear_list_value


async def get_general_constractor_list(clear_list_value: list) -> list:
    """Получение списка get_general_constractor_list

    """
    general_constractor_list = [item_value.get('general_contractor_id') for item_value in clear_list_value]
    general_constractor_list = list(set(general_constractor_list))

    return general_constractor_list


async def get_sub_locations_ids_list(clear_list_value: list) -> list:
    """Получение списка get_general_constractor_list

    """
    sub_locations_ids_list = [item_value.get('sub_location_id') for item_value in clear_list_value]
    sub_locations_ids_list = list(set(sub_locations_ids_list))

    return sub_locations_ids_list


async def get_general_constractor_data(constractor_id: int, type_constractor: str) -> dict:
    """Получение данных из таблицы `core_generalcontractor` по constractor_id

    :return:
    """
    contractor: dict = {}

    if type_constractor == 'general':
        contractor = await db_get_data_dict_from_table_with_id(
            table_name='core_generalcontractor',
            post_id=constractor_id)

    if type_constractor == 'sub':
        contractor = await db_get_data_dict_from_table_with_id(
            table_name='core_subcontractor',
            post_id=constractor_id)

    if not contractor:
        return {}

    return contractor


async def get_clean_headers(table_name: str) -> list:
    """Получение заголовков таблицы по имени table_name

    :param table_name: str - имя таблицы для получения заголовков
    :return: list[str] or []
    """

    if not table_name:
        return []

    clean_headers: list = await db_get_clean_headers(table_name=table_name)
    logger.debug(clean_headers)

    return clean_headers


async def create_lite_dataframe_from_query(chat_id: int, query: str, clean_headers: list) -> DataFrame:
    """Формирование dataframe из запроса query и заголовков clean_headers

    :param chat_id: id  пользователя
    :param clean_headers: заголовки таблицы для формирования dataframe
    :param query: запрос в базу данных
    :return:
    """

    item_datas_query: list = await db_get_data_list(query=query)
    report_dataframe: DataFrame = await create_lite_dataframe(
        chat_id=chat_id, data_list=item_datas_query, header_list=clean_headers
    )

    if report_dataframe.empty:
        logger.error(f'{Messages.Error.dataframe_is_empty}  \n{chat_id = }  \n{query = }  \n{item_datas_query = }')
        await bot_send_message(chat_id=chat_id, text=Messages.Error.dataframe_is_empty)

    return report_dataframe


async def create_lite_dataframe(chat_id, data_list: list, header_list: list) -> DataFrame:
    """Создание dataframe

    :param chat_id:
    :param header_list: список с заголовками
    :param data_list: список с данными
    """
    try:
        dataframe: DataFrame = DataFrame(data_list, columns=header_list)
        return dataframe

    except Exception as err:
        logger.error(F"create_dataframe {repr(err)}")
        return None


async def get_query(type_query: str, table_name: str, query_date: str = None, value_id: int = None, user_id=None) -> str:
    """

    """
    query = ''
    if type_query == 'general_contractor_id':
        if isinstance(query_date, list):
            query: str = f'SELECT * ' \
                         f'FROM {table_name} ' \
                         f"WHERE (`act_number` = '' or `act_number` is NULL ) " \
                         f"AND `general_contractor_id` = {value_id} " \
                         f"AND `act_required_id` = 1 " \
                         f"AND `created_at` BETWEEN date('{await format_data_db(query_date[0])}') " \
                         f"AND date('{await format_data_db(query_date[1])}') " \
                         f"AND `user_id` = {user_id}"
        else:
            query: str = f'SELECT * ' \
                         f'FROM {table_name} ' \
                         f"WHERE (`created_at` = date('{query_date}') " \
                         f"AND (`act_number` = '' or `act_number` is NULL ) " \
                         f"AND `general_contractor_id` = {value_id} " \
                         f"AND `act_required_id` = 1 " \
                         f"AND `user_id` = {user_id}" \
                         f") "

    if type_query == 'sub_location_id':
        query: str = f'SELECT * ' \
                     f'FROM {table_name} ' \
                     f"WHERE (`created_at` = date('{query_date}') " \
                     f"AND `act_required_id` = 1 " \
                     f"AND (`act_number` = '' or `act_number` is NULL ) " \
                     f"AND `sub_location_id` = {value_id})"

    if type_query == 'query_act':
        if isinstance(query_date, list):
            query: str = f'SELECT * ' \
                         f'FROM {table_name} ' \
                         f"WHERE (`act_number` = '' or `act_number` is NULL ) " \
                         f"AND `act_required_id` = 1 " \
                         f"AND `created_at` BETWEEN date('{await format_data_db(query_date[0])}') " \
                         f"AND date('{await format_data_db(query_date[1])}') " \
                         f"AND `user_id` = {user_id}"

        if isinstance(query_date, str):
            query: str = f'SELECT * ' \
                         f'FROM {table_name} ' \
                         f"AND `act_required_id` = 1 " \
                         f"WHERE (`created_at` = date('{query_date}') " \
                         f"AND (`act_number` = '' or `act_number` is NULL ) " \
                         f"AND `user_id` = {user_id} )"

    # if type_query == 'query_daily_report':
    #     if isinstance(query_date, list):
    #         query: str = f'SELECT * ' \
    #                      f'FROM {table_name} ' \
    #                      f"WHERE `user_id` = {user_id} " \
    #                      f"AND `created_at` BETWEEN date('{await format_data_db(query_date[0])}') " \
    #                      f"AND date('{await format_data_db(query_date[1])}') "
    #
    #     if isinstance(query_date, str):
    #         query: str = f'SELECT * ' \
    #                      f'FROM {table_name} ' \
    #                      f"WHERE `user_id` = {user_id} " \
    #                      f"AND (`created_at` = date('{query_date}') )"
    #
    # if type_query == 'query_stat':
    #     if isinstance(query_date, list):
    #         query: str = f'SELECT * ' \
    #                      f'FROM {table_name} ' \
    #                      f"WHERE `user_id` = {user_id} " \
    #                      f"AND `created_at` BETWEEN date('{await format_data_db(query_date[0])}') " \
    #                      f"AND date('{await format_data_db(query_date[1])}') "
    #
    #     if isinstance(query_date, str):
    #         query: str = f'SELECT * ' \
    #                      f'FROM {table_name} ' \
    #                      f"WHERE `user_id` = {user_id} " \
    #                      f"AND (`created_at` = date('{query_date}') )"

    return query


async def format_data_db(date_item: str):
    """ Форматирование даты в формат даты БВ
    """
    return datetime.strptime(date_item, "%d.%m.%Y").strftime("%Y-%m-%d")
