from __future__ import annotations

import datetime
import io
import json
import os
import traceback

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup
from pandas import DataFrame

from apps.core.bot.data.board_config import BoardConfig as board_config
from apps.core.bot.reports.report_data import ViolationData
from loader import logger
from apps.MyBot import MyBot, bot_send_document, bot_send_message, _send_message
from apps.core.database.query_constructor import QueryConstructor
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.bot_utils.progress_bar import ProgressBar
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages import Messages
from apps.core.bot.handlers.photo.AmazingQRCodeGenerator import create_qr_code_with_param
from apps.core.bot.handlers.generate.generate_support import set_act_data_on_google_drive
from apps.core.bot.handlers.generate.generate_support_paths import (create_file_path,
                                                                    get_report_full_filepath_in_registry,
                                                                    get_report_full_name,
                                                                    get_full_act_prescription_path,
                                                                    get_report_full_filepath)
from apps.core.database.db_utils import (db_get_max_number,
                                         db_set_act_value,
                                         db_update_column_value,
                                         db_get_dict_userdata,
                                         db_get_data_dict_from_table_with_id,
                                         db_get_data_list,
                                         db_get_clean_headers)

from apps.core.bot.handlers.generate.generate_act_prescription import create_act_prescription


async def generate_and_send_act_prescription(chat_id: int) -> bool:
    """Формирование актов - предписаний за период query_act_date_period по организации

    :param chat_id: id  пользователя
    :return:
    """
    hse_role_df: DataFrame = await get_role_receive_df()

    if not await check_user_access(chat_id=chat_id, role_df=hse_role_df):
        logger.error(f'access fail {chat_id = }')
        return False

    main_reply_markup = InlineKeyboardMarkup()
    main_reply_markup = await add_inline_keyboard_with_action(main_reply_markup)

    await bot_send_message(chat_id=chat_id, text=Messages.Choose.action, reply_markup=main_reply_markup)


