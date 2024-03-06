from __future__ import annotations
import asyncio
import math
import traceback
from datetime import datetime

from pandas import DataFrame

from apps.core.settyngs import get_sett
from loader import logger
from apps.MyBot import bot_send_message
from apps.core.bot.messages.messages import LogMessage, Messages
from apps.core.database.db_utils import (db_get_data_list,
                                         db_get_data_dict_from_table_with_id,
                                         db_get_clean_headers)
from apps.core.database.query_constructor import QueryConstructor


async def periodic_check_indefinite_normative():
    """Периодическая проверка записей с не определенной нормативной документацией"""

    while True:

        offset_hour: int = get_sett(cat='param', param='offset_hour').get_set()
        work_period: int = get_sett(cat='param', param='check_work_period').get_set()

        await asyncio.sleep(1)

        now = datetime.now()
        if not 18 + offset_hour > now.hour + 1 > 9 + offset_hour:
            logger.info(f"{LogMessage.Check.time_period_error} ::: {await get_now()}")
            await asyncio.sleep(work_period)
            continue

        if not get_sett(cat='check', param='check_indefinite_normative').get_set():
            logger.warning(f'{await fanc_name()} not access')
            await asyncio.sleep(work_period)
            continue

        result_check_list: bool = await check_indefinite_normative()

        if result_check_list:
            logger.info(f"{LogMessage.Check.periodic_check_indefinite_normative} ::: {await get_now()}")
        else:
            logger.error(f'Error check_indefinite_normative {result_check_list = } ::: {await get_now()}')

        await asyncio.sleep(work_period)


async def check_indefinite_normative(*args) -> bool:
    """Проверка наличия записей в БД со статусом - не определена нормативная документация

    """

    query_kwargs: dict = {
        "action": 'SELECT',
        "subject": '*',
        "conditions": {
            "normative_documents_id": "= 0",
        },
    }
    query: str = await QueryConstructor(None, 'core_violations', **query_kwargs).prepare_data()

    violations_dataframe: DataFrame = await create_lite_dataframe_from_query(query=query, table_name='core_violations')
    if violations_dataframe.empty:
        logger.error(f'{Messages.Error.dataframe_is_empty}  \n{query = }')
        return False

    unique_violations_ids: list = violations_dataframe.id.unique().tolist()
    logger.debug(f'{unique_violations_ids = }')

    if not unique_violations_ids:
        return False

    text_violations: str = await text_processor_user_violations(violations_dataframe)

    text_v_list: list = await text_processor(text=text_violations)
    developer_ids_list: list = await get_developer_id_list()

    for dev_id in developer_ids_list:
        for item_txt in text_v_list:
            await bot_send_message(chat_id=dev_id, text=item_txt)

    return True


async def text_processor(text: str = None) -> list:
    """Принимает data_list_to_text[] для формирования текста ответа
    Если len(text) <= 3500 - отправляет [сообщение]
    Если len(text) > 3500 - формирует list_with_parts_text = []

    :param text:
    :return: list - list_with_parts_text
    """
    if not text:
        return []

    step = 3500
    if len(text) <= step:
        return [text]

    len_parts = math.ceil(len(text) / step)
    list_with_parts_text: list = [text[step * (i - 1):step * i] for i in range(1, len_parts + 1)]

    return list_with_parts_text


