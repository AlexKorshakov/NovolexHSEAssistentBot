# from loader import logger
#
# logger.debug(f"{__name__} start import")
# import apps.xxx
# from aiogram import types
# from aiogram.dispatcher import FSMContext
# from aiogram.dispatcher.filters import Textr
# from aiogram.types import (CallbackQuery, ReplyKeyboardMarkup, ReplyKeyboardRemove)
# from apps.core.bot.data.board_config import BoardConfig as board_config
# from apps.core.bot.callbacks.sequential_action.category import REGISTRATION_DATA_LIST, get_filter_data_list
# from apps.core.bot.filters.custom_filters import filter_is_private
# from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import build_inlinekeyboard
# from apps.core.bot.messages.messages import Messages
# from apps.core.bot.states import CorrectRegisterState
# from apps.core.utils.data_recording_processor.set_user_registration_data import set_user_registration_data
# from apps.core.bot.handlers.generate.generate_report.get_file_list import get_registration_json_file_list
# from apps.core.utils.json_worker.read_json_file import read_json_file
# from apps.MyBot import MyBot, bot_send_message
# from config.config import ADMIN_ID
#
# logger.debug(f"{__name__} finish import")
#
#
# @MyBot.dp.callback_query_handler(lambda call: call.data in REGISTRATION_DATA_LIST)
# async def correct_registration_data_answer(call: types.CallbackQuery, state: FSMContext = None):
#     """Обработка ответов содержащихся в REGISTRATION_DATA_LIST
#
#     """
#     hse_chat_id = call.from_user.id
#     await call.message.edit_reply_markup()
#
#     reply_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
#     reply_markup.add(Messages.correct_cancel)
#
#     if call.data == "ФИО":
#         logger.debug(f"{hse_chat_id = } Выбрано: {call.data}")
#         await CorrectRegisterState.name.set()
#
#         await bot_send_message(chat_id=hse_chat_id, text=Messages.Ask.name, reply_markup=reply_markup)
#
#     if call.data == "Должность":
#         logger.debug(f"{hse_chat_id = } Выбрано: {call.data}")
#         await CorrectRegisterState.function.set()
#
#         await bot_send_message(chat_id=hse_chat_id, text=Messages.Ask.function, reply_markup=reply_markup)
#
#     if call.data == "Смена":
#         logger.debug(f"{hse_chat_id = } Выбрано: {call.data}")
#
#         # menu_level = board_config.menu_level = 2
#         # menu_list = board_config.menu_list = [item for item in get_filter_data_list("WORK_SHIFT") if item]
#         menu_level = await board_config(state, "menu_level", 2).set_data()
#         menu_list = await board_config(state, "menu_list",
#                                        [item for item in get_filter_data_list("WORK_SHIFT") if item]).set_data()
#
#         reply_markup = await build_inlinekeyboard(some_list=menu_list, num_col=1, level=menu_level, step=len(menu_list))
#         await bot_send_message(chat_id=hse_chat_id, text=Messages.Ask.work_shift, reply_markup=reply_markup)
#
#         await CorrectRegisterState.work_shift.set()
#
#     if call.data == "Телефон":
#         logger.debug(f"{hse_chat_id = } Выбрано: {call.data}")
#         await CorrectRegisterState.phone_number.set()
#
#         await bot_send_message(chat_id=hse_chat_id, text=Messages.Ask.phone_number, reply_markup=reply_markup)
#
#     if call.data == "Место работы":
#         logger.debug(f"{hse_chat_id = } Выбрано: {call.data}")
#
#         # menu_level = board_config.menu_level = 2
#         # menu_list = board_config.menu_list = [list(item.keys())[0] for item in get_filter_data_list("METRO_STATION")]
#
#         menu_level = await board_config(state, "menu_level", 2).set_data()
#         menu_list = await board_config(state, "menu_list",
#                                        [list(item.keys())[0] for item in get_filter_data_list("METRO_STATION")]).set_data()
#
#         await CorrectRegisterState.name_location.set()
#
#
# @MyBot.dp.message_handler(filter_is_private, Text(equals=Messages.correct_cancel), state=CorrectRegisterState.all_states)
# async def cancel(message: types.Message, state: FSMContext):
#     """Отмена регистрации
#     :param message:
#     :param state:
#     :return:
#     """
#     await state.finish()
#     return await message.reply(Messages.Registration.canceled, reply_markup=ReplyKeyboardRemove())
#
#
# @MyBot.dp.callback_query_handler(filter_is_private, lambda call: call.data in [list(item.keys())[0] for item in
#                                                                         get_filter_data_list("METRO_STATION")],
#                                  state=CorrectRegisterState.name_location)
# async def correct_registration_data_name_location_answer(call: types.CallbackQuery, state: FSMContext):
#     """Обработка ответов содержащихся в METRO_STATION
#     """
#
#     chat_id = call.from_user.id
#     correct_data = await get_correct_data(chat_id=chat_id, call=call, json_file_name="METRO_STATION")
#     if not correct_data:
#         await state.finish()
#         return
#
#     state_name = await get_state_storage_name(state, chat_id)
#     await all_states(chat_id=chat_id, correct_data=correct_data, state_name=state_name)
#     await state.finish()
#
#
# @MyBot.dp.callback_query_handler(filter_is_private, lambda call: call.data in [item for item in
#                                                                         get_filter_data_list("WORK_SHIFT") if
#                                                                         item is not None],
#                                  state=CorrectRegisterState.work_shift)
# async def correct_registration_data_work_shift_answer(call: types.CallbackQuery, state: FSMContext):
#     """Обработка ответов содержащихся в WORK_SHIFT
#     """
#     chat_id = call.from_user.id
#     correct_data = await get_correct_data(chat_id=chat_id, call=call, json_file_name="WORK_SHIFT")
#     if not correct_data:
#         await state.finish()
#         return
#
#     state_name = await get_state_storage_name(state, chat_id)
#     await all_states(chat_id=chat_id, correct_data=correct_data, state_name=state_name)
#     await state.finish()
#
#
# @MyBot.dp.message_handler(filter_is_private, state=CorrectRegisterState.all_states)
# async def correct_registration_data_all_states_answer(message: types.Message, state: FSMContext) -> None:
#     """Отмена регистрации
#     :param message types.Message
#     :param state FSMContext
#     :return None
#     """
#     chat_id = message.chat.id
#     state_name = await get_state_storage_name(state, chat_id)
#     await all_states(chat_id=chat_id, correct_data=message.text, state_name=state_name)
#     await state.finish()
#
#
# async def get_state_storage_name(state, chat_id):
#     """Получение имени состояния state[state]
#     """
#     state_storage = dict(apps.xxx.storage.data)
#     state_name: str = state_storage.get(f'{chat_id}').get(f'{chat_id}').get('state').split(':')[-1]
#
#     return state_name
#
#
# async def all_states(*, chat_id, correct_data, state_name):
#     """Обработка состояний из get_state_storage_name и данных correct_data
#
#     :param chat_id:
#     :param correct_data:
#     :param state_name:
#     :return:
#     """
#     registration_file_list: list = await get_registration_json_file_list(chat_id=chat_id)
#     if not registration_file_list:
#         logger.warning(Messages.Error.registration_file_list_not_found)
#         await bot_send_message(chat_id=chat_id, text=Messages.Error.file_list_not_found)
#         return
#
#     registration_data = await read_json_file(registration_file_list)
#     if not registration_data:
#         logger.error("registration_data is empty")
#         return
#
#     registration_data[f'{state_name}'] = correct_data
#
#     await set_user_registration_data(chat_id=chat_id, user_data=registration_data)
#
#     registration_data: dict = await read_json_file(registration_file_list)
#
#     if not registration_data:
#         logger.error("registration_data is empty")
#         await bot_send_message(chat_id=chat_id, text=Messages.Error.file_list_not_found)
#         return
#     registration_text: str = ''
#     if registration_data:
#         registration_text = await get_registration_text(registration_data)
#
#     await bot_send_message(chat_id=chat_id, text=registration_text)
#
#     await bot_send_message(chat_id=chat_id,
#                            text=Messages.Successfully.correct_registration_completed,
#                            reply_markup=ReplyKeyboardRemove())
#
#
# async def get_correct_data(*, chat_id: int, call: CallbackQuery, json_file_name: str) -> str:
#     """Получение корректных данных из call: types.CallbackQuery и  state: FSMContext
#     """
#     correct_data: str = ''
#     correct_data_list = get_filter_data_list(json_file_name)
#     item_correct_data = correct_data_list[0]
#
#     try:
#         if isinstance(item_correct_data, dict):
#             correct_data: str = \
#                 [list(item.keys())[0] for item in correct_data_list if list(item.keys())[0] == call.data][0]
#
#         if isinstance(item_correct_data, str):
#             correct_data: str = \
#                 [item for item in correct_data_list if item == call.data][0]
#     except Exception as callback_err:
#         logger.error(f"{chat_id= } {repr(callback_err)}")
#
#     if not correct_data:
#         text = f'get_correct_data is None or error {json_file_name = }'
#         logger.error(text)
#         await bot_send_message(chat_id=ADMIN_ID, text=text)
#         await bot_send_message(chat_id=chat_id, text=text)
#         return correct_data
#
#     logger.debug(f"{chat_id = } Выбрано: {correct_data}")
#     await bot_send_message(chat_id=chat_id, text=f"Выбрано: {correct_data}")
#     await call.message.edit_reply_markup()
#
#     return correct_data
#
#
# async def get_registration_text(registration_data: dict) -> str:
#     """
#
#     :param registration_data: dict
#     :return:
#     """
#     if registration_data:
#         registration_data_text: str = f"Данные регистрации: \n\n" \
#                                       f"ФИО: {registration_data.get('name')} \n" \
#                                       f"Должность: {registration_data.get('function')} \n" \
#                                       f"Место работы: {registration_data.get('name_location')} \n" \
#                                       f"Смена: {registration_data.get('work_shift')} \n" \
#                                       f"Телефон: {registration_data.get('phone_number')} \n"
#
#         return registration_data_text
#     return ''
