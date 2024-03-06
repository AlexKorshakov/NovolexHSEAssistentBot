from apps.core.bot.reports.report_data import ViolationData
from loader import logger

logger.debug(f"{__name__} start import")

from aiogram import types
from aiogram.dispatcher import FSMContext
from apps.core.bot.messages.messages import Messages
from apps.core.bot.reports.report_data_preparation import set_violation_atr_data
from apps.MyBot import MyBot, bot_send_message

logger.debug(f"{__name__} finish import")


# Сюда приходит ответ с description, state=состояние
@MyBot.dp.message_handler(state=ViolationData.description)
async def process_description(message: types.Message, state: FSMContext):
    """Обработчик состояния description
    """
    chat_id = message.chat.id

    await set_violation_atr_data("description", message.text, state=state)

    await ViolationData.comment.set()

    await bot_send_message(chat_id=chat_id, text=Messages.Enter.comment)
