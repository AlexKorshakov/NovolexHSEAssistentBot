from __future__ import annotations

import asyncio

from aiogram import types
from aiogram.dispatcher import FSMContext

from apps.MyBot import MyBot, bot_send_message
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.filters.custom_filters import (is_admin_add_user,
                                                  admin_add_user_default)
from apps.core.bot.handlers.admin_func.admin_write_data_in_database import write_new_user_data_in_database
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages import Messages
from apps.core.bot.messages.messages_test import msg
from apps.core.settyngs import get_sett
from loader import logger


@MyBot.dp.callback_query_handler(is_admin_add_user, state='*')  # if 'admin_add_user_' in call.data
async def admin_add_user_answer(call: types.CallbackQuery, callback_data: dict[str, str] = None,
                                state: FSMContext = None, user_id: int | str = None):
    """

    :return:
    """
    hse_user_id: int | str = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {call.data = }')

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    if not get_sett(cat='enable_features', param='use_bagration_admin_add_user').get_set():
        msg_text: str = f"{await msg(hse_user_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=hse_user_id, text=msg_text, disable_web_page_preview=True)
        return

    user_for_action = call.data.split(':')[-1].replace('admin_add_user_', '')
    print(f'{user_for_action = }')

    main_reply_markup = types.InlineKeyboardMarkup()
    main_reply_markup = await add_inline_keyboard_with_action_for_admin(main_reply_markup, user_for_action)

    await bot_send_message(chat_id=hse_user_id, text=Messages.Choose.action, reply_markup=main_reply_markup)


async def add_inline_keyboard_with_action_for_admin(markup: types.InlineKeyboardMarkup, user_for_action):
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """
    if not markup:
        markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(
        text='Ввод обязательных данных',
        callback_data=posts_cb.new(id='-', action=f'admin_add_add_user_progress_{user_for_action}'))
    )
    markup.add(types.InlineKeyboardButton(
        text='Ввод по умолчанию',
        callback_data=posts_cb.new(id='-', action=f'admin_add_add_user_default_{user_for_action}'))
    )
    return markup


@MyBot.dp.callback_query_handler(admin_add_user_default, state='*')
async def set_admin_add_user_default(call: types.CallbackQuery, callback_data: dict[str, str] = None,
                                     state: FSMContext = None, user_id: int | str = None):
    """

    :param call:
    :param callback_data:
    :param state:
    :param user_id:
    :return:
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {call.data = }')

    user_for_action = call.data.split(':')[-1].replace('admin_add_add_user_default_', '')
    print(f'{user_for_action = }')

    user_data: dict = {
        'user_telegram_id': user_for_action,
        'hse_telegram_id': user_for_action,
        'title': user_for_action,
    }

    user_data.update({
        'hse_role_is_author': 0,
        'hse_role_is_developer': 0,
        'hse_role_is_admin': 0,
        'hse_role_is_coordinating_person': 0,
        'hse_role_is_super_user': 0,
        'hse_role_is_user': 1,
        'hse_role_is_subcontractor': 0,
        'hse_role_receive_notifications': 0,
        'hse_role_is_user_bagration': 1,
        'hse_role_is_emploee_tc': 1,
    })
    user_data.update({
        'hse_full_name': 'Жопов Жан Жак',
        'hse_full_name_dative': 'Жоповым Жан Жак',
        'hse_short_name': 'Жоповым Ж.Ж.',
        'hse_full_name_telegram': 'Жопов',
        'hse_function': 'Жопа с ушами',
        'hse_function_dative': 'Жопой с ушами',
        'hse_department': 'Отдел жопошников',
        'hse_department_dative': 'Отделом жопошников',
    })
    user_data.update({
        'hse_language_code': 'ru',
    })
    user_data.update({
        'hse_is_work': 1,
        'hse_status': 1,
        'hse_status_comment': 'на вахте',
    })

    if await write_new_user_data_in_database(user_data_to_db=user_data, admin_id=hse_user_id):
        return True


async def test():
    hse_user_id = 373084462
    user_data: dict = {
        'hse_telegram_id': hse_user_id,
        'user_telegram_id': 5484554,
        'title': 373084462,
        'hse_is_work': 1,
        'hse_organization': 1
    }
    user_data.update({
        'hse_role_is_author': 0,
        'hse_role_is_developer': 0,
        'hse_role_is_admin': 0,
        'hse_role_is_coordinating_person': 0,
        'hse_role_is_super_user': 0,
        'hse_role_is_user': 1,
        'hse_role_is_subcontractor': 0,
        'hse_role_receive_notifications': 0,
        'hse_role_is_user_bagration': 1,
        'hse_role_is_emploee_tc': 1,
    })
    user_data.update({
        'hse_full_name': 'Жопов Жан Жак',
        'hse_full_name_dative': 'Жоповым Жан Жак',
        'hse_short_name': 'Жоповым Ж.Ж.',
        'hse_full_name_telegram': 'Жопов',
        'hse_function': 'Жопа с ушами',
        'hse_function_dative': 'Жопой с ушами',
        'hse_department': 'Отдел жопошников',
        'hse_department_dative': 'Отделом жопошников',
    })
    user_data.update({
        'hse_language_code': 'ru',
    })
    user_data.update({
        'hse_status': 1,
        'hse_status_comment': 'на вахте',
    })
    await write_new_user_data_in_database(user_data_to_db=user_data, admin_id=hse_user_id)


if __name__ == '__main__':
    asyncio.run(test())
