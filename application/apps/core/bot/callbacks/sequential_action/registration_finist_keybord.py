from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup

from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb


async def registration_finish_keyboard_reply() -> ReplyKeyboardMarkup:
    """Сборка клавиатуры команд в конце ввода данных
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(
        types.KeyboardButton(
            text="Завершить регистрацию",
        )
    )
    return markup


async def registration_finish_keyboard_inline() -> InlineKeyboardMarkup:
    """Сборка клавиатуры команд в конце ввода данных
    """
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            text='Сформировать акт',
            callback_data=posts_cb.new(id='-', action='registration_finish_add_coordinate')
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            text='Добавить координаты',
            callback_data=posts_cb.new(id='-', action='registration_finish_add_coordinate')
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            text='Добавить фотографии к нарушению',
            callback_data=posts_cb.new(id='-', action='registration_finish_add_many_photo')
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            text='Завершить регистрацию',
            callback_data=posts_cb.new(id='-', action='registration_finish')
        )
    )
    return markup
