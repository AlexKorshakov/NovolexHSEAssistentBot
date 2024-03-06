from __future__ import annotations

from aiogram import types

from apps.MyBot import MyBot, bot_send_message, bot_delete_markup
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.handlers.correct_entries.correct_entries_handler import correct_entries_handler
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages import Messages
from apps.core.bot.messages.messages_test import msg
from apps.core.database.db_utils import db_update_column_value
from loader import logger


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['correct_non_act_item_finalize']))
async def call_correct_non_act_item_finalize(call: types.CallbackQuery = None, callback_data: dict[str, str] = None,
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
    try:
        item_number_text = int(item_number_text)
    except Exception as err:
        logger.error(f'{hse_user_id = } {repr(err)} {item_number_text = }')
        await bot_send_message(chat_id=hse_user_id, text=Messages.Error.error_command)
        # TODO Delete
        logger.error(f'{hse_user_id = } Messages.Error.error_action')
        msg_text = await msg(hse_user_id, cat='error', msge='error_action', default=Messages.Error.error_action).g_mas()
        await bot_send_message(chat_id=hse_user_id, text=msg_text)
        return

    reply_markup = await add_correct_act_delete_inline_keyboard_with_action()
    item_finalize_text: str = 'Вы уверены что хотите финализировать и записать пункт как завершенный? ' \
                              f'Выбрано item_number_{item_number_text}'
    await bot_send_message(chat_id=hse_user_id, text=item_finalize_text, reply_markup=reply_markup)


async def add_correct_act_delete_inline_keyboard_with_action():
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """

    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton('Да. Финализировать и записать',
                                          callback_data=posts_cb.new(id='-',
                                                                     action='correct_non_act_item_finalize_yes')))
    markup.add(types.InlineKeyboardButton('Нет. Вернуться',
                                          callback_data=posts_cb.new(id='-',
                                                                     action='correct_non_act_item_finalize_not')))
    return markup


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['correct_non_act_item_finalize_not']))
async def call_correct_non_act_item_finalize_not(call: types.CallbackQuery = None, callback_data: dict[str, str] = None,
                                                 user_id: int | str = None):
    """Обработка ответов содержащихся в callback_data "Финализировать и записать"
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {callback_data = }')

    await bot_delete_markup(message=call.message)

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    await correct_entries_handler(hse_user_id=hse_user_id)


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['correct_non_act_item_finalize_yes']))
async def call_correct_act_finalize_yes(call: types.CallbackQuery = None, callback_data: dict[str, str] = None,
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
    errors_count: int = 0

    finished_result_execute: bool = await db_update_column_value(
        column_name='finished_id',
        value=1,
        violation_id=str(item_number_text)
    )
    status_result_execute: bool = await db_update_column_value(
        column_name='status_id',
        value=1,
        violation_id=str(item_number_text)
    )

    if finished_result_execute and status_result_execute:
        logger.info(
            f'{hse_user_id = } Данные записи {item_number_text} успешно обновлены в database!')
    else:
        logger.error(
            f'{hse_user_id = } Ошибка обновления данных {item_number_text}  в database!')
        errors_count += 1

    if errors_count:
        text: str = f'Акт-предписание не закрыт. Количество ошибок: {errors_count}.'
        await bot_send_message(chat_id=hse_user_id, text=text)
        return

    text: str = f'Данные записи {item_number_text} успешно обновлены в database! Пункт закрыт.'
    await bot_send_message(chat_id=hse_user_id, text=text)
