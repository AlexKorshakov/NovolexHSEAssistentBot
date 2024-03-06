from loader import logger

logger.debug(f"{__name__} start import")
from aiogram import types
from aiogram.dispatcher import FSMContext
from apps.core.bot.filters.custom_filters import filter_category
from apps.core.bot.reports.report_data import ViolationData
from apps.core.database.db_utils import db_get_data_list
from apps.core.database.query_constructor import QueryConstructor
from apps.core.bot.callbacks.sequential_action.data_answer import get_and_send_category_data
from apps.core.bot.reports.report_data_preparation import set_violation_atr_data
from apps.MyBot import MyBot

logger.debug(f"{__name__} finish import")


@MyBot.dp.callback_query_handler(filter_category, state=ViolationData.all_states)
async def category_answer(call: types.CallbackQuery, state: FSMContext = None):
    """Обработка ответов содержащихся в CATEGORY
    """
    try:
        await set_violation_atr_data("category", call.data, state=state)

        kwargs: dict = {
            "action": 'SELECT',
            "subject": 'id',
            "conditions": {
                "title": f"{call.data}",
            }
        }
        query: str = await QueryConstructor(table_name='core_category', **kwargs).prepare_data()

        datas_query: list = await db_get_data_list(query=query)
        category_id = datas_query[0][0] if datas_query else None

        await set_violation_atr_data("category_id", category_id, state=state)

        await get_and_send_category_data(call, state=state)

    except Exception as callback_err:
        logger.error(f"{repr(callback_err)}")
