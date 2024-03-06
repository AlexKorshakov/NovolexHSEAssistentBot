from __future__ import annotations

import os
import traceback
from datetime import datetime
from pprint import pprint

from aiogram import types
from aiogram.dispatcher import FSMContext
from pandas import DataFrame

from apps.core.bot.handlers.group.group_admin_create_report import create_act_prescription
from loader import logger
from apps.core.bot.messages.messages import Messages
from apps.core.database.query_constructor import QueryConstructor
from apps.MyBot import bot_send_message, MyBot, bot_send_document
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.handlers.group.group_support_path import (get_report_full_filepath,
                                                             create_file_path,
                                                             get_and_create_full_act_prescription_name)
from apps.core.bot.handlers.group.group_write_data import (db_get_data_list,
                                                           db_get_clean_headers,
                                                           db_check_data_exists)


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['group_generate_act_continue']), state='*')
async def group_generate_and_send_act_prescription_answer(call: types.CallbackQuery, user_id: int | str = None,
                                                          act_date_period=None, state: FSMContext = None, **kwargs) -> bool:
    """Формирование актов - предписаний за период query_act_date_period по организации

    :param call:
    :param state:
    :param act_date_period: list период (даты) для выборки
    :param user_id: id  пользователя
    :return:
    """
    user_id = call.message.chat.id if call else user_id
    await notify_user_for_choice(call, data_answer=call.data)

    v_data: dict = await state.get_data()
    await state.finish()

    # msg = await _send_message(chat_id=user_id, text='⬜' * 10)
    # p_bar = ProgressBar(msg=msg)

    # await p_bar.update_msg(1)
    act_kwargs = {**kwargs}
    if act_kwargs: logger.info(f"{act_kwargs = }")

    # await p_bar.update_msg(2)

    act_date_period = act_date_period if act_date_period else v_data.get('act_date_period', [])

    act_date: str = datetime.now().strftime("%d.%m.%Y")  # '28.10.2022'  #
    if not act_date_period:
        date_now = await format_data_db(act_date)
        act_date_period = [date_now, date_now]

    clean_headers: list = await db_get_clean_headers(table_name='violations')

    clear_list_value = await get_clean_data(
            user_id, period=act_date_period, headers=clean_headers
    )
    if not clear_list_value:
        return False

    # await p_bar.update_msg(3)
    general_constractor_ids_list: list = await get_general_constractor_list(clear_list_value=clear_list_value)
    if not general_constractor_ids_list:
        return False

    # await p_bar.update_msg(4)
    for constractor_id in general_constractor_ids_list:

        act_dataframe: DataFrame = await get_act_dataframe(
                chat_id=user_id, act_period=act_date_period, constractor_id=constractor_id, headers=clean_headers
        )
        if not await check_dataframe(act_dataframe, user_id):
            continue

        act_number: str = '00000'
        # act_number: int = await get_act_number_on_data_base()
        # if not act_number: act_number: str = '00000'

        full_act_prescription_path: str = await get_full_act_prescription_path(
                chat_id=user_id, act_number=act_number, act_date=act_date, constractor_id=constractor_id
        )
        # qr_report_path = await get_report_full_filepath(str(user_id), actual_date=act_date)
        #
        # await create_qr_code_with_param(user_id, act_number, qr_report_path)

        if not full_act_prescription_path:
            continue

        # await p_bar.update_msg(5)
        act_is_created: bool = await create_act_prescription(
                chat_id=user_id, act_number=act_number, dataframe=act_dataframe,
                full_act_path=full_act_prescription_path, act_date=act_date, qr_img_insert=True
        )
        if not act_is_created:
            continue

        # await p_bar.update_msg(6)
        await bot_send_message(chat_id=user_id, text=f'{Messages.Report.create_successfully} \n')

        # await set_act_data_on_data_base(
        #         act_data=act_dataframe, act_num=act_number, act_date=act_date
        # )
        # await p_bar.update_msg(7)
        # await set_act_data_on_google_drive(
        #         chat_id=user_id, full_report_path=full_act_prescription_path
        # )
        #
        # await p_bar.update_msg(8)
        # path_in_registry = await get_full_patch_to_act_prescription(
        #         chat_id=user_id, act_number=act_number, act_date=act_date, constractor_id=constractor_id
        # )
        #
        # await set_act_data_on_data_in_registry(
        #         hse_chat_id=user_id, act_dataframe=act_dataframe, path_in_registry=path_in_registry,
        #         act_date=act_date, act_number=act_number, constractor_id=constractor_id
        # )
        #
        # await p_bar.update_msg(9)
        await send_act_prescription(
                chat_id=user_id, full_act_prescription_path=full_act_prescription_path
        )

        # await p_bar.update_msg(10)
        await bot_send_message(chat_id=user_id, text=f'{Messages.Report.done} \n')

    return True


