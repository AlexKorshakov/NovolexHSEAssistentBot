# from apps.MyBot import bot_send_message
# from loader import logger
#
# logger.debug(f"{__name__} start import")
# from aiogram import types
# from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
# from apps.core.bot.messages.messages import Messages
#
# logger.debug(f"{__name__} finish import")
#
#
# async def bild_inline_keyboard(message: types.Message, *, some_list, num_col=1) -> None:
#     """Создание кнопок в чате для пользователя на основе some_list.
#
#     Количество кнопок = количество элементов в списке some_list
#     Расположение в n_cols столбцов
#     Текст на кнопках text=ss
#     Возвращаемое значение, при нажатии кнопки в чате callback_data=ss
#     """
#     chat_id = message.chat.id
#
#     button_list = [InlineKeyboardButton(text=some_item, callback_data=some_item) for some_item in some_list]
#     # сборка клавиатуры из кнопок `InlineKeyboardMarkup`
#     menu = await _build_menu(buttons=button_list, n_cols=num_col)
#
#     reply_markup = InlineKeyboardMarkup(resize_keyboard=True, inline_keyboard=menu)
#     # отправка клавиатуры в чат
#     await bot_send_message(chat_id=chat_id, text=Messages.Choose.main_category, reply_markup=reply_markup)
#
#
# async def _build_menu(buttons, n_cols: int = 1, header_buttons: list = None, footer_buttons: list = None) -> list:
#     """Создание меню кнопок
#     """
#     menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
#     if header_buttons:
#         menu.insert(0, [header_buttons])
#     if footer_buttons:
#         menu.append([footer_buttons])
#     return menu
