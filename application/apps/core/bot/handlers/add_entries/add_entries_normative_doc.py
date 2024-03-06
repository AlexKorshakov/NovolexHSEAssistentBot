from aiogram import types

from apps.MyBot import MyBot, bot_send_message
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages import Messages
from apps.core.bot.messages.messages_test import msg
from loader import logger


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['add_entries_normative_doc']))
async def call_add_entries(call: types.CallbackQuery, callback_data: dict[str, str], user_id=None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST

    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {callback_data = }')

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    logger.error(f'{hse_user_id = } Messages.Error.error_action')
    msg_text = await msg(hse_user_id, cat='error', msge='error_action', default=Messages.Error.error_action).g_mas()
    await bot_send_message(chat_id=hse_user_id, text=msg_text)