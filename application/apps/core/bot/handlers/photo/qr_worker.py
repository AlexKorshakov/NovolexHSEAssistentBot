from __future__ import annotations

import cv2
from pandas import DataFrame
from pyzbar import pyzbar
from itertools import chain

from apps.MyBot import bot_send_message
from apps.core.bot.messages.messages import Messages
from apps.core.database.db_utils import (db_get_data_list,
                                         db_get_data_dict_from_table_with_id,
                                         db_get_clean_headers)
from apps.core.database.query_constructor import QueryConstructor
from loader import logger


async def generate_text(hse_user_id: str | int, qr_data: str | list = None) -> str:
    """Получение информации из data

    :param hse_user_id:
    :param qr_data:
    :return:
    """
    if qr_data is None:
        return ""

    qr_data_list: list = []
    if isinstance(qr_data, list):
        qr_data_list: list = list(chain(*qr_data))

    qr_data_text: list = []
    for qr_data_item in qr_data_list:

        if isinstance(qr_data_item, str):
            qr_data_list: list = qr_data_item.split("_")
            if qr_data_list[0] != 'qr':
                return ''

            if len(qr_data_list) < 3:
                return ''

            act_number = qr_data_list[-1]
            user_id = qr_data_list[-2]

            violations_df: DataFrame = await get_violations_df(act_number, hse_user_id)
            if not await check_dataframe(violations_df, hse_user_id=hse_user_id):
                await bot_send_message(chat_id=hse_user_id, text='Данные не найдены dataframe')
                continue

            act_text: str = await text_processor_act(act_number, violations_df, hse_user_id)
            items_text: str = await text_processor_items(violations_df, hse_user_id=user_id)

            qr_data_text.append(f'{act_text}\n\n{items_text}')

    return '\n\n '.join(qr_data_text)


async def get_violations_df(act_number: str | int, hse_user_id: str | int) -> DataFrame | None:
    """

    :return:
    """

    query_kwargs: dict = {
        "action": 'SELECT',
        "subject": '*',
        "conditions": {
            "act_number": act_number,
        },
    }
    query: str = await QueryConstructor(None, 'core_violations', **query_kwargs).prepare_data()

    violations_dataframe: DataFrame = await create_lite_dataframe_from_query(
        query=query, table_name='core_violations'
    )
    if not await check_dataframe(violations_dataframe, hse_user_id):
        return None

    return violations_dataframe


async def text_processor_act(act_number: int | str, act_violations_df: DataFrame, hse_user_id: str | int) -> str:
    """Формирование текста для отправки пользователю"""

    if not act_number:
        return ''

    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "act_number": act_number,
        },
    }
    query: str = await QueryConstructor(None, 'core_actsprescriptions', **query_kwargs).prepare_data()

    act_dataframe: DataFrame = await create_lite_dataframe_from_query(
        query=query, table_name='core_actsprescriptions'
    )
    if not await check_dataframe(act_dataframe, hse_user_id):
        return ''

    len_violations: int = 0
    if act_dataframe.act_row_count.unique().tolist():
        len_violations = act_dataframe.act_row_count.unique().tolist()[0]

    act_date = ''
    if act_dataframe.act_date.unique().tolist():
        act_date = act_dataframe.act_date.unique().tolist()[0]

    general_constractor: str = ''
    if act_dataframe.act_general_contractor_id.unique().tolist()[0]:
        item_general_constractor_id = act_dataframe.act_general_contractor_id.unique().tolist()[0]

        general_constractor: str = await get_item_title_for_id(
            table_name='core_generalcontractor', item_id=item_general_constractor_id
        )

    unclosed_points_df = act_violations_df.loc[act_violations_df['status_id'] != 1]
    unclosed_points: int = len(unclosed_points_df)

    act_description: list = []
    item_info = f'Ном: {act_number} от {act_date} {general_constractor} всего пунктов: {len_violations} Незакрыто: {unclosed_points}'
    act_description.append(item_info)

    header_text: str = 'Акт - предписание '
    acts_text: str = '\n'.join(act_description)

    final_text: str = f'{header_text} \n\n{acts_text}'
    return final_text


