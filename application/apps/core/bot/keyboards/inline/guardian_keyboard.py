from loader import logger

logger.debug(f"{__name__} start import")
import random
from typing import Tuple

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData
from apps.core.bot.data.emojies import emojies
from config.config import NUM_BUTTONS

logger.debug(f"{__name__} finish import")


# создаём CallbackData для удобного парсинга Callback
confirming_callback = CallbackData("confirm", "subject", "necessary_subject", "user_id")


def generate_confirm_markup(user_id: int) -> Tuple[InlineKeyboardMarkup, str]:
    """Функция, создающая клавиатуру для подтверждения, что пользователь не является ботом
    """
    # создаём инлайн клавиатуру
    confirm_user_markup = InlineKeyboardMarkup(row_width=NUM_BUTTONS)
    # генерируем список объектов по которым будем итерироваться
    subjects = random.sample(emojies, NUM_BUTTONS)
    # из них выбираем один рандомный объект, на который должен нажать пользователь
    necessary_subject = random.choice(subjects)
    for emoji in subjects:
        button = InlineKeyboardButton(
            text=emoji.unicode,
            callback_data=confirming_callback.new(
                subject=emoji.subject,
                necessary_subject=necessary_subject.subject,
                user_id=user_id
            )
        )
        confirm_user_markup.insert(button)

    # отдаём клавиатуру после создания
    return confirm_user_markup, necessary_subject.name
