from loader import logger

logger.debug(f"{__name__} start import")
from aiogram import types
from aiogram.dispatcher import FSMContext
from apps.core.bot.callbacks.sequential_action.data_answer import (get_and_send_normative_documents_data,
                                                                   get_and_send_null_normative_documents_data)
from apps.core.bot.filters.custom_filters import filter_normativedocuments
from apps.core.bot.callbacks.sequential_action.category import (_PREFIX_ND,
                                                                get_data_list)
from apps.core.bot.reports.report_data import ViolationData
from apps.core.bot.reports.report_data_preparation import set_violation_atr_data
from apps.MyBot import MyBot

logger.debug(f"{__name__} finish import")


@MyBot.dp.callback_query_handler(filter_normativedocuments, state=ViolationData.all_states)
async def normative_documents_answer(call: types.CallbackQuery, state: FSMContext = None):
    """Обработка ответов содержащихся в NORMATIVE_DOCUMENTS
    """
    v_data: dict = await state.get_data()

    if call.data == _PREFIX_ND + "0":
        await get_and_send_null_normative_documents_data(call, state=state)

        await set_violation_atr_data("normative_documents", 'Нет нужной записи', state=state)
        await set_violation_atr_data("normative_documents_normative", 'укажите НД', state=state)
        await set_violation_atr_data("normative_documents_procedure", 'укажите процедуру устранения по НД',
                                     state=state)
        return

    nd_data: list = []
    try:
        condition: dict = {
            "data": call.data,
            "category_in_db": "core_normativedocuments",
        }
        nd_data: list = await get_data_list("core_normativedocuments",
                                            category=v_data.get("category", None),
                                            condition=condition)
        if not nd_data:
            await set_violation_atr_data("normative_documents", call.data, state=state)

        nd_data = [item for item in nd_data if (isinstance(item, dict) and item.get("id", None))]

        await set_violation_atr_data("normative_documents", nd_data[0].get('title', None), state=state)
        await set_violation_atr_data("normative_documents_normative", nd_data[0].get('normative', None),
                                     state=state)
        await set_violation_atr_data("normative_documents_procedure", nd_data[0].get('procedure', None),
                                     state=state)

        await get_and_send_normative_documents_data(call, state=state)

    except Exception as callback_err:
        logger.error(f"{repr(callback_err)} {nd_data = }")
