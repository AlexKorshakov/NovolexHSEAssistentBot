from __future__ import annotations

import asyncio
from datetime import datetime

from aiogram import types

from apps.MyBot import MyBot, bot_send_message, bot_delete_markup
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages import Messages
from apps.core.bot.messages.messages_test import msg
from loader import logger


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['correct_act_item_delete']))
async def call_correct_act_item_delete(call: types.CallbackQuery = None, callback_data: dict[str, str] = None,
                                       user_id: int | str = None):
    """Обработка ответов содержащихся в callback_data "Финализировать и записать"
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {callback_data = }')

    await bot_delete_markup(message=call.message)

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    if not call:
        await bot_send_message(chat_id=hse_user_id, text=Messages.Error.error_call)
        return

    if not call.message.values['text']:
        await bot_send_message(chat_id=hse_user_id, text=Messages.Error.error_call_text)
        return

    item_number_text = call.message.values['text'].split('_')[-1].split(' ')[-1]
    logger.debug(f'{hse_user_id = } {item_number_text = }')
    # TODO Delete
    logger.error(f'{hse_user_id = } Messages.Error.error_action')
    msg_text = await msg(hse_user_id, cat='error', msge='error_action', default=Messages.Error.error_action).g_mas()
    await bot_send_message(chat_id=hse_user_id, text=msg_text)


async def get_now() -> str:
    """Возвращает текущую дату и время.
    :return: str
    """
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")


async def test():
    await call_correct_act_item_delete(user_id='373084462')


if __name__ == '__main__':
    asyncio.run(test())
