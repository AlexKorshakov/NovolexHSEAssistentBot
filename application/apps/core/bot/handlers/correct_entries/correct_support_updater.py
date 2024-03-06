from __future__ import annotations

import os

from pandas import DataFrame

from apps.MyBot import bot_send_message
from apps.core.bot.handlers.correct_entries.correct_support import (create_lite_dataframe_from_query,
                                                                    check_dataframe,
                                                                    spotter_data)
from apps.core.bot.handlers.generate.generate_act_prescription_and_send import get_full_patch_to_act_prescription
from apps.core.database.db_utils import (db_update_column_value,
                                         db_get_dict_userdata,
                                         db_get_data_dict_from_table_with_id)
from apps.core.database.query_constructor import QueryConstructor
from apps.core.utils.json_worker.read_json_file import read_json_file
from apps.core.utils.json_worker.writer_json_file import write_json_file
from apps.core.utils.reports_processor.report_worker_utils import get_general_constractor_data
from apps.core.utils.secondary_functions.get_filepath import Novolex_media_path, REGISTRY_NAME
from config.config import WRITE_DATA_ON_GOOGLE_DRIVE
from loader import logger


async def update_column_value(hse_user_id: int | str, character: str, character_id: int | str,
                              item_number: int | str, violations_dataframe: DataFrame) -> bool:
    """Внесение изменений различными способами

    :return:
    """

    if character not in violations_dataframe.columns.values.tolist():
        return False

    result_update_db: bool = await update_column_value_in_db(
        item_number=item_number, column_name=character, item_value=character_id, hse_user_id=hse_user_id
    )

    result_update_local: bool = await update_column_value_in_local(
        item_number=item_number, column_name=character, item_value=character_id, hse_user_id=hse_user_id,
        v_df=violations_dataframe
    )

    result_update_registry: bool = await update_column_value_in_registry(
        item_number=item_number, column_name=character, item_value=character_id, hse_user_id=hse_user_id,
        v_df=violations_dataframe
    )

    result_update_google: bool = await update_column_value_in_google_disk(
        item_number=item_number, column_name=character, item_value=character_id, hse_user_id=hse_user_id
    )

    spotter_data.clear()

    result_list: list = [result_update_db, result_update_local, result_update_registry, result_update_google]

    if not all(result_list):
        await bot_send_message(chat_id=hse_user_id,
                               text=f'{hse_user_id = }. Ошибка обновления данных {item_number} {character = }!')
        return False

    await bot_send_message(chat_id=hse_user_id,
                           text=f'{hse_user_id = }. Данные записи {item_number} {character = } успешно обновлены')
    return True


async def update_column_value_in_db(*, item_number: str | int, column_name: str, item_value: str | int,
                                    hse_user_id: str | int) -> bool:
    """Обновление данных item_value записи violation_id в колонке column_name в базе данных

    :return:
    """

    status_result_execute: bool = await db_update_column_value(
        column_name=column_name,
        value=item_value,
        violation_id=str(item_number)
    )
    if not status_result_execute:
        logger.error(f'{hse_user_id = } Ошибка обновления данных {item_number}  в database!')
        return False

    logger.info(f'{hse_user_id = } Данные записи {item_number} успешно обновлены в database!')
    return True


async def update_column_value_in_local(*, item_number: str | int, column_name: str, item_value: str | int,
                                       hse_user_id: str | int, v_df: DataFrame = None) -> bool:
    """Внесение изменений в файл json на сервере

    :param v_df:
    :param item_number: str | int
    :param column_name: str
    :param item_value: str | int
    :param hse_user_id: str | int id пользователя
    :return: bool
    """

    if not await check_dataframe(v_df, hse_user_id):
        query_kwargs: dict = {
            "action": 'SELECT', "subject": '*',
            "conditions": {
                "id": item_number,
            },
        }
        query: str = await QueryConstructor(None, 'core_violations', **query_kwargs).prepare_data()

        v_df: DataFrame = await create_lite_dataframe_from_query(query=query, table_name='core_violations')
        if not await check_dataframe(v_df, hse_user_id):
            return False

    v_df[column_name] = item_value

    violation_data: dict = v_df.to_dict()
    violation_data = {key: value.get(0, None) for (key, value) in violation_data.items() if value is not None}
    if not violation_data.get('json', None):
        return False

    violation_read_json = await read_json_file(file=f"{Novolex_media_path}\\HSE\\{violation_data.get('json', None)}")
    violation_data.update(violation_read_json)

    if not await write_json_file(data=violation_data,
                                 name=f"{Novolex_media_path}\\HSE\\{violation_data.get('json', None)}"):
        return False

    logger.info(f'{hse_user_id = } Данные записи {item_number} успешно обновлены в local!')
    return True


