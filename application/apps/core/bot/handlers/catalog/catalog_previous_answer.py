from aiogram import types

from apps.core.bot.handlers.catalog.catalog_func_handler import catalog_func_handler
from apps.core.bot.handlers.catalog.catalog_lna import call_catalog_lna_answer
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import move_action
from apps.MyBot import MyBot
from aiogram.dispatcher import FSMContext

from apps.core.bot.states.CatalogState import CatalogStateLNA


@MyBot.dp.callback_query_handler(move_action.filter(action=["pre_paragraph"]), state=CatalogStateLNA.all_states)
async def previous_paragraph_answer(call: types.CallbackQuery, callback_data: dict,
                                    user_id: [int, str] = None, state: FSMContext = None):
    """Обработка ответов содержащихся в previous_paragraph
    """

    chat_id = call.message.chat.id if call else user_id
    v_data: dict = await state.get_data()

    if callback_data['pre_val'] == 'call_catalog_lna_catalog_answer':
        await call_catalog_lna_answer(call, callback_data, state=state)

    elif callback_data['pre_val'] == 'call_catalog_func_handler':
        await catalog_func_handler(call.message, user_id=chat_id, state=state)
