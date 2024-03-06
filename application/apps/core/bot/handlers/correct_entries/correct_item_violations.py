from __future__ import annotations
import asyncio

from datetime import datetime

from aiogram import types

from apps.MyBot import MyBot, bot_send_message, bot_delete_message, bot_delete_markup
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.handlers.correct_entries.correct_entries_handler import correct_entries_handler
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages import Messages
from apps.core.bot.messages.messages_test import msg
from loader import logger


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['correct_item_violations']))
async def call_correct_item_violations(call: types.CallbackQuery = None, callback_data: dict[str, str] = None,
                                       user_id: int | str = None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST
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

    act_number_text = call.message.values['text'].split('_')[-1].split(' ')[-1]
    logger.debug(f'{hse_user_id = } {act_number_text = }')

    try:
        act_number_text = int(act_number_text)
    except Exception as err:
        logger.error(f'{hse_user_id = } {repr(err)} {act_number_text = }')
        await bot_send_message(chat_id=hse_user_id, text=Messages.Error.error_command)
        # TODO Delete
        logger.error(f'{hse_user_id = } Messages.Error.error_action')
        msg_text = await msg(hse_user_id, cat='error', msge='error_action', default=Messages.Error.error_action).g_mas()
        await bot_send_message(chat_id=hse_user_id, text=msg_text)
        return

    reply_markup = await add_correct_item_violations_inline_keyboard_with_action()
    act_delete_text: str = f'Вы уверены что хотите начать корректировать отдельные пункты акта {act_number_text}? ' \
                           f'Выбрано act_number_{act_number_text}'
    await bot_send_message(chat_id=hse_user_id, text=act_delete_text, reply_markup=reply_markup)


async def add_correct_item_violations_inline_keyboard_with_action():
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """

    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton('Да. Финализировать и записать',
                                          callback_data=posts_cb.new(id='-', action='correct_item_violations_yes')))
    markup.add(types.InlineKeyboardButton('Нет. Вернуться',
                                          callback_data=posts_cb.new(id='-', action='correct_item_violations_not')))
    return markup


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['correct_item_violations_not']))
async def call_correct_item_violations_not(call: types.CallbackQuery, callback_data: dict[str, str],
                                           user_id: int | str = None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {callback_data = }')

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    await correct_entries_handler(hse_user_id=hse_user_id)


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['correct_item_violations_yes']))
async def call_correct_item_violations_yes(call: types.CallbackQuery, callback_data: dict[str, str],
                                           user_id: int | str = None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {callback_data = }')

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    if not call:
        await bot_send_message(chat_id=hse_user_id, text=Messages.Error.error_call)
        return

    if not call.message.values['text']:
        await bot_send_message(chat_id=hse_user_id, text=Messages.Error.error_call_text)
        return

    act_number_text = call.message.values['text'].split('_')[-1].split(' ')[-1]
    logger.debug(f'{hse_user_id = } {act_number_text = }')

    msg_id = call.message.message_id
    await bot_delete_message(chat_id=hse_user_id, message_id=msg_id, sleep_sec=15)


async def get_now() -> str:
    """Возвращает текущую дату и время.
    :return: str
    """
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")


async def test():
    await call_correct_item_violations(user_id='373084462')


if __name__ == '__main__':
    asyncio.run(test())
