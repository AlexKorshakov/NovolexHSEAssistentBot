from loader import logger

logger.debug(f"{__name__} start import")
from aiogram import types
from aiogram.dispatcher import FSMContext

from apps.MyBot import MyBot
from apps.core.bot.callbacks.sequential_action.data_answer import (get_and_send_act_required_data,
                                                                   get_and_send_category_data,
                                                                   get_and_send_elimination_time_data,
                                                                   get_and_send_general_contractor_data,
                                                                   get_and_send_incident_level_data,
                                                                   get_and_send_main_category_data,
                                                                   get_and_send_normative_documents_data,
                                                                   get_and_send_null_normative_documents_data,
                                                                   get_and_send_null_sub_locations_data,
                                                                   get_and_send_sub_locations_data,
                                                                   get_and_send_violation_category_data,
                                                                   get_and_send_start_location_data,
                                                                   get_and_send_main_location_data)
from apps.core.bot.callbacks.sequential_action.category import (_PREFIX_ND,
                                                                _PREFIX_POZ,
                                                                get_data_list)
from apps.core.bot.handlers.catalog.catalog_lna import call_catalog_lna_catalog_answer
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import move_action
from apps.core.bot.reports.report_data import ViolationData
from apps.core.bot.reports.report_data_preparation import set_violation_atr_data

logger.debug(f"{__name__} finish import")


@MyBot.dp.callback_query_handler(move_action.filter(action=["pre_paragraph"]), state=ViolationData.all_states)
async def previous_paragraph_answer(call: types.CallbackQuery, callback_data: dict,
                                    user_id: [int, str] = None, state: FSMContext = None):
    """Обработка ответов содержащихся в previous_paragraph
    """

    chat_id = call.message.chat.id if call else user_id

    v_data: dict = await state.get_data()

    if callback_data['pre_val'] == 'location':
        await get_and_send_start_location_data(call, state=state, context='this_level')

    if callback_data['pre_val'] == 'main_location':
        await get_and_send_main_location_data(call, state=state, context='this_level')

    elif callback_data['pre_val'] == "sub_location":
        if call.data == _PREFIX_POZ + "0":
            await get_and_send_null_sub_locations_data(call, state=state, context='this_level')

        condition: dict = {
            "data": call.data,
            "category_in_db": "core_sublocation",
        }
        sub_loc: list = await get_data_list("core_sublocation",
                                            category=v_data["main_location"],
                                            condition=condition)
        if not sub_loc:
            await set_violation_atr_data("sub_location", call.data, state=state)

        await set_violation_atr_data("sub_location", sub_loc[0].get('title', None), state=state)

        await get_and_send_sub_locations_data(call, state=state, context='this_level')

    elif callback_data['pre_val'] == "main_category":
        await get_and_send_main_category_data(call, state=state, context='this_level')

    elif callback_data['pre_val'] == "category":
        await get_and_send_category_data(call, state=state, context='this_level')

    elif callback_data['pre_val'] == "normative_documents":
        if call.data == _PREFIX_ND + "0":
            await get_and_send_null_normative_documents_data(call, state=state, context='this_level')

        condition: dict = {
            "data": call.data,
            "category_in_db": "core_normativedocuments",
        }
        nd_data: list = await get_data_list("core_normativedocuments",
                                            category=v_data["category"],
                                            condition=condition)
        if not nd_data:
            await set_violation_atr_data("normative_documents", call.data, state=state)

        await set_violation_atr_data("normative_documents", nd_data[0].get('title', None), state=state)
        await set_violation_atr_data("normative_documents_normative", nd_data[0].get('normative', None), state=state)
        await set_violation_atr_data("normative_documents_procedure", nd_data[0].get('procedure', None), state=state)

        await get_and_send_normative_documents_data(call, state=state, context='this_level')

    elif callback_data['pre_val'] == "violation_category":
        await get_and_send_violation_category_data(call, state=state, context='this_level')

    elif callback_data['pre_val'] == "general_contractors":
        await get_and_send_general_contractor_data(call, state=state, context='this_level')

    elif callback_data['pre_val'] == "incident_level":
        await get_and_send_incident_level_data(call, state=state, context='this_level')

    elif callback_data['pre_val'] == "act_required":
        await get_and_send_act_required_data(call, state=state, context='this_level')

    elif callback_data['pre_val'] == "elimination_time":
        await get_and_send_elimination_time_data(call, state=state, context='this_level')

    elif callback_data['pre_val'] == 'call_catalog_lna_catalog_answer':
        await call_catalog_lna_catalog_answer(call, callback_data, state=state)

    else:
        logger.debug(f"{chat_id = }  Выбрано: {callback_data['action']}")
        logger.info(f"User {call.message.chat.id} choices {callback_data['action']}")
        logger.info(f"{call.data = }")
        logger.info(f"{callback_data = }")
