from loader import logger

logger.debug(f"{__name__} start import")
from aiogram import types

from apps.MyBot import MyBot, bot_send_message
from aiogram.dispatcher import FSMContext
from apps.core.bot.callbacks.sequential_action.registration_finist_keybord import registration_finish_keyboard_inline
from apps.core.bot.messages.messages import Messages
from apps.core.bot.reports.report_data import ViolationData
from apps.core.bot.reports.report_data_preparation import set_violation_atr_data

logger.debug(f"{__name__} finish import")


@MyBot.dp.message_handler(state=ViolationData.location, content_types=['location'])
async def location_comment(message: types.Message, state: FSMContext):
    """Обработчик состояния location
    """
    chat_id = message.from_user.id

    await set_violation_atr_data("coordinates", f'{message.location.latitude} \n{message.location.longitude}',
                                 state=state)

    logger.info(f'coordinates: {message.location.latitude} \n{message.location.longitude}')

    await set_violation_atr_data("latitude", message.location.latitude, state=state)
    await set_violation_atr_data("longitude", message.location.longitude, state=state)

    keyboard = await registration_finish_keyboard_inline()
    await bot_send_message(chat_id=chat_id, text=Messages.Registration.confirm, reply_markup=keyboard)
