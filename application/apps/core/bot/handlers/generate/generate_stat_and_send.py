from __future__ import annotations

import datetime
import traceback

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup

from apps.core.bot.bot_utils.progress_bar import ProgressBar
# from apps.core.bot.handlers.generate.generate_statistic import create_stat
from apps.core.bot.handlers.generate.generate_support_paths import get_report_full_filepath, create_file_path
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages import Messages
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.database.db_utils import (db_get_dict_userdata,
                                         db_get_data_dict_from_table_with_id,
                                         db_get_data_list,
                                         db_get_clean_headers)
from apps.core.database.query_constructor import QueryConstructor

from apps.core.utils.reports_processor.report_worker_utils import (create_lite_dataframe_from_query,
                                                                   format_data_db,
                                                                   get_clean_headers)

from apps.MyBot import bot_send_message, MyBot, _send_message, bot_send_document
from loader import logger
from pandas import DataFrame


async def create_and_send_stat(chat_id, query_period: [list, str] = None, **stat_kwargs) -> bool:
    """Формирование и отправка отчета

    :param query_period:
    :param chat_id:
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
    markup.add(
        types.InlineKeyboardButton(
            text='Добавить номер акта',
            callback_data=posts_cb.new(id='-', action='generate_stat_add_act_number')
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            text='Продолжить',
            callback_data=posts_cb.new(id='-', action='generate_stat_continue'))
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


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['generate_act_continue']), state='*')
async def create_and_send_stat_answer(call: types.CallbackQuery, user_id: int | str = None,
                                      stat_date_period=None, state: FSMContext = None, **stat_kwargs) -> bool:
    """Формирование и отправка отчета

    :param user_id:
    :param state:
    :param call:
    :param stat_date_period:

    :return:
    """
    user_id = call.message.chat.id if call else user_id
    await notify_user_for_choice(call, data_answer=call.data)

    v_data: dict = await state.get_data()
    await state.finish()

    msg = await _send_message(chat_id=user_id, text='⬜' * 10)
    p_bar = ProgressBar(msg=msg)

    await p_bar.update_msg(1)
    act_kwargs = {**stat_kwargs}
    if act_kwargs:
        logger.info(f"{act_kwargs = }")

    stat_date_period = stat_date_period if stat_date_period else v_data.get('stat_date_period', [])
    if not stat_date_period:
        stat_date: str = datetime.datetime.now().strftime("%d.%m.%Y")  # '28.10.2022'  #
        stat_date_period = await format_data_db(stat_date)

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
            "period": stat_date_period,
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

    query: str = await QueryConstructor(user_id, table_name='core_violations', **kwargs).prepare_data()
    print(f'get_stat_dataframe {query = }')

    stat_dataframe: DataFrame = await get_stat_dataframe_with_query(
        user_id, query=query, header_list=clean_headers,
    )

    if stat_dataframe.empty:
        logger.error(Messages.Error.dataframe_not_found)
        await bot_send_message(chat_id=user_id, text=Messages.Error.dataframe_not_found)
        return False

    full_stat_path: str = await get_full_stat_name(chat_id=user_id)

    # stat_is_created: bool = await create_stat(
    #     chat_id=user_id,
    #     dataframe=stat_dataframe,
    #     full_stat_path=full_stat_path,
    #     query_period=stat_date_period
    # )

    # if not stat_is_created:
    #     return False

    await bot_send_message(chat_id=user_id, text=f'{Messages.Report.done} \n')

    await send_stat(chat_id=user_id, full_report_path=full_stat_path)

    return True


async def get_stat_dataframe_with_query(chat_id, query: str, header_list: list = None):
    """Получение dataframe с данными статистики

    :return:
    """

    stat_dataframe: DataFrame = await create_lite_dataframe_from_query(
        chat_id=chat_id, query=query, clean_headers=header_list
    )
    return stat_dataframe


async def get_full_stat_name(chat_id: int):
    """Получение полного пути к отчету со статистикой

    :param chat_id:
    :return: полный путь к файлу с отчетом
    """
    now: str = (datetime.datetime.now()).strftime("%d.%m.%Y")
    userdata: dict = await db_get_dict_userdata(chat_id)
    location_id: int = int(userdata.get('hse_location', ''))

    location = await db_get_data_dict_from_table_with_id(
        table_name='core_location',
        post_id=location_id
    )
    location = location.get('title', '')

    try:
        report_full_name = f'СТАТ-ОТ_ПБ_ПТ-{location} {now}.xlsx'
        report_path = await get_report_full_filepath(str(chat_id))
        await create_file_path(report_path)
        return report_path + report_full_name

    except Exception as err:
        logger.error(f"get_report_path {repr(err)}")
        return ''


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
