from loader import logger

logger.debug(f"{__name__} start import")
from aiogram import types
from aiogram.dispatcher import FSMContext
from apps.core.bot.filters.custom_filters import filter_main_category
from apps.core.bot.callbacks.sequential_action.data_answer import get_and_send_main_category_data
from apps.core.bot.reports.report_data import ViolationData
from apps.core.bot.reports.report_data_preparation import set_violation_atr_data
from apps.MyBot import MyBot

logger.debug(f"{__name__} finish import")


@MyBot.dp.callback_query_handler(filter_main_category, state=ViolationData.all_states)
async def main_category_answer(call: types.CallbackQuery, state: FSMContext = None):
    """Обработка ответов содержащихся в MAIN_CATEGORY
    """
    try:
        await set_violation_atr_data("main_category", call.data, state=state)
        await get_and_send_main_category_data(call, state=state)

    except Exception as callback_err:
        logger.error(f"{repr(callback_err)}")
