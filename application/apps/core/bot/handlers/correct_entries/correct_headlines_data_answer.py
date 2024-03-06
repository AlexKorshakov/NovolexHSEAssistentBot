from loader import logger

logger.debug(f"{__name__} start import")
import apps.xxx
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from apps.core.bot.data.board_config import BoardConfig as board_config
from apps.core.bot.callbacks.sequential_action.category import (HEADLINES_DATA_LIST,
                                                                get_data_list)
from apps.core.bot.filters.custom_filters import filter_is_private
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import build_inlinekeyboard
from apps.core.bot.messages.messages import Messages
from apps.core.bot.reports.report_data import headlines_data
from apps.core.bot.states.CorrectHeadlinesState import CorrectHeadlinesState
from apps.MyBot import MyBot, bot_send_message

logger.debug(f"{__name__} finish import")


@MyBot.dp.callback_query_handler(lambda call: call.data in HEADLINES_DATA_LIST)
async def correct_headlines_data_answer(call: types.CallbackQuery, state: FSMContext = None):
    """Обработка ответов содержащихся в HEADLINES_DATA_LIST
    """
    chat_id = call.from_user.id
    await call.message.edit_reply_markup()

    reply_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    reply_markup.add(Messages.correct_cancel)

    if call.data == "Руководитель строительства":
        logger.debug(f"{chat_id = } Выбрано: {call.data}")
        await CorrectHeadlinesState.construction_manager.set()

        await bot_send_message(chat_id=chat_id, text=Messages.Ask.construction_manager, reply_markup=reply_markup)
        return

    if call.data == "Инженер СК":
        logger.debug(f"{chat_id = } Выбрано: {call.data}")
        await CorrectHeadlinesState.building_control_engineer.set()

        await bot_send_message(chat_id=chat_id, text=Messages.Ask.building_control_engineer, reply_markup=reply_markup)
        return

    if call.data == "Подрядчик":
        logger.debug(f"{chat_id = } Выбрано: {call.data}")

        menu_level = await board_config(state, "menu_level", 2).set_data()
        menu_list = await board_config(state, "menu_list", [
            item for item in await get_data_list("core_generalcontractor") if item is not None
        ]).set_data()

        reply_markup = await build_inlinekeyboard(some_list=menu_list, num_col=1, level=menu_level, step=len(menu_list),
                                                  state=state)
        await bot_send_message(chat_id=chat_id, text=Messages.Ask.contractor, reply_markup=reply_markup)

        await CorrectHeadlinesState.general_contractor.set()
        return

    if call.data == "Субподрядчик":
        logger.debug(f"{chat_id = } Выбрано: {call.data}")
        await CorrectHeadlinesState.subcontractor.set()

        await bot_send_message(chat_id=chat_id, text=Messages.Ask.subcontractor, reply_markup=reply_markup)
        return

    if call.data == "Вид обхода":
        logger.debug(f"{chat_id = } Выбрано: {call.data}")
        await CorrectHeadlinesState.linear_bypass.set()

        await bot_send_message(chat_id=chat_id, text=Messages.Ask.linear_bypass, reply_markup=reply_markup)
        return

    if call.data == "Представитель подрядчика":
        logger.debug(f"{chat_id = } Выбрано: {call.data}")
        await CorrectHeadlinesState.contractor_representative.set()

        await bot_send_message(chat_id=chat_id, text=Messages.Ask.contractor_representative, reply_markup=reply_markup)
        return

    if call.data == "Представитель субподрядчика":
        logger.debug(f"{chat_id = } Выбрано: {call.data}")
        await CorrectHeadlinesState.subcontractor_representative.set()

        await bot_send_message(chat_id=chat_id, text=Messages.Ask.subcontractor_representative,
                               reply_markup=reply_markup)


@MyBot.dp.message_handler(filter_is_private, Text(equals=Messages.correct_cancel), state=CorrectHeadlinesState.all_states)
async def cancel(message: types.Message, state: FSMContext):
    """Отмена регистрации
    :param message:
    :param state:
    :return:
    """
    await state.finish()
    return await message.reply(Messages.Registration.canceled, reply_markup=ReplyKeyboardRemove())


@MyBot.dp.message_handler(filter_is_private, state=CorrectHeadlinesState.all_states)
async def correct_headlines_data_all_states_answer(message: types.Message, state: FSMContext):
    """Отмена регистрации
    :param message:
    :param state:
    :return:
    """
    chat_id = message.chat.id

    state_name = await get_state_storage_name(state, chat_id)
    await all_states(chat_id=chat_id, correct_data=message.text, state_name=state_name)
    await state.finish()


async def get_state_storage_name(state, chat_id):
    """Получение имени состояния state[state]
    """
    state_storage = dict(apps.xxx.storage.data)
    state_name: str = state_storage.get(f'{chat_id}').get(f'{chat_id}').get('state').split(':')[-1]
    return state_name


async def all_states(*, chat_id, correct_data, state_name):
    """Обработка состояний из get_state_storage_name и данных correct_data

    :param chat_id:
    :param correct_data:
    :param state_name:
    :return: None
    """
    headlines_data[f'{state_name}'] = correct_data

    if headlines_data:
        headlines_text = await get_headlines_text(headlines_data)
        await bot_send_message(chat_id=chat_id, text=headlines_text)

    await bot_send_message(chat_id=chat_id,
                           text=Messages.Successfully.correct_headlines_completed,
                           reply_markup=ReplyKeyboardRemove())


async def get_headlines_text(headlines_data: dict) -> str:
    """

    :param headlines_data:
    :return:
    """
    if not headlines_data:
        return ''

    headlines_text = f"Данные регистрации: \n\n" \
                     f"Руководитель строительства: {headlines_data.get('construction_manager')} \n" \
                     f"Инженер СК: {headlines_data.get('building_control_engineer')} \n" \
                     f"Подрядчик: {headlines_data.get('general_contractor')} \n" \
                     f"Субподрядчик: {headlines_data.get('subcontractor')} \n" \
                     f"Проект: {headlines_data.get('name_location')} \n" \
                     f"Вид обхода: {headlines_data.get('linear_bypass')} \n" \
                     f"Дата: {headlines_data.get('date_linear_bypass')} \n" \
                     f"Представитель подрядчика: {headlines_data.get('contractor_representative')} \n" \
                     f"Представитель субподрядчика: {headlines_data.get('subcontractor_representative')} \n"

    return headlines_text