async def update_column_value_in_registry(*, item_number: str | int, column_name: str, item_value: str | int,
                                          hse_user_id: str | int, v_df: DataFrame = None) -> bool:
    """Внесение изменений в файл json в регистре

    :param v_df:
    :param item_number: str | int
    :param column_name: str
    :param item_value: str | int
    :param hse_user_id: str | int id пользователя
    :return: bool
    """

    if not await check_dataframe(v_df, hse_user_id):
        query_kwargs: dict = {
            "action": 'SELECT', "subject": '*',
            "conditions": {
                "id": item_number,
            },
        }
        query: str = await QueryConstructor(None, 'core_violations', **query_kwargs).prepare_data()

        v_df: DataFrame = await create_lite_dataframe_from_query(query=query, table_name='core_violations')
        if not await check_dataframe(v_df, hse_user_id):
            return False

    v_df[column_name] = item_value

    violation_data: dict = v_df.to_dict()
    violation_data = {key: value.get(0, None) for (key, value) in violation_data.items() if value is not None}
    if not violation_data.get('json', None):
        return False

    hse_user_dict: dict = await db_get_dict_userdata(hse_user_id)
    hse_organization_id: int = hse_user_dict.get('hse_organization', None)
    hse_organization_dict: dict = await db_get_data_dict_from_table_with_id(
        table_name='core_generalcontractor', post_id=hse_organization_id)
    hse_organization_name = hse_organization_dict.get('title', '')

    act_number = v_df.act_number.values[0]

    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "act_number": act_number,
        },
    }
    table_name: str = 'core_actsprescriptions'

    query: str = await QueryConstructor(None, table_name, **query_kwargs).prepare_data()

    act_dataframe: DataFrame = await create_lite_dataframe_from_query(query=query, table_name=table_name)
    if not await check_dataframe(act_dataframe, hse_user_id):
        return False

    act_date: str = act_dataframe.act_date.values[0]
    act_number: str = act_dataframe.act_number.values[0]
    act_constractor_id: int = act_dataframe.act_general_contractor_id.values[0]

    contractor_data: dict = await db_get_data_dict_from_table_with_id(
        table_name='core_generalcontractor',
        post_id=act_constractor_id
    )
    short_title = contractor_data.get('short_title')

    year = act_dataframe.act_year.values[0]
    month = act_dataframe.act_month.values[0]
    month = month if month > 10 else f'0{month}'
    report_path = f"{Novolex_media_path}\\HSE\\{REGISTRY_NAME}\\{hse_organization_name}\\{year}\\{month}"
    report_name = f'Акт-предписание № {act_number} от {act_date} {short_title}'
    report_full_name = f'{report_path}\\{report_name}\\{report_name}.json'

    if not os.path.isfile(path=report_full_name):
        return False

    violation_read_json = await read_json_file(file=report_full_name)
    if not violation_read_json:
        return False

    try:
        violations: list = violation_read_json.get('violations', {})
        violations_items: dict = [item for item in violations if 'violations_items' in item.keys()][0]
        violations_items_list: list = violations_items.get('violations_items', [])

        item_dict: dict = [item for item in violations_items_list if item_number in item.keys()][0]

        violations_items_list.remove(item_dict)
        item_dict[item_number].update(violation_data)
        violations_items_list.append(item_dict)

    except TypeError as err:
        logger.error(f"create_dataframe {repr(err)}")
        return False

    except Exception as err:
        logger.error(f"create_dataframe {repr(err)}")
        return False

    hse_userdata: dict = await db_get_dict_userdata(hse_user_id)
    contractor: dict = await db_get_data_dict_from_table_with_id(
        table_name='core_generalcontractor', post_id=act_constractor_id)

    act_data_dict: dict = {
        'violations': [
            {'violations_items': violations_items_list},
            {'violations_index': len(violations_items_list)},
        ],
        'contractor': contractor,
        'hse_userdata': hse_userdata,
        'hse_organization': hse_organization_dict
    }

    # TODO Дополнить заголовками и пр.

    contractor_data: dict = await get_general_constractor_data(
        constractor_id=act_constractor_id, type_constractor='general'
    )
    if not contractor_data:
        return False

    short_title = contractor_data.get('short_title')

    path_in_registry = await get_full_patch_to_act_prescription(
        chat_id=hse_user_id, act_number=act_number, act_date=act_date, constractor_id=act_constractor_id
    )

    report_full_name = f'Акт-предписание № {act_number} от {act_date} {short_title}.json'
    full_patch_to_act_prescription_json = f"{path_in_registry}\\{report_full_name}"

    await write_json_file(data=act_data_dict, name=full_patch_to_act_prescription_json)

    # if not await write_json_file(data=violation_data, name=report_full_name):
    #     return False

    logger.info(f'{hse_user_id = } Данные записи {item_number} успешно обновлены в registry!')
    return True


async def update_column_value_in_google_disk(*, item_number: str | int, column_name: str, item_value: str | int,
                                             hse_user_id: str | int) -> bool:
    if not WRITE_DATA_ON_GOOGLE_DRIVE:
        logger.info(f'{WRITE_DATA_ON_GOOGLE_DRIVE = } abort upload / download from Google Drive')
        return True

    logger.info(f'{hse_user_id = } Данные записи {item_number} успешно обновлены в google_disk!')
    return True