async def add_inline_keyboard_with_action(markup: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """
    # markup.add(
    #     types.InlineKeyboardButton(
    #         text='Добавить номер акта',
    #         callback_data=posts_cb.new(id='-', action='generate_act_add_act_number')
    #     )
    # )
    markup.add(
        types.InlineKeyboardButton(
            text='Продолжить',
            callback_data=posts_cb.new(id='-', action='generate_act_continue'))
    )
    return markup


async def get_role_receive_df() -> DataFrame | None:
    """Получение df с ролями пользователя

    :return:
    """

    db_table_name: str = 'core_hseuser'
    kwargs: dict = {
        "action": 'SELECT',
        "subject": '*',
    }
    query: str = await QueryConstructor(table_name=db_table_name, **kwargs).prepare_data()
    datas_query: list = await db_get_data_list(query=query)
    if not datas_query:
        return None

    if not isinstance(datas_query, list):
        return None

    clean_headers: list = await db_get_clean_headers(table_name=db_table_name)
    if not clean_headers:
        return None

    try:
        hse_role_receive_df: DataFrame = DataFrame(datas_query, columns=clean_headers)

    except Exception as err:
        logger.error(f"create_dataframe {repr(err)}")
        return None

    return hse_role_receive_df


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['generate_act_add_act_number']), state='*')
async def generate_and_send_act_prescription_answer(call: types.CallbackQuery, user_id: int | str = None,
                                                    state: FSMContext = None, **kwargs) -> bool:
    """Формирование актов - предписаний за период query_act_date_period по организации

    :param call:
    :param state:
    :param user_id: id  пользователя
    :return:
    """

    hse_user_id = call.message.chat.id if call else user_id
    await notify_user_for_choice(call, data_answer=call.data)

    await state.finish()

    await notify_user_for_choice(call, data_answer=call.data)

    await ViolationData.add_act_number.set()
    await bot_send_message(chat_id=hse_user_id, text="Загрузите фотографии из галереи",
                           disable_web_page_preview=True)


@MyBot.dp.message_handler(content_types=types.ContentType.TEXT, state=ViolationData.add_act_number)
async def handler_albums(message: types.Message, callback_data: dict = None,
                         user_id: int | str = None, state: FSMContext = None):
    """This handler will receive a complete album of any type

    """

    hse_user_id = message.chat.id if message else user_id
    add_act_number = message.text

    await board_config(state, "add_act_number", add_act_number).set_data()

    main_reply_markup = InlineKeyboardMarkup()
    reply_markup = await add_inline_keyboard_with_action(main_reply_markup)
    await bot_send_message(chat_id=hse_user_id, text=Messages.Choose.action, reply_markup=reply_markup)


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['generate_act_continue']), state='*')
async def generate_and_send_act_prescription_answer(call: types.CallbackQuery, user_id: int | str = None,
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

    msg = await _send_message(chat_id=user_id, text='⬜' * 10)
    p_bar = ProgressBar(msg=msg)

    await p_bar.update_msg(1)
    act_kwargs = {**kwargs}
    if act_kwargs:
        logger.info(f"{act_kwargs = }")

    await p_bar.update_msg(2)

    act_date_period = act_date_period if act_date_period else v_data.get('act_date_period', [])

    act_date: str = datetime.datetime.now().strftime("%d.%m.%Y")  # '28.10.2022'  #
    if not act_date_period:
        date_now = await format_data_db(act_date)
        act_date_period = [date_now, date_now]

    clean_headers: list = await db_get_clean_headers(table_name='core_violations')

    clear_list_value = await get_clean_data(
        user_id, period=act_date_period, headers=clean_headers
    )
    if not clear_list_value:
        return False

    await p_bar.update_msg(3)
    general_constractor_ids_list: list = await get_general_constractor_list(clear_list_value=clear_list_value)
    if not general_constractor_ids_list:
        return False

    await p_bar.update_msg(4)
    for constractor_id in general_constractor_ids_list:

        act_dataframe: DataFrame = await get_act_dataframe(
            chat_id=user_id, act_period=act_date_period, constractor_id=constractor_id, headers=clean_headers
        )
        if not await check_dataframe(act_dataframe, user_id):
            continue

        act_number: int = await get_act_number_on_data_base()
        if not act_number:
            act_number: str = '00000'

        full_act_prescription_path: str = await get_full_act_prescription_path(
            chat_id=user_id, act_number=act_number, act_date=act_date, constractor_id=constractor_id
        )
        qr_report_path = await get_report_full_filepath(str(user_id), actual_date=act_date)

        await create_qr_code_with_param(user_id, act_number, qr_report_path)

        if not full_act_prescription_path:
            continue

        await p_bar.update_msg(5)
        act_is_created: bool = await create_act_prescription(
            chat_id=user_id, act_number=act_number, dataframe=act_dataframe,
            full_act_path=full_act_prescription_path, act_date=act_date, qr_img_insert=True
        )
        if not act_is_created:
            continue

        await p_bar.update_msg(6)
        await bot_send_message(chat_id=user_id, text=f'{Messages.Report.create_successfully} \n')

        await set_act_data_on_data_base(
            act_data=act_dataframe, act_num=act_number, act_date=act_date
        )
        await p_bar.update_msg(7)
        await set_act_data_on_google_drive(
            chat_id=user_id, full_report_path=full_act_prescription_path
        )

        await p_bar.update_msg(8)
        path_in_registry = await get_full_patch_to_act_prescription(
            chat_id=user_id, act_number=act_number, act_date=act_date, constractor_id=constractor_id
        )

        await set_act_data_on_data_in_registry(
            hse_chat_id=user_id, act_dataframe=act_dataframe, path_in_registry=path_in_registry,
            act_date=act_date, act_number=act_number, constractor_id=constractor_id
        )

        await p_bar.update_msg(9)
        await send_act_prescription(
            chat_id=user_id, full_act_prescription_path=full_act_prescription_path
        )

        await p_bar.update_msg(10)
        await bot_send_message(chat_id=user_id, text=f'{Messages.Report.done} \n')

    return True


async def get_act_number_on_data_base() -> int:
    """Получение номера акта из Database `core_reestr_acts`

    :return: int act_num: номер акта - предписания
    """
    act_num: int = await db_get_max_number() + 1
    return act_num


async def set_act_data_on_data_base(act_data: DataFrame, act_num: int, act_date: str) -> bool:
    """Запись данных в Database `core_reestreacts` и дополнение данных в `core_violations` ели был оформлен акт

    :param act_data: DataFrame
    :param act_num: int
    :param act_date: str
    :return: bool
    """
    act_is_created: bool = await db_set_act_value(
        act_data_dict=act_data, act_number=act_num, act_date=act_date
    )
    if not act_is_created:
        return False

    for act_id in act_data.id:
        await db_update_column_value(
            column_name='act_number', value=str(act_num), violation_id=act_id
        )
    return True


async def send_report_from_user(chat_id, full_report_path=None):
    """Отправка пользователю сообщения с готовым отчетом
    """

    if not full_report_path:
        report_name = f'МИП Отчет за {(datetime.datetime.now()).strftime("%d.%m.%Y")}.xlsx'
        report_path = await get_report_full_filepath(str(chat_id))
        await create_file_path(report_path)
        full_report_path = report_path + report_name

    caption = 'Отчет собран с помощью бота!'
    await bot_send_document(
        chat_id=chat_id, doc_path=full_report_path, caption=caption, calling_fanc_name=await fanc_name()
    )


async def get_clean_data(chat_id, period, headers, **stat_kwargs):
    """Получение данных с заголовками за период query_act_date_period

    :return:
    """
    kwargs: dict = {
        "action": 'SELECT',
        "subject": '*',
        "conditions": {
            "period": period,
            "act_number": "",
            "location": stat_kwargs.get('location', None)
        }
    }
    query: str = await QueryConstructor(chat_id, table_name='core_violations', **kwargs).prepare_data()
    clear_list_value: list = await get_clear_list_value(
        chat_id=chat_id, query=query, clean_headers=headers
    )

    return clear_list_value


async def get_and_create_full_act_prescription_name_in_registry(chat_id: int, param: dict) -> str:
    """Формирование и получение полного имение пути к акту  в реестре (хранилище)

    :param param:
    :param chat_id:
    :return:
    """
    if not param:
        return ''

    act_number = param.get('act_number', None)
    if not act_number:
        act_number = (datetime.datetime.now()).strftime("%d.%m.%Y")

    act_date = param.get('act_date', None)
    if not act_date:
        act_date = (datetime.datetime.now()).strftime("%d.%m.%Y")

    short_title = param.get('short_title', None)
    if not short_title:
        short_title = ''

    # main_location = param.get('main_location', '')

    try:
        report_full_name = f'Акт-предписание № {act_number} от {act_date} {short_title}'
        report_path_in_registry = await get_report_full_filepath_in_registry(chat_id, actual_date=act_date)
        await create_file_path(report_path_in_registry)
        full_report_path_in_registry: str = await get_report_full_name(report_path_in_registry, report_full_name)
        await create_file_path(full_report_path_in_registry)

        return full_report_path_in_registry

    except Exception as err:
        logger.error(f"get_report_path {repr(err)}")
        return ''


async def set_act_data_on_data_in_registry(
        hse_chat_id, act_dataframe, act_date, act_number, path_in_registry, constractor_id) -> None:
    """Сoхранение данных отчета различными методами"""

    result: bool = await set_act_prescription_json(
        hse_chat_id=hse_chat_id, act_dataframe=act_dataframe, path_in_registry=path_in_registry,
        act_date=act_date, act_number=act_number, constractor_id=constractor_id)

    if result:
        await bot_send_message(chat_id=hse_chat_id, text=Messages.Successfully.registration_completed_in_registry)
    else:
        await bot_send_message(chat_id=hse_chat_id, text=Messages.Error.entry_in_registry_fail)


async def set_json_act_prescription_in_registry(full_patch: str, json_name: str,
                                                json_data: dict | str | list | tuple) -> bool:
    """

    :param json_data:
    :param json_name:
    :param full_patch:
    :return:
    """
    with open(f'{full_patch}\\{json_name}', 'w') as json_file:
        json_file.write(json_data)

    return True


async def set_act_prescription_json(hse_chat_id: str | int, act_dataframe: DataFrame, act_number: str | int,
                                    path_in_registry: str, constractor_id: str | int, act_date: str) -> bool:
    """Формирование json-файла со ВСЕМИ данными акта - предписания

    :return:
    """
    act_data_dict: dict = {}
    item_list = []

    unique_id = act_dataframe.id.unique().tolist()

    v_index = 0
    for v_index, v_id, in enumerate(unique_id, start=1):
        item_v_df = act_dataframe.copy(deep=True)
        item_df = item_v_df.loc[item_v_df['id'] == v_id]

        if item_v_df.empty:
            continue

        item_data_dict = {}
        for (key, value) in item_df.items():
            if value.values.dtype == 'int64':
                value = value.values[0].item()
                item_data_dict[key] = value
            else:
                item_data_dict[key] = value.get(v_index - 1, None)

        item_list.append(
            {item_data_dict['id']: item_data_dict}
        )

    hse_userdata: dict = await db_get_dict_userdata(hse_chat_id)
    hse_organization_id = hse_userdata.get('hse_organization')

    hse_organization_dict: dict = await db_get_data_dict_from_table_with_id(
        table_name='core_generalcontractor', post_id=hse_organization_id)

    contractor: dict = await db_get_data_dict_from_table_with_id(
        table_name='core_generalcontractor', post_id=constractor_id)

    act_data_dict['violations'] = [
        {'violations_items': item_list},
        {'violations_index': v_index},
    ]

    act_data_dict['contractor'] = contractor
    act_data_dict['hse_userdata'] = hse_userdata
    act_data_dict['hse_organization'] = hse_organization_dict

    # TODO Дополнить заголовками и пр.

    contractor_data: dict = await get_general_constractor_data(
        constractor_id=constractor_id, type_constractor='general'
    )
    if not contractor_data:
        return False

    short_title = contractor_data.get('short_title')

    report_full_name = f'Акт-предписание № {act_number} от {act_date} {short_title}.json'
    full_patch_to_act_prescription_json = f"{path_in_registry}{os.sep}{report_full_name}"

    result: bool = await write_json_file(data=act_data_dict, name=full_patch_to_act_prescription_json)

    return result


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


async def get_act_dataframe(chat_id, act_period: list, constractor_id, headers) -> DataFrame | None:
    """Получение dataframe с данными акта - предписания

    :return:
    """
    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "general_contractor_id": constractor_id,
            'user_id': chat_id,
            "act_number": "",
            'period': [await format_data_db(act_period[0]), await format_data_db(act_period[1])]
        },
    }
    query: str = await QueryConstructor(None, 'core_violations', **query_kwargs).prepare_data()

    act_dataframe: DataFrame = await create_lite_dataframe_from_query(
        chat_id=chat_id, query=query, clean_headers=headers
    )
    return act_dataframe


async def create_lite_dataframe_from_query(chat_id: int, query: str, clean_headers: list) -> DataFrame | None:
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

    if not await check_dataframe(report_dataframe, chat_id):
        return None

    return report_dataframe


async def create_lite_dataframe(chat_id, data_list: list, header_list: list) -> DataFrame | None:
    """Создание dataframe

    :param chat_id:
    :param header_list: список с заголовками
    :param data_list: список с данными
    """
    try:
        dataframe: DataFrame = DataFrame(data_list, columns=header_list)
        return dataframe

    except Exception as err:
        return None


async def write_json_file(*, data: dict | str = None, name: str = None) -> bool:
    """Запись данных в json

    :param name: полный путь к файлу
    :param data: dict  с данными для записи
    """

    result: bool = await write_json(name=name, data=data)
    return result


async def write_json(name: str, data) -> bool:
    """Запись данных в json

    :param name: полный путь для записи / сохранения файла включая расширение,
    :param data: данные для записи / сохранения
    :return: True or False
    """
    try:
        with io.open(name, 'w', encoding='utf8') as outfile:
            str_ = json.dumps(data,
                              indent=4,
                              sort_keys=True,
                              separators=(',', ': '),
                              ensure_ascii=False)
            outfile.write(str_)
            return True
    except TypeError as err:
        logger.error(f"TypeError: {repr(err)}")
        return False


async def get_full_patch_to_act_prescription(chat_id, act_number, act_date, constractor_id) -> str:
    """Формирование полного пути до папки хранения файла json акта - предписания

    :return:
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
        'contractor_data': contractor_data,
    }
    full_act_prescription_path: str = await get_and_create_full_act_prescription_name_in_registry(
        chat_id=chat_id, param=param
    )

    return full_act_prescription_path


