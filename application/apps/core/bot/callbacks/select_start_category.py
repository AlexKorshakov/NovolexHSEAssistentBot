from __future__ import annotations
from loader import logger

logger.debug(f"{__name__} start import")

from aiogram import types
from aiogram.types import InlineKeyboardMarkup
from apps.MyBot import bot_send_message
from apps.core.bot.callbacks.callback_action import cb_start

logger.debug(f"{__name__} finish import")


async def select_start_category(message: types.Message, user_id: int | str = None) -> None:
    """Действия при начале регистрации нарушения / начале работы бота
    """
    hse_user_id = message.chat.id if message else user_id
    markup = await get_start_category()

    await bot_send_message(chat_id=hse_user_id, text="Зарегистрировать нарушение?", reply_markup=markup)


async def get_start_category() -> InlineKeyboardMarkup:
    """Действия при начале регистрации нарушений (в конце ввода данных).
    Возвращает кнопки 'Зарегистрировать' и 'Отмена'
    """
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(
            text="Зарегистрировать",
            callback_data=cb_start.new(action="select_start_registration")
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            text="Отмена",
            callback_data=cb_start.new(action="select_abort_registration"))
    )
    return markup