async def text_processor_user_violations(violations_dataframe: DataFrame) -> str:
    """Получение текста с описанием

    """
    unique_violations_numbers: list = violations_dataframe.id.unique().tolist()

    act_description: list = []
    len_violations: int = len(violations_dataframe) if not violations_dataframe.empty else 0

    for violation_number in unique_violations_numbers:

        if not violation_number:
            continue

        violation_items_df: DataFrame = violations_dataframe.loc[violations_dataframe['id'] == violation_number]
        violation_date: str = violation_items_df.created_at.values[0]
        violation_description: str = violation_items_df.description.values[0]
        violation_comment: str = violation_items_df.comment.values[0]

        violation_main_category_id = violation_items_df.main_category_id.values[0]
        violation_main_category: str = await get_item_title_for_id(
            table_name='core_maincategory', item_id=violation_main_category_id
        )
        violation_category_id = violation_items_df.category_id.values[0]
        violation_category: str = await get_item_title_for_id(
            table_name='core_category', item_id=violation_category_id
        )
        violation_name_id = violation_items_df.hse_id.values[0]
        violation_name: str = await get_item_title_for_id(
            table_name='core_hseuser', item_id=violation_name_id, item_name='hse_full_name'
        )
        item_info = f'Ном записи: {violation_number} от {violation_date}\n' \
                    f'Основная категория: {violation_main_category}\n' \
                    f'Категория: {violation_category}\n' \
                    f'Запись: {violation_description}\n' \
                    f'Устранение: {violation_comment}\n' \
                    f'Запись внес: {violation_name}\n'

        act_description.append(item_info)

    header_text: str = f'В Базе Данных есть записи с неизвестной НД. Всего записей {len_violations}'
    footer_text: str = 'Для действий выберите в меню соответствующую команду(/correct_entries)'

    acts_text: str = '\n\n'.join(act_description)

    final_text: str = f'{header_text} \n\n{acts_text} \n\n{footer_text}'
    return final_text


async def get_item_title_for_id(table_name: str, item_id: int, item_name: str = None) -> str:
    """Получение параметра из table_name по id и item_name

    :param item_name: имя параметра
    :param table_name: имя таблицы для поиска
    :param item_id: id записи
    :return: str - текстовое значение параметра записи
    """
    item_dict: dict = await db_get_data_dict_from_table_with_id(
        table_name=table_name,
        post_id=item_id
    )

    item_name = item_name if item_name else 'title'
    item_text: str = item_dict.get(item_name, '')
    return item_text


async def get_developer_id_list() -> list:
    """Получение id разработчиков"""

    db_table_name: str = 'core_hseuser'

    kwargs: dict = {
        "action": 'SELECT',
        "subject": '*',
    }
    query: str = await QueryConstructor(table_name=db_table_name, **kwargs).prepare_data()
    datas_query: list = await db_get_data_list(query=query)
    if not datas_query:
        return []

    if not isinstance(datas_query, list):
        return []

    clean_headers: list = await db_get_clean_headers(table_name=db_table_name)
    if not clean_headers:
        return []

    try:
        hse_role_receive_df: DataFrame = DataFrame(datas_query, columns=clean_headers)
    except Exception as err:
        logger.error(F"create_dataframe {repr(err)}")
        return []

    current_act_violations_df: DataFrame = hse_role_receive_df.loc[
        hse_role_receive_df['hse_role_is_admin'] == 1
        ]

    unique_hse_telegram_id: list = current_act_violations_df.hse_telegram_id.unique().tolist()
    return unique_hse_telegram_id


async def create_lite_dataframe_from_query(query: str, table_name: str) -> DataFrame or None:
    """Возвращает list с нарушениями

    :return: DataFrame or None
    """

    if not query:
        logger.error(f"{LogMessage.Check.no_query} ::: {await get_now()}")
        return None

    violations_data: list = await db_get_data_list(query=query)

    if not violations_data:
        logger.debug(f"{LogMessage.Check.no_violations} ::: {await get_now()}")
        return None

    clean_headers = await db_get_clean_headers(table_name=table_name)

    try:
        dataframe = DataFrame(violations_data, columns=clean_headers)
        return dataframe
    except Exception as err:
        logger.error(f"create_dataframe {repr(err)}")
        return None


async def get_now() -> str:
    """Возвращает текущую дату и время.
    :return: str
    """
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])


async def test():
    await periodic_check_indefinite_normative()


if __name__ == '__main__':
    asyncio.run(test())
