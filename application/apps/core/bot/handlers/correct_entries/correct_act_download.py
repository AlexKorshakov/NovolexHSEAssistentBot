from __future__ import annotations

import asyncio
import os
import traceback
from datetime import datetime

from aiogram import types
from pandas import DataFrame

from apps.MyBot import MyBot, bot_send_message, bot_send_document
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.handlers.correct_entries.correct_support_path import get_full_act_prescription_path
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages import Messages, LogMessage
from apps.core.database.db_utils import (db_get_data_list,
                                         db_get_clean_headers,
                                         db_get_data_dict_from_table_with_id)
from apps.core.database.query_constructor import QueryConstructor
from loader import logger


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['correct_act_download']))
async def call_correct_act_download(call: types.CallbackQuery = None, callback_data: dict[str, str] = None,
                                    user_id: int | str = None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST
    """

    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {callback_data = }')

    # await bot_delete_markup(message=call.message)

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    if not call:
        await bot_send_message(chat_id=hse_user_id, text=Messages.Error.error_call)
        return

    if not call.message.values['text']:
        await bot_send_message(chat_id=hse_user_id, text=Messages.Error.error_call_text)
        return

    act_number_text = call.message.values['text'].split('_')[-1].split(' ')[-1]
    logger.debug(f'{hse_user_id = } {act_number_text = }')

    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "act_number": act_number_text,
        },
    }
    table_name: str = 'core_actsprescriptions'

    query: str = await QueryConstructor(None, table_name, **query_kwargs).prepare_data()

    act_dataframe: DataFrame = await create_lite_dataframe_from_query(query=query, table_name=table_name)
    if act_dataframe.empty:
        logger.error(f'{hse_user_id = } {Messages.Error.dataframe_is_empty}  \n{query = }')
        return

    act_number: str = act_dataframe.act_number.values[0]
    act_date: str = act_dataframe.act_date.values[0]
    act_constractor_id: int = act_dataframe.act_general_contractor_id.values[0]

    contractor_data: dict = await db_get_data_dict_from_table_with_id(
        table_name='core_generalcontractor',
        post_id=act_constractor_id
    )
    short_title = contractor_data.get('short_title')

    full_act_prescription_path: str = await get_full_act_prescription_path(
        chat_id=hse_user_id, act_number=act_number, act_date=act_date, short_title=short_title
    )

    if not full_act_prescription_path:
        logger.error(f'{hse_user_id = } {Messages.Error.act_prescription_path_not_found}')
        await bot_send_message(chat_id=hse_user_id, text=Messages.Error.act_prescription_path_not_found)
        return False

    if os.path.isfile(full_act_prescription_path):
        logger.error(f'{hse_user_id = } {Messages.Error.act_prescription_path_not_found}')
        await bot_send_message(chat_id=hse_user_id, text=Messages.Error.act_prescription_path_not_found)
        return False

    await send_act_prescription(
        hse_user_id=hse_user_id, full_act_prescription_path=full_act_prescription_path
    )


# async def get_full_act_prescription_path(hse_user_id, act_number, act_date, short_title) -> str:
#     """Получение и создание полного пути акта предписания
#
#     """
#     act_prescription_full_name: str = f'{Udocan_media_path}\\HSE\\{hse_user_id}\\data_file\\{act_date}\\reports\\Акт-предписание № ' \
#                                       f'{act_number} от {act_date} {short_title}'
#     return act_prescription_full_name


async def send_act_prescription(hse_user_id: int or str, full_act_prescription_path: str) -> bool:
    """Отправка акта-предписания пользователю в заданных форматах

    :param full_act_prescription_path: int or str
    :param hse_user_id: str id пользователя
    :return:
    """

    if not full_act_prescription_path:
        logger.error(f'{hse_user_id = } {Messages.Error.act_prescription_path_not_found}')
        await bot_send_message(chat_id=hse_user_id, text=Messages.Error.act_prescription_path_not_found)
        return False

    if os.path.isfile(full_act_prescription_path):
        logger.error(f'{hse_user_id = } {Messages.Error.act_prescription_path_not_found}')
        await bot_send_message(chat_id=hse_user_id, text=Messages.Error.act_prescription_path_not_found)
        return False

    # full_act_prescription_path = full_act_prescription_path.replace(".xlsx", ".pdf")

    result: bool = await send_act_from_user(
        hse_user_id=hse_user_id, full_report_path=full_act_prescription_path
    )
    return result


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


async def send_act_from_user(hse_user_id: int | str, full_report_path: str = None, act_name: str = None) -> bool:
    """Отправка пользователю сообщения с готовым отчетом
    """

    if not full_report_path:
        logger.error(f'{hse_user_id = } {Messages.Error.act_prescription_path_not_found}')
        await bot_send_message(chat_id=hse_user_id, text=Messages.Error.act_prescription_path_not_found)
        return False

    if os.path.isfile(full_report_path):
        logger.error(f'{hse_user_id = } {Messages.Error.act_prescription_path_not_found}')
        await bot_send_message(chat_id=hse_user_id, text=Messages.Error.act_prescription_path_not_found)
        return False

    caption = None
    if act_name:
        caption = f'Отправлен отчет {act_name}'

    await bot_send_document(
        chat_id=hse_user_id, doc_path=f'{full_report_path} .pdf', caption=caption, calling_fanc_name=await fanc_name()
    )


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])


async def get_now() -> str:
    """Возвращает текущую дату и время.
    :return: str
    """
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")


async def test():
    hse_user_id = 373084462
    full_report_path: str = ''
    act_name: str = ''

    result: bool = await send_act_from_user(hse_user_id, full_report_path, act_name)


if __name__ == '__main__':
    asyncio.run(test())
