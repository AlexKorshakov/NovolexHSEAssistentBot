from __future__ import annotations

from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup

from apps.core.bot.handlers.group.group_support_generate import notify_user_for_choice
from loader import logger

logger.debug(f"{__name__} start import")

import traceback
import asyncio
from datetime import datetime, timedelta, date
from pandas import DataFrame
from aiogram import types

from apps.MyBot import MyBot, bot_send_message
from apps.core.utils.misc import rate_limit
from apps.core.bot.bot_utils.check_access import (check_user_access,
                                                  check_admin_access,
                                                  check_super_user_access)
from apps.core.bot.data.board_config import BoardConfig as board_config
from apps.core.bot.messages.messages_test import Messages
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.database.query_constructor import QueryConstructor

from apps.core.database.db_utils import (db_get_period_for_current_week,
                                         db_get_username,
                                         db_get_data_list,
                                         db_get_clean_headers)

logger.debug(f"{__name__} finish import")


@rate_limit(limit=10)
# @MyBot.dp.message_handler(Command('group_generate_act'))
@MyBot.dp.callback_query_handler(posts_cb.filter(action=['group_generate_act']))
async def act_generate_handler(message: types.Message, state: FSMContext = None, user_id: str = None) -> None:
    """Запуск генерации акта - предписания

    :param user_id:
    :param state:
    :param message:
    :return:
    """
    hse_user_id = message.from_user.id

    if not await check_user_access(chat_id=hse_user_id):
        return

    main_reply_markup = types.InlineKeyboardMarkup()
    hse_role_df: DataFrame = await get_role_receive_df()

    if not await check_user_access(chat_id=hse_user_id, role_df=hse_role_df):
        logger.error(f'access fail {hse_user_id = }')
        return

    main_reply_markup = await add_period_inline_keyboard_with_action(main_reply_markup)

    if await check_admin_access(chat_id=hse_user_id, role_df=hse_role_df):
        main_reply_markup = await add_inline_keyboard_with_action_for_admin(main_reply_markup)

    if await check_super_user_access(chat_id=hse_user_id, role_df=hse_role_df):
        main_reply_markup = await add_inline_keyboard_with_action_for_super_user(main_reply_markup)

    await bot_send_message(chat_id=hse_user_id, text=Messages.Choose.period, reply_markup=main_reply_markup)


async def add_period_inline_keyboard_with_action(markup: types.InlineKeyboardMarkup):
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """
    markup.add(
            types.InlineKeyboardButton(
                    text='за сегодня',
                    callback_data=posts_cb.new(id='-', action='group_gen_act_today'))
    )
    markup.add(
            types.InlineKeyboardButton(
                    text='за сегодня и вчера',
                    callback_data=posts_cb.new(id='-', action='group_gen_act_today_and_previous'))
    )
    markup.add(
            types.InlineKeyboardButton(
                    text='за текущую неделю',
                    callback_data=posts_cb.new(id='-', action='group_gen_act_current_week'))
    )
    return markup


async def add_inline_keyboard_with_action_for_admin(markup: types.InlineKeyboardMarkup):
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """
    # markup.add(
    #     types.InlineKeyboardButton(
    #         text='Статистика',
    #         callback_data=posts_cb.new(id='-', action='group_generate_stat'))
    # )
    return markup


