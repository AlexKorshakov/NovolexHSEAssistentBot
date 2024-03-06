# from aiogram.dispatcher import FSMContext
#
# from loader import logger
#
# logger.debug(f"{__name__} start import")
# import apps.xxx
# from aiogram import types
# from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
# from apps.core.bot.data.board_config import BoardConfig as board_config
# from apps.core.bot.callbacks.sequential_action.category import VIOLATIONS_DATA_LIST, get_filter_data_list
# from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import build_inlinekeyboard
# from apps.core.bot.messages.messages import Messages
# from apps.core.bot.states import CorrectViolationsState
# from apps.core.bot.handlers.generate.generate_report.get_file_list import get_json_file_list
# # from apps.core.utils.goolgedrive_processor.GoogleDriveUtils.set_user_violation_data_on_google_drave import \
# #     update_user_violation_data_on_google_drive
# from apps.core.utils.json_worker.read_json_file import read_json_file
# from apps.core.utils.json_worker.writer_json_file import write_json_file
# from apps.MyBot import MyBot, bot_send_message
# from config.config import ADMIN_ID, SEPARATOR
#
# logger.debug(f"{__name__} finish import")
#
#
# @MyBot.dp.callback_query_handler(lambda call: call.data in VIOLATIONS_DATA_LIST)
# async def correct_violations_data_answer(call: types.CallbackQuery, state: FSMContext = None):
#     """Обработка ответов содержащихся в VIOLATIONS_DATA_LIST
#
#     """
#     chat_id = call.from_user.id
#     await call.message.edit_reply_markup()
#     reply_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
#     reply_markup.add(Messages.correct_cancel)
#
#     if call.data == "Описание нарушения":
#         logger.debug(f"{chat_id = } Выбрано:: {call.data}")
#         await CorrectViolationsState.description.set()
#
#         await bot_send_message(chat_id=chat_id, text=Messages.Enter.description_violation, reply_markup=reply_markup)
#         return
#
#     if call.data == "Комментарий к нарушению":
#         logger.debug(f"{chat_id = } Выбрано:: {call.data}")
#         await CorrectViolationsState.comment.set()
#
#         await bot_send_message(chat_id=chat_id, text=Messages.Enter.comment, reply_markup=reply_markup)
#         return
#
#     if call.data == "Основное направление":
#         logger.debug(f"{chat_id = } Выбрано:: {call.data}")
#
#         # menu_level = board_config.menu_level = 2
#         # menu_list = board_config.menu_list = [item for item in get_filter_data_list("MAIN_CATEGORY") if item is not None]
#         menu_level = await board_config(state, "menu_level", 2).set_data()
#         menu_list = await board_config(state, "menu_list",
#                                        [item for item in get_filter_data_list("MAIN_CATEGORY") if item is not None]).set_data()
#
#         reply_markup = await build_inlinekeyboard(some_list=menu_list, num_col=1, level=menu_level, step=len(menu_list))
#         await bot_send_message(chat_id=chat_id, text=Messages.Choose.main_category, reply_markup=reply_markup)
#
#         await CorrectViolationsState.main_category.set()
#         return
#
#     if call.data == "Количество дней на устранение":
#         logger.debug(f"{chat_id = } Выбрано:: {call.data}")
#
#         # menu_level = board_config.menu_level = 2
#         # menu_list = board_config.menu_list = [item for item in get_filter_data_list("ELIMINATION_TIME") if item is not None]
#         menu_level = await board_config(state, "menu_level", 2).set_data()
#         menu_list = await board_config(state, "menu_list", [item for item in get_filter_data_list("ELIMINATION_TIME") if
#                                                             item is not None]).set_data()
#
#         reply_markup = await build_inlinekeyboard(some_list=menu_list, num_col=1, level=menu_level, step=len(menu_list))
#         await bot_send_message(chat_id=chat_id, text=Messages.Choose.elimination_time, reply_markup=reply_markup)
#
#         await CorrectViolationsState.elimination_time.set()
#         return
#
#     if call.data == "Степень опасности ситуации":
#         logger.debug(f"{chat_id = } Выбрано:: {call.data}")
#
#         # menu_level = board_config.menu_level = 2
#         # menu_list = board_config.menu_list = [item for item in get_filter_data_list("INCIDENT_LEVEL") if item is not None]
#         menu_level = await board_config(state, "menu_level", 2).set_data()
#         menu_list = await board_config(state, "menu_list", [item for item in get_filter_data_list("INCIDENT_LEVEL") if
#                                                             item is not None]).set_data()
#
#         reply_markup = await build_inlinekeyboard(some_list=menu_list, num_col=1, level=menu_level, step=len(menu_list))
#         await bot_send_message(chat_id=chat_id, text=Messages.Choose.incident_level, reply_markup=reply_markup)
#
#         await CorrectViolationsState.incident_level.set()
#         return
#
#     if call.data == "Требуется ли оформление акта?":
#         logger.debug(f"{chat_id = } Выбрано:: {call.data}")
#
#         # menu_level = board_config.menu_level = 2
#         # menu_list = board_config.menu_list = [item for item in get_filter_data_list("ACT_REQUIRED") if item is not None]
#         menu_level = await board_config(state, "menu_level", 2).set_data()
#         menu_list = await board_config(state, "menu_list",
#                                        [item for item in get_filter_data_list("ACT_REQUIRED") if item is not None]).set_data()
#
#         reply_markup = await build_inlinekeyboard(some_list=menu_list, num_col=1, level=menu_level, step=len(menu_list))
#         await bot_send_message(chat_id=chat_id, text=Messages.Choose.act_required, reply_markup=reply_markup)
#
#         await CorrectViolationsState.act_required.set()
#         return
#
#     if call.data == "Подрядная организация":
#         logger.debug(f"{chat_id = } Выбрано:: {call.data}")
#
#         # menu_level = board_config.menu_level = 1
#         # menu_list = board_config.menu_list = [item for item in get_filter_data_list("GENERAL_CONTRACTORS") if item is not None]
#         menu_level = await board_config(state, "menu_level", 2).set_data()
#         menu_list = await board_config(state, "menu_list", [item for item in get_filter_data_list("GENERAL_CONTRACTORS") if
#                                                             item is not None]).set_data()
#
#         reply_markup = await build_inlinekeyboard(some_list=menu_list, num_col=1, level=menu_level, step=len(menu_list))
#         await bot_send_message(chat_id=chat_id, text=Messages.Choose.general_constractor, reply_markup=reply_markup)
#
#         await CorrectViolationsState.general_constractor.set()
#         return
#
#     if call.data == "Степень опасности ситуации":
#         logger.debug(f"{chat_id = } Выбрано:: {call.data}")
#
#         # menu_level = board_config.menu_level = 2
#         # menu_list = board_config.menu_list = [item for item in get_filter_data_list("VIOLATION_CATEGORY") if item is not None]
#         menu_level = await board_config(state, "menu_level", 2).set_data()
#         menu_list = await board_config(state, "menu_list", [item for item in get_filter_data_list("VIOLATION_CATEGORY") if
#                                                             item is not None]).set_data()
#
#         reply_markup = await build_inlinekeyboard(some_list=menu_list, num_col=1, level=menu_level, step=len(menu_list))
#         await bot_send_message(chat_id=chat_id, text=Messages.Choose.violation_category, reply_markup=reply_markup)
#
#         await CorrectViolationsState.violation_category.set()
#         return
#
#     if call.data == "Категория нарушения":
#         logger.debug(f"{chat_id = } Выбрано:: {call.data}")
#
#         # menu_level = board_config.menu_level = 2
#         # menu_list = board_config.menu_list = [item for item in get_filter_data_list("CATEGORY") if item]
#         menu_level = await board_config(state, "menu_level", 2).set_data()
#         menu_list = await board_config(state, "menu_list",
#                                        [item for item in get_filter_data_list("CATEGORY") if item]).set_data()
#
#         reply_markup = await build_inlinekeyboard(some_list=menu_list, num_col=1, level=menu_level, step=len(menu_list))
#         await bot_send_message(chat_id=chat_id, text=Messages.Choose.category, reply_markup=reply_markup)
#
#         await CorrectViolationsState.category.set()
#         return
#
#     if call.data == "Уровень происшествия":
#         logger.debug(f"{chat_id = } Выбрано:: {call.data}")
#
#         # menu_level = board_config.menu_level = 2
#         # menu_list = board_config.menu_list = [item for item in get_filter_data_list("INCIDENT_LEVEL") if item]
#         menu_level = await board_config(state, "menu_level", 2).set_data()
#         menu_list = await board_config(state, "menu_list",
#                                        [item for item in get_filter_data_list("INCIDENT_LEVEL") if item]).set_data()
#
#         reply_markup = await build_inlinekeyboard(some_list=menu_list, num_col=1, level=menu_level, step=len(menu_list))
#         await bot_send_message(chat_id=chat_id, text=Messages.Choose.incident_level, reply_markup=reply_markup)
#
#         await CorrectViolationsState.incident_level.set()
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
# async def all_states(*, chat_id: str, correct_data: str, state_name: str, state: FSMContext = None):
#     """Обработка состояний из get_state_storage_name и данных correct_data
#
#     :param chat_id: id пользователя / чата
#     :param correct_data: данне для коррекции параметра state_name
#     :param state_name: имя параметра для коррекции
#     :return:
#     """
#     violations_file_path: str = ''
#
#     violations_files_list: list = await get_json_file_list(chat_id)
#     if not violations_files_list:
#         logger.warning(Messages.Error.file_list_not_found)
#         await bot_send_message(chat_id=chat_id, text=Messages.Error.file_list_not_found)
#         return
#
#     v_data: dict = await state.get_data()
#
#     violations_id = v_data['current_file'].split(' ')[0]
#
#     for file in violations_files_list:
#         if file.split('\\')[-1].split(SEPARATOR)[-1].replace('.json', '') == violations_id:
#             violations_file_path = file
#             break
#
#     if not violations_file_path:
#         logger.warning(f'{Messages.Error.file_not_found} {violations_id = }')
#         await bot_send_message(chat_id=chat_id, text=f'{Messages.Error.file_not_found} {violations_id = }')
#         return
#
#     violation_data: dict = await read_json_file(file=violations_file_path)
#
#     violation_data[state_name] = correct_data
#
#     await write_json_file(data=violation_data, name=violation_data["json_full_name"])
#
#     # await update_user_violation_data_on_google_drive(chat_id=chat_id, violation_data=violation_data, notify_user=True)
#
#     if violation_data:
#         violation_text = await get_violations_text(violation_data)
#         await bot_send_message(chat_id=chat_id, text=violation_text)
#
#     await bot_send_message(chat_id=chat_id, text=Messages.Successfully.correct_violations_completed,
#                            reply_markup=ReplyKeyboardRemove())
#
#
# async def get_correct_data(*, chat_id, call, json_file_name) -> str:
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
#             correct_data: str = [item for item in correct_data_list if item == call.data][0]
#
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
#     logger.debug(f"chat_{chat_id = } Выбрано:: {correct_data}")
#     await bot_send_message(chat_id=chat_id, text=f"Выбрано: {correct_data}")
#     await call.message.edit_reply_markup()
#
#     return correct_data
#
#
# async def get_violations_text(violations_data) -> str:
#     """
#
#     :param violations_data:
#     :return:
#     """
#     if violations_data:
#         registration_data_text: str = \
#             f"Данные нарушения: \n\n" \
#             f"Описание нарушения: {violations_data.get('description')} \n" \
#             f"Комментарий к нарушению: {violations_data.get('comment')} \n" \
#             f"Основное направление: {violations_data.get('main_category')} \n" \
#             f"Количество дней на устранение: {violations_data.get('elimination_time')} \n" \
#             f"Степень опасности ситуации: {violations_data.get('violation_category')} \n" \
#             f"Требуется ли оформление акта?: {violations_data.get('act_required')} \n" \
#             f"Подрядная организация: {violations_data.get('general_contractor')} \n" \
#             f"Уровень происшествия: {violations_data.get('incident_level')} \n"
#
#         return registration_data_text
#     return ''
