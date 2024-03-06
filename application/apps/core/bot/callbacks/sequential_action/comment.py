from loader import logger

logger.debug(f"{__name__} start import")

from aiogram import types
from aiogram.dispatcher import FSMContext
from apps.core.bot.callbacks.sequential_action.registration_finist_keybord import registration_finish_keyboard_inline
from apps.core.bot.messages.messages import Messages
from apps.core.bot.reports.report_data import ViolationData
from apps.core.bot.reports.report_data_preparation import set_violation_atr_data
from apps.MyBot import MyBot, bot_send_message

logger.debug(f"{__name__} finish import")


@MyBot.dp.message_handler(state=ViolationData.comment)
async def process_comment(message: types.Message, state: FSMContext):
    """Обработчик состояния comment
    """
    chat_id = message.chat.id

    await set_violation_atr_data("comment", message.text, state=state)

    await ViolationData.location.set()
    await bot_send_message(chat_id=chat_id, text="При необходимости отправьте своё местоположение")

    violation: dict = await state.get_data()
    if violation.get("comment"):
        # await notify_user_for_choice(call, data_answer=message.text)

        reply_markup = await registration_finish_keyboard_inline()
        await bot_send_message(chat_id=chat_id, text=Messages.Registration.confirm, reply_markup=reply_markup)
