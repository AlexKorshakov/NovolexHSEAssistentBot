from __future__ import annotations

from datetime import datetime, timedelta
import asyncio

from aiogram import types

from apps.MyBot import MyBot, bot_send_message
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.handlers.bagration.bagration_utils import get_pass_report, get_week_message, get_month_message, \
    get_year_message, db_get_period_for_current_week, db_get_period_for_current_month
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages import Messages
from apps.core.bot.messages.messages_test import msg
from apps.core.settyngs import get_sett
from loader import logger


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['bagration_admin_get_pass_report']))
async def call_bagration_admin_get_pass_report(call: types.CallbackQuery = None, callback_data: dict = None,
                                               user_id: int | str = None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST
    """

    hse_user_id = call.message.chat.id if call else user_id
    if call: logger.debug(f'{hse_user_id = } {call.data = }')

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    if not get_sett(cat='enable_features', param='use_bagration_admin_get_pass_report').get_set():
        msg_text: str = f"{await msg(hse_user_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=hse_user_id, text=msg_text, disable_web_page_preview=True)
        return

    reply_markup = await add_correct_inline_keyboard_with_action()
    msg_text: str = 'Выберите действие'
    await bot_send_message(chat_id=hse_user_id, text=msg_text, reply_markup=reply_markup)


async def add_correct_inline_keyboard_with_action(markup: types.InlineKeyboardMarkup = None):
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """
    if not markup:
        markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(
        'За сегодня',
        callback_data=posts_cb.new(id='-', action='use_bagration_admin_get_pass_report_today'))
    )
    markup.add(types.InlineKeyboardButton(
        'За сегодня и вчера',
        callback_data=posts_cb.new(id='-', action='use_bagration_admin_get_pass_report_today_and_yesterday'))
    )
    markup.add(types.InlineKeyboardButton(
        'За текущую неделю',
        callback_data=posts_cb.new(id='-', action='use_bagration_admin_get_pass_report_week'))
    )
    markup.add(types.InlineKeyboardButton(
        'За текущий месяц',
        callback_data=posts_cb.new(id='-', action='use_bagration_admin_get_pass_report_month'))
    )
    markup.add(types.InlineKeyboardButton(
        'За весь период',
        callback_data=posts_cb.new(id='-', action='use_bagration_admin_get_pass_report_all'))
    )
    return markup


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['use_bagration_admin_get_pass_report_today']))
async def call_bagration_admin_get_pass_report(call: types.CallbackQuery = None, callback_data: dict = None,
                                               user_id: int | str = None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST
    """

    hse_user_id = call.message.chat.id if call else user_id
    if call: logger.debug(f'{hse_user_id = } {call.data = }')

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    now = datetime.now()
    period: list = [now.strftime("%d.%m.%Y"), now.strftime("%d.%m.%Y"), ]
    logger.info(f"{hse_user_id = } {period = }")

    await get_pass_report(hse_user_id, period)


@MyBot.dp.callback_query_handler(
    posts_cb.filter(action=['use_bagration_admin_get_pass_report_today_and_yesterday']))
async def call_bagration_admin_get_pass_report(call: types.CallbackQuery = None, callback_data: dict = None,
                                               user_id: int | str = None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST
    """

    hse_user_id = call.message.chat.id if call else user_id
    if call: logger.debug(f'{hse_user_id = } {call.data = }')

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    now = datetime.now()
    previous = now - timedelta(days=1)
    period: list = [previous.strftime("%d.%m.%Y"), now.strftime("%d.%m.%Y"), ]
    logger.info(f"{hse_user_id = } {period = }")

    await get_pass_report(hse_user_id, period)


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['use_bagration_admin_get_pass_report_week']))
async def call_bagration_admin_get_pass_report(call: types.CallbackQuery = None, callback_data: dict = None,
                                               user_id: int | str = None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST
    """

    hse_user_id = call.message.chat.id if call else user_id
    if call: logger.debug(f'{hse_user_id = } {call.data = }')

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    now = datetime.now()
    current_week: str = await get_week_message(current_date=now)
    current_year: str = await get_year_message(current_date=now)

    period = await db_get_period_for_current_week(current_week, current_year)
    logger.info(f"{hse_user_id = } {period = }")

    await get_pass_report(hse_user_id, period)


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['use_bagration_admin_get_pass_report_month']))
async def call_bagration_admin_get_pass_report(call: types.CallbackQuery = None, callback_data: dict = None,
                                               user_id: int | str = None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST
    """

    hse_user_id = call.message.chat.id if call else user_id
    if call: logger.debug(f'{hse_user_id = } {call.data = }')

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    now = datetime.now()
    current_month: str = await get_month_message(current_date=now)
    current_year: str = await get_year_message(current_date=now)

    period = await db_get_period_for_current_month(current_month, current_year)
    logger.info(f"{hse_user_id = } {period = }")

    await get_pass_report(hse_user_id, period)


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['use_bagration_admin_get_pass_report_all']))
async def call_bagration_admin_get_pass_report(call: types.CallbackQuery = None, callback_data: dict = None,
                                               user_id: int | str = None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST
    """

    hse_user_id = call.message.chat.id if call else user_id
    if call: logger.debug(f'{hse_user_id = } {call.data = }')

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    period = None

    await get_pass_report(hse_user_id, period)


async def test():
    # await call_bagration_admin_get_pass_report()

    hse_user_id = 373084462
    period = None  # [datetime.now().strftime("%d.%m.%Y"), datetime.now().strftime("%d.%m.%Y")]

    await get_pass_report(hse_user_id, period)

    return []


if __name__ == '__main__':
    asyncio.run(test())
