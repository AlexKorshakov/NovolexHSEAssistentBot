from __future__ import annotations

from aiogram import types
from aiogram.dispatcher import FSMContext

from apps.MyBot import bot_send_message, MyBot
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.checker.periodic_check_unclosed_points_for_subcontractor import \
    check_acts_prescriptions_status_for_subcontractor
from loader import logger


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['check_acts_prescriptions_status_for_subcontractor']))
async def check_acts_prescriptions_status_for_subcontractor_answer(call: types.CallbackQuery,
                                                                   callback_data: dict[str, str],
                                                                   state: FSMContext = None):
    """

    :return:
    """
    hse_user_id = call.message.chat.id
    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    await check_acts_prescriptions_status_for_subcontractor()
    await bot_send_message(chat_id=hse_user_id, text="Уведомления направлены")
