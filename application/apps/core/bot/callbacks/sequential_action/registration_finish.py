from __future__ import annotations

from loader import logger

logger.debug(f"{__name__} start import")
import pandas
from aiogram import types
from aiogram.dispatcher import FSMContext
from datetime import date, datetime

from apps.MyBot import MyBot, bot_send_message
from apps.core.bot.bot_utils.check_access import get_hse_user_data
from apps.core.bot.callbacks.sequential_action.data_answer import notify_user_for_choice
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.reports.report_data_preparation import set_violation_atr_data
from apps.core.database.db_utils import (get_year_message,
                                         get_month_message,
                                         get_week_message,
                                         db_get_data_dict_from_table_with_id)
from apps.core.utils.data_recording_processor.set_user_violation_data import pre_set_violation_data

logger.debug(f"{__name__} finish import")


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['registration_finish']), state='*')
async def registration_finish_handler(call: types.CallbackQuery = None, callback_data: dict = None,
                                      user_id: int | str = None, state: FSMContext = None):
    """Обработчик сообщений содержащих 'завершить регистрацию'

    """
    hse_user_id = call.message.chat.id if call else user_id

    await bot_send_message(
        chat_id=hse_user_id,
        text="Запущена процедура регистрации данных. Дождитесь сообщения об окончании."
    )
    await update_violation_data(
        chat_id=hse_user_id, message=call.message, state=state
    )
    await notify_user_for_choice(call, data_answer=call.data)
    await pre_set_violation_data(call.message, state=state)

    await state.finish()


async def get_day_message(current_date: datetime | str = None) -> str:
    """Обработчик сообщений с фото
    Получение номер str дня из сообщения в формате dd
    """

    current_date: date = await str_to_datetime(current_date)

    if not current_date:
        current_date: datetime = datetime.now()
    return str("0" + str(current_date.day) if current_date.day < 10 else str(current_date.day))


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


async def get_day_of_year_message(current_date: datetime | str = None) -> str:
    """Возвращает номер дня в году для даты сообщения

    """
    current_date: date = await str_to_datetime(current_date)

    if not current_date:
        current_date: datetime = datetime.now()
    day_of_year = pandas.Timestamp(current_date).day_of_year
    return str("0" + str(day_of_year) if day_of_year < 10 else str(day_of_year))


async def get_quarter_message(current_date: datetime | str = None) -> str:
    """Обработчик сообщений с фото
    Получение номер str квартала из сообщения в формате dd
    """
    current_date: date = await str_to_datetime(current_date)

    if not current_date:
        current_date: date = datetime.now()
    quarter = pandas.Timestamp(current_date).quarter
    return str("0" + str(quarter) if quarter < 10 else str(quarter))


async def update_violation_data(chat_id, message: types.Message, state: FSMContext):
    """

    :param chat_id:
    :param message:
    :param state:
    :return:
    """
    await state.update_data(user_id=chat_id)
    await set_violation_atr_data("user_id", chat_id, state=state)

    await state.update_data(user_fullname=message.from_user.full_name)
    await set_violation_atr_data("user_fullname", message.from_user.full_name, state=state)

    await set_violation_atr_data("now", str(datetime.now()), state=state)

    await state.update_data(status='В работе')
    await set_violation_atr_data("status", 'В работе', state=state)

    user_registration_data: dict = await get_hse_user_data(message=message)

    location = await db_get_data_dict_from_table_with_id(
        table_name='core_location',
        post_id=user_registration_data.get("hse_location", None)
    )

    await state.update_data(location=location['title'])
    await set_violation_atr_data("location", location['title'], state=state)

    work_shift = await db_get_data_dict_from_table_with_id(
        table_name='core_workshift',
        post_id=user_registration_data.get("hse_work_shift", None)
    )

    await state.update_data(work_shift=work_shift['title'])
    await set_violation_atr_data("work_shift", work_shift['title'], state=state)

    await state.update_data(hse_id=user_registration_data.get("id", None))
    await set_violation_atr_data("hse_id", user_registration_data.get("id", None), state=state)

    await state.update_data(function=user_registration_data.get("hse_function", None))
    await set_violation_atr_data("function", user_registration_data.get("hse_function", None), state=state)

    await state.update_data(name=user_registration_data.get("hse_full_name", None))
    await set_violation_atr_data("name", user_registration_data.get("hse_full_name", None), state=state)

    await state.update_data(parent_id=user_registration_data.get("parent_id"))
    await set_violation_atr_data("parent_id", user_registration_data.get("parent_id"), state=state)

    await state.update_data(day=await get_day_message())
    await set_violation_atr_data("day", await get_day_message(), state=state)

    await state.update_data(week=await get_week_message())
    await set_violation_atr_data("week", await get_week_message(), state=state)

    await state.update_data(quarter=await get_quarter_message())
    await set_violation_atr_data("quarter", await get_quarter_message(), state=state)

    await state.update_data(day_of_year=await get_day_of_year_message())
    await set_violation_atr_data("day_of_year", await get_day_of_year_message(), state=state)

    await state.update_data(month=await get_month_message())
    await set_violation_atr_data("month", await get_month_message(), state=state)

    await state.update_data(year=await get_year_message())
    await set_violation_atr_data("year", await get_year_message(), state=state)

    deta = await get_day_message() + ":" + await get_month_message() + ":" + await get_year_message()

    await state.update_data(deta=deta)
    await set_violation_atr_data("deta", deta, state=state)