async def send_act_prescription(chat_id: int or str, full_act_prescription_path: str) -> bool:
    """Отправка акта-предписания пользователю в заданных форматах

    :param full_act_prescription_path: int or str
    :param chat_id: str
    :return:
    """

    # await convert_report_to_pdf(
    #     chat_id=chat_id, path=full_act_prescription_path
    # )
    await send_report_from_user(
        chat_id=chat_id, full_report_path=full_act_prescription_path
    )
    # full_act_prescription_path = full_act_prescription_path.replace(".xlsx", ".pdf")
    #
    # await send_report_from_user(
    #     chat_id=chat_id, full_report_path=full_act_prescription_path
    # )
    return True


async def check_dataframe(dataframe: DataFrame, hse_user_id: str | int) -> bool:
    """Проверка dataframe на наличие данных

    :param dataframe:
    :param hse_user_id: id пользователя
    :return:
    """
    if dataframe is None:
        text_violations: str = 'не удалось получить данные!'
        logger.error(f'{hse_user_id = } {text_violations}')
        # await bot_send_message(chat_id=hse_user_id, text=text_violations)
        return False

    if dataframe.empty:
        logger.error(f'{hse_user_id = } {Messages.Error.dataframe_is_empty}')
        return False

    return True


async def get_general_constractor_list(clear_list_value: list) -> list:
    """Получение списка get_general_constractor_list

    """
    general_constractor_list = [item_value.get('general_contractor_id') for item_value in clear_list_value]
    general_constractor_list = list(set(general_constractor_list))

    return general_constractor_list


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


async def format_data_db(date_item: str):
    """ Форматирование даты в формат даты БВ
    """
    return datetime.datetime.strptime(date_item, "%d.%m.%Y").strftime("%Y-%m-%d")


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])


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
        if call_msg.text in call_msg.text:
            mesg_list: list = [item for item in call_msg.text.split('\n\n') if call_msg.text in item]
            mesg_text = f"Выбрано: {mesg_list[0] if mesg_list else ''}"

        try:
            hse_user_id = call_msg.chat.id if call_msg else user_id
            logger.debug(f"{hse_user_id = } Выбрано: {data_answer} {call_msg.text}")
            await call_msg.edit_text(text=mesg_text, reply_markup=None)
            return True

        except Exception as err:
            logger.debug(f"{call_msg.chat.id = } {repr(err)}")