async def get_general_constractor_list(clear_list_value: list) -> list:
    """Получение списка get_general_constractor_list

    """
    general_constractor_list = [item_value.get('general_contractor_id') for item_value in clear_list_value]
    general_constractor_list = list(set(general_constractor_list))
    return general_constractor_list


async def get_full_act_prescription_path(chat_id, act_number, act_date, constractor_id) -> str:
    """Получение и создание полного пути акта предписания

    """
    contractor_data: dict = await get_general_constractor_data(
            constractor_id=constractor_id, type_constractor='general'
    )
    if not contractor_data:
        return ''

    param: dict = {
        'act_number': act_number,
        'act_date': act_date,
        'general_contractor': contractor_data.get('title'),
        'short_title': contractor_data.get('short_title'),
    }
    full_act_prescription_path: str = await get_and_create_full_act_prescription_name(chat_id=chat_id, param=param)
    return full_act_prescription_path


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


async def db_get_data_dict_from_table_with_id(table_name: str, post_id: int, query: str = None) -> dict:
    """Получение данных из table_name с помощью post_id

    :return: dict - dict с данными
    """
    check_result: bool = await get_check_param(__file__, await fanc_name(), table_name=table_name, post_id=post_id)
    if not check_result: return {}

    data_exists: dict = await db_check_data_exists(
        table_name=table_name, post_id=post_id, query=query
    )
    return data_exists


async def get_check_param(local_file: str, calling_function: str, **kvargs) -> bool:
    """Проверка параметров """
    calling_file: str = f'{os.sep}'.join(local_file.split(os.sep)[-2:])
    result_list: list = []
    print_dict: dict = {}

    for param_num, param in enumerate(kvargs, start=1):
        if kvargs[param] is None:
            logger.error(f'{calling_file} {calling_function} Invalid param. #{param_num} {param = } {kvargs[param]}')
        result_list.append(kvargs[param])
        print_dict[param] = kvargs[param]

    pprint(f'{await fanc_name()} :: {calling_function = } check_param: {print_dict}', width=200)
    return all(result_list)


async def get_act_dataframe(chat_id, act_period: list, constractor_id, headers):
    """Получение dataframe с данными акта - предписания

    :return:
    """
    table_name: str = 'violations'
    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "chat_id": chat_id,
            "general_contractor_id": constractor_id,
            'period': [await format_data_db(act_period[0]), await format_data_db(act_period[1])],

        },
    }
    query: str = await QueryConstructor(None, table_name, **query_kwargs).prepare_data()

    # TODO заменить на вызов конструктора QueryConstructor
    query: str = f'SELECT * ' \
                 f'FROM {table_name} ' \
                 f"AND `general_contractor_id` = {constractor_id} " \
                 f"AND `created_at` BETWEEN date('{await format_data_db(act_period[0])}') " \
                 f"AND date('{await format_data_db(act_period[1])}') " \
                 f"AND `user_id` = {chat_id}"

    act_dataframe: DataFrame = await create_lite_dataframe_from_query(
            chat_id=chat_id, query=query, clean_headers=headers
    )
    return act_dataframe


async def get_clean_data(chat_id, period, headers, **stat_kwargs):
    """Получение данных с заголовками за период query_act_date_period

    :return:
    """
    table_name: str = 'violations'
    kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "period": period,
            "act_number": "",
            "location": stat_kwargs.get('location', None)
        }
    }
    query: str = await QueryConstructor(chat_id, table_name=table_name, **kwargs).prepare_data()
    clear_list_value: list = await get_clear_list_value(
            chat_id=chat_id, query=query, clean_headers=headers
    )

    return clear_list_value


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


async def create_lite_dataframe_from_query(chat_id: int, query: str, clean_headers: list) -> DataFrame | None:
    """Формирование dataframe из запроса query и заголовков clean_headers

    :param chat_id: id  пользователя
    :param clean_headers: заголовки таблицы для формирования dataframe
    :param query: запрос в базу данных
    :return:
    """
    item_datas_query: list = await db_get_data_list(query=query)
    report_dataframe: DataFrame = await create_lite_dataframe(
            data_list=item_datas_query, header_list=clean_headers
    )
    if not await check_dataframe(report_dataframe, chat_id):
        return None

    return report_dataframe


