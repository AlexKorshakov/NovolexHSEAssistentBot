from apps.core.bot.filters.custom_filters import filter_elimination_time
from loader import logger

logger.debug(f"{__name__} start import")
from aiogram import types
from aiogram.dispatcher import FSMContext
from apps.core.bot.reports.report_data import ViolationData
from apps.core.bot.callbacks.sequential_action.data_answer import get_and_send_elimination_time_data
from apps.core.bot.reports.report_data_preparation import set_violation_atr_data
from apps.MyBot import MyBot

logger.debug(f"{__name__} finish import")


@MyBot.dp.callback_query_handler(filter_elimination_time, state=ViolationData.all_states)
async def elimination_time_answer(call: types.CallbackQuery, state: FSMContext = None):
    """Обработка ответов содержащихся в ELIMINATION_TIME
    """
    await set_violation_atr_data("elimination_time", call.data, state=state)

    try:
        await get_and_send_elimination_time_data(call, state=state)

    except Exception as callback_err:
        logger.error(f"{repr(callback_err)}")
