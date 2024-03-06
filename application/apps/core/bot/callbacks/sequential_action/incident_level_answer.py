from loader import logger

logger.debug(f"{__name__} start import")
from aiogram import types
from aiogram.dispatcher import FSMContext
from apps.core.bot.filters.custom_filters import filter_incident_level
from apps.core.bot.reports.report_data_preparation import set_violation_atr_data
from apps.core.bot.reports.report_data import ViolationData
from apps.core.bot.callbacks.sequential_action.data_answer import get_and_send_incident_level_data
from apps.MyBot import MyBot

logger.debug(f"{__name__} finish import")


@MyBot.dp.callback_query_handler(filter_incident_level, state=ViolationData.all_states)
async def incident_level_answer(call: types.CallbackQuery, state: FSMContext = None):
    """Обработка ответов содержащихся в INCIDENT_LEVEL
    """
    try:
        await set_violation_atr_data("incident_level", call.data, state=state)

        await get_and_send_incident_level_data(call, state=state)

    except Exception as callback_err:
        logger.error(f"{repr(callback_err)}")