async def create_lite_dataframe(data_list: list, header_list: list):
    """Создание dataframe

    :param header_list: список с заголовками
    :param data_list: список с данными
    """
    try:
        dataframe: DataFrame = DataFrame(data_list, columns=header_list)
        return dataframe

    except Exception as err:
        logger.error(f"create_dataframe {repr(err)}")
        return None


async def format_data_db(date_item: str):
    """ Форматирование даты в формат даты БВ
    """
    return datetime.strptime(date_item, "%d.%m.%Y").strftime("%Y-%m-%d")


async def check_dataframe(dataframe: DataFrame, hse_user_id: str | int) -> bool:
    """Проверка dataframe на наличие данных

    :param dataframe:
    :param hse_user_id: id пользователя
    :return:
    """
    if dataframe is None:
        logger.error(f'{hse_user_id = } {Messages.Error.dataframe_is_empty}')
        return False

    if dataframe.empty:
        logger.error(f'{hse_user_id = } {Messages.Error.dataframe_is_empty}')
        return False

    return True


async def notify_user_for_choice(call_msg: types.CallbackQuery | types.Message, user_id: int | str = None,
                                 data_answer: str = None) -> bool:
    """Уведомление пользователя о выборе + логирование

    :param data_answer:
    :param user_id: int | str id пользователя
    :param call_msg:
    :return None :
    """
    if isinstance(call_msg, types.CallbackQuery):
        for i in ('previous_paragraph', 'move_up', 'move_down'):
            if i in call_msg.data: return True

        mesg_text: str = f"Выбрано: {data_answer}"
        if call_msg.data in call_msg.message.text:
            mesg_list: list = [item for item in call_msg.message.text.split('\n\n') if call_msg.data in item]
            mesg_text = f"Выбрано: {mesg_list[0]}"

        try:
            hse_user_id = call_msg.message.chat.id if call_msg else user_id
            logger.debug(f"{hse_user_id = } Выбрано: {data_answer} {call_msg.data}")
            await call_msg.message.edit_text(text=mesg_text, reply_markup=None)
            return True

        except Exception as err:
            logger.debug(f"{call_msg.message.chat.id = } {repr(err)}")

    if isinstance(call_msg, types.Message):
        for i in ('previous_paragraph', 'move_up', 'move_down'):
            if i in call_msg.text: return True

        mesg_text: str = f"Выбрано: {data_answer}"
        if call_msg.text:
            mesg_list: list = [item for item in call_msg.text.split('\n\n') if call_msg.text in item]
            mesg_text = f"Выбрано: {mesg_list[0] if mesg_list else ''}"

        try:
            hse_user_id = call_msg.chat.id if call_msg else user_id
            logger.debug(f"{hse_user_id = } Выбрано: {data_answer} {call_msg.text}")
            await call_msg.edit_text(text=mesg_text, reply_markup=None)
            return True

        except Exception as err:
            logger.debug(f"{call_msg.chat.id = } {repr(err)}")


async def send_act_prescription(chat_id: int or str, full_act_prescription_path: str) -> bool:
    """Отправка акта-предписания пользователю в заданных форматах

    :param full_act_prescription_path: int or str
    :param chat_id: str
    :return:
    """
    # await convert_report_to_pdf( chat_id=chat_id, path=full_act_prescription_path)
    await send_report_from_user(
            chat_id=chat_id, full_report_path=full_act_prescription_path
    )
    # full_act_prescription_path = full_act_prescription_path.replace(".xlsx", ".pdf")
    # await send_report_from_user(chat_id=chat_id, full_report_path=full_act_prescription_path)
    return True


async def send_report_from_user(chat_id, full_report_path=None):
    """Отправка пользователю сообщения с готовым отчетом
    """
    if not full_report_path:
        report_name = f'МИП Отчет за {(datetime.now()).strftime("%d.%m.%Y")}.xlsx'
        report_path = await get_report_full_filepath(str(chat_id))

        await create_file_path(report_path)
        full_report_path = f'{report_path}{os.sep}{report_name}'

    caption = 'Отчет собран с помощью бота!'
    await bot_send_document(
            chat_id=chat_id, doc_path=full_report_path, caption=caption, calling_fanc_name=await fanc_name()
    )


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])