async def add_inline_keyboard_with_action_for_super_user(markup: types.InlineKeyboardMarkup):
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """
    # markup.add(types.InlineKeyboardButton(
    #     text='SU за текущую КН',
    #     callback_data=posts_cb.new(id='-', action='group_act_stat_current_week_all'))
    # )
    return markup


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['gen_act_today']), state='*')
async def call_gen_act_today(call: types.CallbackQuery, callback_data: dict[str, str], state: FSMContext = None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST

    :return:
    """
    chat_id: int = call.message.chat.id
    username: str = await db_get_username(user_id=chat_id)
    action: str = callback_data['action']

    if action != 'gen_act_today':
        return

    await notify_user_for_choice(call, data_answer=call.data)

    logger.info(f'User: @{username} user_id: {chat_id} choose {action} for generate act prescription')
    print(f'User: @{username} user_id: {chat_id} choose {action} for generate act prescription')

    await bot_send_message(chat_id=chat_id, text=f'{Messages.Report.start_act} \n {Messages.wait}')

    now = datetime.now()
    act_date_period: list = [now.strftime("%d.%m.%Y"), now.strftime("%d.%m.%Y"), ]
    logger.info(f"{chat_id = } {act_date_period = }")

    logger.info(f'User @{username}:{chat_id} generate act prescription')
    await board_config(state, "act_date_period", act_date_period).set_data()

    if await group_generate_and_send_act_prescription(chat_id=chat_id):
        logger.info(Messages.Report.acts_generated_successfully)


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['group_gen_act_today_and_previous']), state='*')
async def call_gen_act_today_and_previous(call: types.CallbackQuery, callback_data: dict[str, str],
                                          state: FSMContext = None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST

    :return:
    """
    chat_id: int = call.message.chat.id
    username: str = await db_get_username(user_id=chat_id)
    action: str = callback_data['action']

    if action != 'gen_act_today_and_previous':
        return

    await notify_user_for_choice(call, data_answer=call.data)

    logger.info(f'User: @{username} user_id: {chat_id} choose {action} for generate act prescription')
    print(f'User: @{username} user_id: {chat_id} choose {action} for generate act prescription')

    await bot_send_message(chat_id=chat_id, text=f'{Messages.Report.start_act} \n {Messages.wait}')

    now = datetime.now()
    previous = now - timedelta(days=1)
    act_date_period: list = [previous.strftime("%d.%m.%Y"), now.strftime("%d.%m.%Y"), ]
    logger.info(f"{chat_id = } {act_date_period = }")

    logger.info(f'User @{username}:{chat_id} generate act prescription')
    await board_config(state, "act_date_period", act_date_period).set_data()

    if await group_generate_and_send_act_prescription(chat_id=chat_id):
        logger.info(Messages.Report.acts_generated_successfully)


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['group_gen_act_current_week']), state='*')
async def call_gen_act_current_week(call: types.CallbackQuery, callback_data: dict[str, str], state: FSMContext = None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST

    :return:
    """
    chat_id: int = call.message.chat.id
    username: str = await db_get_username(user_id=chat_id)
    action: str = callback_data['action']

    if action != 'gen_act_current_week':
        return

    await notify_user_for_choice(call, data_answer=call.data)

    logger.info(f'User: @{username} user_id: {chat_id} choose {action} for generate act prescription')
    print(f'User: @{username} user_id: {chat_id} choose {action} for generate act prescription')

    await bot_send_message(chat_id=chat_id, text=f'{Messages.Report.start_act} \n {Messages.wait}')

    now = datetime.now()
    current_week: str = await get_week_message(current_date=now)
    current_year: str = await get_year_message(current_date=now)

    act_date_period = await db_get_period_for_current_week(current_week, current_year)
    logger.info(f"{chat_id = } {act_date_period = }")

    logger.info(f'User @{username}:{chat_id} generate act prescription')
    await board_config(state, "act_date_period", act_date_period).set_data()

    if await group_generate_and_send_act_prescription(chat_id=chat_id):
        logger.info(Messages.Report.acts_generated_successfully)


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


async def get_id_list(hse_user_id: str | int, user_role: str = None, hse_role_df: DataFrame = None) -> list:
    """Получение id"""

    if not await check_dataframe(hse_role_df, hse_user_id):
        hse_role_df: DataFrame = await get_role_receive_df()
        if not await check_dataframe(hse_role_df, hse_user_id):
            return []

    try:
        current_act_violations_df: DataFrame = hse_role_df.loc[
            hse_role_df[user_role] == 1]

    except Exception as err:
        logger.error(f"loc dataframe {repr(err)}")
        return []

    unique_hse_telegram_id: list = current_act_violations_df.hse_telegram_id.unique().tolist()
    if not unique_hse_telegram_id:
        return []

    return unique_hse_telegram_id


async def check_dataframe(dataframe: DataFrame, hse_user_id: str | int) -> bool:
    """Проверка dataframe на наличие данных

    :param dataframe:
    :param hse_user_id: id пользователя
    :return:
    """
    if dataframe is None:
        # text_violations: str = 'не удалось получить данные!'
        # logger.error(f'{hse_user_id = } {text_violations}')
        return False

    if dataframe.empty:
        logger.error(f'{hse_user_id = } {Messages.Error.dataframe_is_empty}')
        return False

    return True


async def get_week_message(current_date: datetime | str = None) -> str:
    """Обработчик сообщений с фото
    Получение номер str недели из сообщения в формате dd
    """
    current_date: date = await str_to_datetime(current_date)

    if not current_date:
        current_date: datetime = datetime.now()
    week = current_date.isocalendar()[1]
    return str("0" + str(week) if week < 10 else str(week))


async def get_year_message(current_date: datetime | str = None) -> str:
    """Обработчик сообщений с фото
    Получение полного пути файла
    """
    current_date: date = await str_to_datetime(current_date)

    if not current_date:
        current_date: datetime = datetime.now()

    return str(current_date.year)


async def str_to_datetime(date_str: str) -> date:
    """Преобразование str даты в datetime

    :param
    """

    current_date = None
    try:
        if isinstance(date_str, str):
            current_date: date = datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError as err:
        logger.error(f"{repr(err)}")

    return current_date


async def group_generate_and_send_act_prescription(chat_id: int) -> bool:
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
                    callback_data=posts_cb.new(id='-', action='group_generate_act_continue'))
    )
    return markup


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])


async def test():
    chat_id = 579531613
    now = datetime.now()
    # previous = now - timedelta(days=1)
    # act_date_period: list = [previous.strftime("%d.%m.%Y"), now.strftime("%d.%m.%Y"), ]
    # logger.info(f"{chat_id = } {act_date_period = }")

    act_date_period: list = [now.strftime("%d.%m.%Y"), now.strftime("%d.%m.%Y"), ]
    logger.info(f"{chat_id = } {act_date_period = }")

    if await group_generate_and_send_act_prescription(chat_id=chat_id):
        logger.info(Messages.Report.acts_generated_successfully)


if __name__ == "__main__":
    asyncio.run(test())
