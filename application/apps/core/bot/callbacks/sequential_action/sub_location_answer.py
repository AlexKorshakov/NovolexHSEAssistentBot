from loader import logger

logger.debug(f"{__name__} start import")
from aiogram import types
from aiogram.dispatcher import FSMContext
from apps.core.bot.filters.custom_filters import filter_sub_location
from apps.core.bot.reports.report_data import ViolationData
from apps.core.bot.callbacks.sequential_action.data_answer import (get_and_send_null_sub_locations_data,
                                                                   get_and_send_sub_locations_data)
from apps.core.bot.callbacks.sequential_action.category import (_PREFIX_POZ,
                                                                get_data_list)
from apps.core.bot.reports.report_data_preparation import set_violation_atr_data
from apps.MyBot import MyBot

logger.debug(f"{__name__} finish import")


@MyBot.dp.callback_query_handler(filter_sub_location, state=ViolationData.all_states)
async def sub_location_answer(call: types.CallbackQuery, state: FSMContext = None):
    """Обработка ответов содержащихся в sub_location
    """

    v_data: dict = await state.get_data()

    if call.data == _PREFIX_POZ + "0":
        await get_and_send_null_sub_locations_data(call, state=state)
        await set_violation_atr_data("sub_location", 'Площадка в целом', state=state)
        return

    try:
        condition: dict = {
            "data": call.data,
            "category_in_db": "core_sublocation",
        }
        sub_loc: list = await get_data_list("core_sublocation",
                                            category=v_data.get("main_location", None),
                                            condition=condition)
        if not sub_loc:
            await set_violation_atr_data("sub_location", call.data, state=state)

        sub_loc = [item for item in sub_loc if (isinstance(item, dict) and item.get("id", None))]

        await set_violation_atr_data("sub_location", sub_loc[0].get('title', None), state=state)
        await get_and_send_sub_locations_data(call, state=state)

    except Exception as callback_err:
        logger.error(f"{repr(callback_err)}")