async def text_processor_items(user_violations_df: DataFrame, hse_user_id: str | int) -> str:
    """Формирование текста для отправки пользователю

    """
    unique_items_ids: list = user_violations_df.id.unique().tolist()
    if not unique_items_ids:
        return ''

    items_description: list = []
    for item_id in unique_items_ids:

        item_violations_dataframe = user_violations_df.copy(deep=True)
        item_df = item_violations_dataframe.loc[item_violations_dataframe['id'] == item_id]

        if not await check_dataframe(item_violations_dataframe, hse_user_id):
            continue

        created_at = item_df['created_at'].values[0]
        item_status = await get_item_title_for_id(
            'core_status', item_id=item_df['status_id'].values[0]
        )
        item_main_category = await get_item_title_for_id(
            table_name='core_maincategory', item_id=item_df['main_category_id'].values[0]
        )
        item_category = await get_item_title_for_id(
            table_name='core_category', item_id=item_df['category_id'].values[0]
        )
        item_general_contractor_id = await get_item_title_for_id(
            table_name='core_generalcontractor', item_id=item_df['general_contractor_id'].values[0]
        )
        item_main_location = await get_item_title_for_id(
            table_name='core_mainlocation', item_id=item_df['main_location_id'].values[0]
        )
        item_sub_location = await get_item_title_for_id(
            table_name='core_sublocation', item_id=item_df['sub_location_id'].values[0]
        )
        item_description = item_df['description'].values[0]
        elimination_time = await get_item_title_for_id(
            table_name='core_eliminationtime', item_id=item_df['elimination_time_id'].values[0]
        )
        normative_documents_title = await get_item_title_for_id(
            table_name='core_normativedocuments', item_id=item_df['normative_documents_id'].values[0],
        )

        normative_documents_desc = await get_item_title_for_id(
            table_name='core_normativedocuments', item_id=item_df['normative_documents_id'].values[0],
            item_name='normative'
        )

        item_info = f'Ном пункта: {item_id} от {created_at} Статус: {item_status} \n\n' \
                    f'Устранить до: {elimination_time} \n' \
                    f'Подрядчик: {item_general_contractor_id} \n' \
                    f'Территория: {item_main_location} - {item_sub_location} \n' \
                    f'Направление: {item_main_category} \n' \
                    f'Категория: {item_category} \n' \
                    f'Описание: {item_description} \n' \
                    f'Подкатегория: {normative_documents_title} \n' \
                    f'Нормативка: {normative_documents_desc}\n'

        items_description.append(item_info)

    items_text: str = '\n'.join(items_description)

    # header_text: str = 'Выбранный пункт:'
    # footer_text: str = 'Выберите характеристику для изменения'
    #
    # final_text: str = f'{header_text} \n\n{items_text}  \n\n{footer_text}'
    return items_text


async def create_lite_dataframe_from_query(query: str, table_name: str,
                                           hse_user_id: str | int = None) -> DataFrame or None:
    """Возвращает list с нарушениями

    :return: DataFrame or None
    """

    if not query:
        # logger.error(f"{hse_user_id} {LogMessage.Check.no_query} ::: {await get_now()}")
        return None

    violations_data: list = await db_get_data_list(query=query)

    if not violations_data:
        # logger.debug(f"{hse_user_id} {LogMessage.Check.no_violations} ::: {await get_now()}")
        return None

    clean_headers = await db_get_clean_headers(table_name=table_name)

    try:
        dataframe = DataFrame(violations_data, columns=clean_headers)
        return dataframe
    except Exception as err:
        logger.error(f"{hse_user_id} create_dataframe error {repr(err)}")
        return None


async def get_item_title_for_id(table_name: str, item_id: int, item_name: str = None) -> str:
    """

    :param item_name:
    :param table_name:
    :param item_id:
    :return:
    """
    item_dict: dict = await db_get_data_dict_from_table_with_id(
        table_name=table_name,
        post_id=item_id
    )

    item_name = item_name if item_name else 'title'
    item_text: str = item_dict.get(item_name, '')
    return item_text


def read_qr_code_image(filename: str):
    """Чтение изображения

    :return:
    """
    return cv2.imread(filename)


async def qr_code_reader(hse_user_id, image) -> list:
    """Распознавание QR-кода на изображении

    :param hse_user_id:
    :param image: - объект изображения
    :return:
    """
    # initialize the cv2 QRCode detector

    all_data: list = []
    qrcodes = pyzbar.decode(image)

    for qrcode in qrcodes:
        qrcode_data: str = qrcode.data.decode('utf-8')
        logger.info(f'{hse_user_id} :: {qrcode.type} :: {qrcode_data}')

        if qrcode.type == 'QRCODE':
            all_data.append(qrcode_data.split('&'))

        if qrcode.type == 'EAN8':
            all_data.append(f'personal_id_code_{qrcode_data}')

    return all_data


async def check_dataframe(dataframe: DataFrame, hse_user_id: str | int) -> bool:
    """Проверка dataframe на наличие данных

    :param dataframe:
    :param hse_user_id: id пользователя
    :return:
    """
    if dataframe is None:
        text_violations: str = 'не удалось получить данные!'
        logger.error(f'{hse_user_id = } {text_violations}')
        return False

    if dataframe.empty:
        logger.error(f'{hse_user_id = } {Messages.Error.dataframe_is_empty}')
        return False

    return True
