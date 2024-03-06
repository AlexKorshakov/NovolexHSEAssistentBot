# from __future__ import annotations
#
# from loader import logger
#
# logger.debug(f"{__name__} start import")
#
# import traceback
# from datetime import datetime, timedelta, date
# from pprint import pprint
# from pandas import DataFrame
#
# from aiogram import types
# from aiogram.dispatcher.filters import Command
#
# from apps.MyBot import MyBot, bot_send_message
# from apps.core.database.query_constructor import QueryConstructor
# from apps.core.database.db_utils import (db_get_data_list,
#                                          db_get_table_headers,
#                                          db_get_username,
#                                          db_get_period_for_current_week)
# from apps.core.bot.handlers.generate.generate_report.generate_daily_report.create_and_send_daily_report import \
#     create_and_send_daily_report
# from apps.core.utils.misc import rate_limit
# from apps.core.bot.messages.messages_test import msg
# from apps.core.bot.messages.messages import Messages
# from apps.core.bot.bot_utils.bot_admin_notify import admin_notify
# from apps.core.bot.bot_utils.check_user_registration import check_user_access
# from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
#
# logger.debug(f"{__name__} finish import")
#
#
# @rate_limit(limit=10)
# @MyBot.dp.callback_query_handler(posts_cb.filter(action=['generate_report']))
# @MyBot.dp.message_handler(Command('generate_report'))
# async def report_generate_handler(message: types.Message) -> None:
#     """Формирование и отправка отчета пользователю
#
#     :param message:
#     :return: None
#     """
#     chat_id = message.chat.id
#     if not await check_user_access(chat_id=chat_id):
#         return
#
#     main_reply_markup = types.InlineKeyboardMarkup()
#     hse_role_df: DataFrame = await get_role_receive_df()
#
#     if not await check_user_access(chat_id=chat_id, role_df=hse_role_df):
#         logger.error(f'access fail {chat_id = }')
#         return
#
#     main_reply_markup = await add_period_inline_keyboard_with_action(main_reply_markup)
#
#     if await check_admin_access(chat_id=chat_id, role_df=hse_role_df):
#         main_reply_markup = await add_inline_keyboard_with_action_for_admin(main_reply_markup)
#
#     if await check_super_user_access(chat_id=chat_id, role_df=hse_role_df):
#         main_reply_markup = await add_inline_keyboard_with_action_for_super_user(main_reply_markup)
#
#     await bot_send_message(chat_id=chat_id, text=Messages.Choose.period, reply_markup=main_reply_markup)
#
#
# async def add_period_inline_keyboard_with_action(markup: types.InlineKeyboardMarkup):
#     """Формирование сообщения с текстом и кнопками действий в зависимости от параметров
#
#     :return:
#     """
#     markup.add(types.InlineKeyboardButton(
#         text='за сегодня',
#         callback_data=posts_cb.new(id='-', action='gen_report_today'))
#     )
#     markup.add(types.InlineKeyboardButton(
#         text='за сегодня и вчера',
#         callback_data=posts_cb.new(id='-', action='gen_report_today_and_previous'))
#     )
#     markup.add(types.InlineKeyboardButton(
#         text='за текущую неделю',
#         callback_data=posts_cb.new(id='-', action='gen_report_current_week'))
#     )
#     return markup
#
#
# async def add_inline_keyboard_with_action_for_admin(markup: types.InlineKeyboardMarkup):
#     """Формирование сообщения с текстом и кнопками действий в зависимости от параметров
#
#     :return:
#     """
#     # markup.add(
#     #     types.InlineKeyboardButton(
#     #         text='Статистика',
#     #         callback_data=posts_cb.new(id='-', action='generate_stat'))
#     # )
#     return markup
#
#
# async def add_inline_keyboard_with_action_for_super_user(markup: types.InlineKeyboardMarkup):
#     """Формирование сообщения с текстом и кнопками действий в зависимости от параметров
#
#     :return:
#     """
#     # markup.add(types.InlineKeyboardButton(
#     #     text='SU за текущую КН',
#     #     callback_data=posts_cb.new(id='-', action='gen_stat_current_week_all'))
#     # )
#     return markup
#
#
# async def check_admin_access(chat_id: int | str, role_df: DataFrame = None):
#     """
#
#     :param role_df:
#     :param chat_id:
#     :return:
#     """
#     admin_id_list: list = await get_id_list(
#         hse_user_id=chat_id, user_role='hse_role_is_admin', hse_role_df=role_df
#     )
#     if not admin_id_list:
#         logger.error(f'{await fanc_name()} access fail {chat_id = }')
#         await user_access_fail(chat_id, hse_id=chat_id)
#         return False
#
#     if chat_id not in admin_id_list:
#         logger.error(f'{await fanc_name()} access fail {chat_id = }')
#         return False
#
#     logger.info(f"user_access_granted for {chat_id = }")
#     await user_access_granted(chat_id, role=await fanc_name(), notify=True)
#     return True
#
#
# async def check_super_user_access(chat_id: int | str, role_df: DataFrame = None):
#     """
#
#     :param role_df:
#     :param chat_id:
#     :return:
#     """
#     super_user_id_list: list = await get_id_list(
#         hse_user_id=chat_id, user_role='hse_role_is_super_user', hse_role_df=role_df
#     )
#     if not super_user_id_list:
#         logger.warning(f'{await fanc_name()} access fail {chat_id = }')
#         await user_access_fail(chat_id, hse_id=chat_id)
#         return False
#
#     if chat_id not in super_user_id_list:
#         logger.warning(f'{await fanc_name()} access fail {chat_id = }')
#         return False
#
#     logger.info(f"user_access_granted for {chat_id = }")
#     await user_access_granted(chat_id, role=await fanc_name())
#     return True
#
#
# async def get_role_receive_df() -> DataFrame | None:
#     """Получение df с ролями пользователя
#
#     :return:
#     """
#
#     db_table_name: str = 'core_hseuser'
#     kwargs: dict = {
#         "action": 'SELECT',
#         "subject": '*',
#     }
#     query: str = await QueryConstructor(table_name=db_table_name, **kwargs).prepare_data()
#     datas_query: list = await db_get_data_list(query=query)
#     if not datas_query:
#         return None
#
#     if not isinstance(datas_query, list):
#         return None
#
#     clean_headers: list = [item[1] for item in await db_get_table_headers(table_name=db_table_name)]
#     if not clean_headers:
#         return None
#
#     try:
#         hse_role_receive_df: DataFrame = DataFrame(datas_query, columns=clean_headers)
#     except Exception as err:
#         logger.error(f"create_dataframe {repr(err)}")
#         return None
#
#     return hse_role_receive_df
#
#
# async def get_id_list(hse_user_id: str | int, user_role: str = None, hse_role_df: DataFrame = None) -> list:
#     """Получение id"""
#
#     if not await check_dataframe_role(hse_role_df, hse_user_id):
#         hse_role_df: DataFrame = await get_role_receive_df()
#         if not await check_dataframe_role(hse_role_df, hse_user_id):
#             return []
#
#     try:
#         current_act_violations_df: DataFrame = hse_role_df.loc[
#             hse_role_df[user_role] == 1]
#
#     except Exception as err:
#         logger.error(f"loc dataframe {repr(err)}")
#         return []
#
#     unique_hse_telegram_id: list = current_act_violations_df.hse_telegram_id.unique().tolist()
#     if not unique_hse_telegram_id:
#         return []
#
#     return unique_hse_telegram_id
#
#
# async def check_dataframe_role(dataframe: DataFrame, hse_user_id: str | int) -> bool:
#     """Проверка dataframe на наличие данных
#
#     :param dataframe:
#     :param hse_user_id: id пользователя
#     :return:
#     """
#     if dataframe is None:
#         # text_violations: str = 'не удалось получить данные!'
#         # logger.error(f'{hse_user_id = } {text_violations}')
#         return False
#
#     if dataframe.empty:
#         logger.error(f'{hse_user_id = } {Messages.Error.dataframe_is_empty}')
#         return False
#
#     return True
#
#
# async def user_access_granted(chat_id: int, role: str = None, notify=False):
#     """Отправка сообщения - доступ разрешен"""
#
#     reply_markup = types.InlineKeyboardMarkup()
#     reply_markup.add(types.InlineKeyboardButton(text=f'{chat_id}', url=f"tg://user?id={chat_id}"))
#
#     notify_text: str = f'доступ разрешен {chat_id = } {role = }'
#     logger.debug(notify_text)
#     if notify:
#         await admin_notify(user_id=chat_id, notify_text=notify_text)
#
#
# async def user_access_fail(chat_id: int, notify_text: str = None, hse_id: str = None):
#     """Отправка сообщения о недостатке прав
#     """
#     hse_id = hse_id if hse_id else chat_id
#
#     try:
#         part_1 = f"{await msg(hse_id, cat='error', msge='access_fail', default=Messages.default_answer_text).g_mas()}"
#         part_2 = f"{await msg(hse_id, cat='help', msge='help_message', default=Messages.help_message).g_mas()}"
#         answer_text = f'{part_1}\n\n{part_2}'
#         print(f'{answer_text = }')
#
#         await bot_send_message(chat_id=chat_id, text=answer_text, disable_web_page_preview=True)
#         return
#
#     except Exception as err:
#         logger.error(f'User {chat_id} ошибка уведомления пользователя {repr(err)}')
#         await admin_notify(user_id=chat_id, notify_text=notify_text)
#
#     finally:
#         if not notify_text:
#             notify_text: str = f'User {chat_id} попытка доступа к функциям без регистрации'
#
#         logger.error(notify_text)
#         # button = types.InlineKeyboardButton(text=f'{chat_id}', url=f"tg://user?id={chat_id}")
#         await admin_notify(
#             user_id=chat_id,
#             notify_text=notify_text,
#             # button=button
#         )
#
#
# async def get_week_message(current_date: datetime | str = None) -> str:
#     """Обработчик сообщений с фото
#     Получение номер str недели из сообщения в формате dd
#     """
#     current_date: date = await str_to_datetime(current_date)
#
#     if not current_date:
#         current_date: datetime = datetime.now()
#     week = current_date.isocalendar()[1]
#     return str("0" + str(week) if week < 10 else str(week))
#
#
# async def get_year_message(current_date: datetime | str = None) -> str:
#     """Обработчик сообщений с фото
#     Получение полного пути файла
#     """
#     current_date: date = await str_to_datetime(current_date)
#
#     if not current_date:
#         current_date: datetime = datetime.now()
#
#     return str(current_date.year)
#
#
# async def str_to_datetime(date_str: str) -> date:
#     """Преобразование str даты в datetime
#
#     :param
#     """
#
#     current_date = None
#     try:
#         if isinstance(date_str, str):
#             current_date: date = datetime.strptime(date_str, "%d.%m.%Y").date()
#     except ValueError as err:
#         logger.error(f"{repr(err)}")
#
#     return current_date
#
#
# async def fanc_name() -> str:
#     """Возвращает имя вызываемой функции"""
#     stack = traceback.extract_stack()
#     return str(stack[-2][2])
#
#
# @MyBot.dp.callback_query_handler(posts_cb.filter(action=['gen_report_today']))
# async def call_correct_abort_current_post(call: types.CallbackQuery, callback_data: dict[str, str]):
#     """Обработка ответов содержащихся в ADMIN_MENU_LIST
#     """
#     chat_id: int = call.message.chat.id
#     username: str = await db_get_username(user_id=chat_id)
#     action: str = callback_data['action']
#
#     if action == 'gen_report_today':
#         logger.info(f'User: @{username} user_id: {chat_id} choose {action} for generate report')
#         print(f'User: @{username} user_id: {chat_id} choose {action} for generate report')
#
#         await bot_send_message(chat_id=chat_id, text=f'{Messages.Report.start_act} \n {Messages.wait}')
#
#         now = datetime.now()
#         daily_report_date_period: list = [now.strftime("%d.%m.%Y"), now.strftime("%d.%m.%Y"), ]
#         pprint(f'{daily_report_date_period = }')
#
#         kwargs = {}
#
#         logger.info(f'User @{username}:{chat_id} generate report')
#         if await create_and_send_daily_report(chat_id=chat_id, query_period=daily_report_date_period, **kwargs):
#             logger.info(Messages.Report.generated_successfully)
#
#
# @MyBot.dp.callback_query_handler(posts_cb.filter(action=['gen_report_today_and_previous']))
# async def call_correct_abort_current_post(call: types.CallbackQuery, callback_data: dict[str, str]):
#     """Обработка ответов содержащихся в ADMIN_MENU_LIST
#     """
#     chat_id: int = call.message.chat.id
#     username: str = await db_get_username(user_id=chat_id)
#     action: str = callback_data['action']
#
#     if action == 'gen_report_today_and_previous':
#         logger.info(f'User: @{username} user_id: {chat_id} choose {action} for generate report')
#         print(f'User: @{username} user_id: {chat_id} choose {action} for generate report')
#
#         await bot_send_message(chat_id=chat_id, text=f'{Messages.Report.start_report} \n {Messages.wait}')
#
#         now = datetime.now()
#         previous = now - timedelta(days=1)
#         daily_report_date_period: list = [previous.strftime("%d.%m.%Y"), now.strftime("%d.%m.%Y"), ]
#         pprint(f'{daily_report_date_period = }')
#
#         kwargs = {}
#
#         logger.info(f'User @{username}:{chat_id} generate report')
#         if await create_and_send_daily_report(chat_id=chat_id, query_period=daily_report_date_period, **kwargs):
#             logger.info(Messages.Report.generated_successfully)
#
#
# @MyBot.dp.callback_query_handler(posts_cb.filter(action=['gen_report_current_week']))
# async def call_correct_abort_current_post(call: types.CallbackQuery, callback_data: dict[str, str]):
#     """Обработка ответов содержащихся в ADMIN_MENU_LIST
#     """
#     chat_id: int = call.message.chat.id
#     username: str = await db_get_username(user_id=chat_id)
#     action: str = callback_data['action']
#
#     if action == 'gen_report_current_week':
#         logger.info(f'User: @{username} user_id: {chat_id} choose {action} for generate report')
#         print(f'User: @{username} user_id: {chat_id} choose {action} for generate report')
#
#         await bot_send_message(chat_id=chat_id, text='{Messages.Report.start_act} \n{Messages.wait}')
#
#         now = datetime.now()
#         current_week: str = await get_week_message(current_date=now)
#         current_year: str = await get_year_message(current_date=now)
#
#         daily_report_date_period = await db_get_period_for_current_week(current_week, current_year)
#         pprint(f"{daily_report_date_period = }")
#
#         kwargs = {}
#
#         logger.info(f'User @{username}:{chat_id} generate report')
#         if await create_and_send_daily_report(chat_id=chat_id, query_period=daily_report_date_period, **kwargs):
#             logger.info(Messages.Report.generated_successfully)
