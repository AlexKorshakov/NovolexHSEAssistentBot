from __future__ import annotations

import asyncio
import traceback
from datetime import datetime, timedelta
from pathlib import Path

from aiogram import types
from aiogram.dispatcher import FSMContext

from apps.MyBot import MyBot, bot_send_message
from apps.core.bot.bot_utils.check_access import check_developer_access, check_user_access
from apps.core.bot.handlers.s_user_fanc.s_admin_support_paths import sa_check_path, sa_check_or_create_dir, \
    sa_get_file_path
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages import Messages
from apps.core.bot.states import AnswerUserState
from loader import logger


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['s_user_set_current_file']))
async def s_user_set_current_file(call: types.CallbackQuery, callback_data: dict[str, str]):
    """Обработка ответов содержащихся в s_user_get_files
    """
    hse_user_id = call.message.chat.id
    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'{await fanc_name()} access fail {hse_user_id = }')
        return

    if not await check_developer_access(chat_id=hse_user_id):
        logger.error(f'{await fanc_name()} check_super_user_access fail {hse_user_id = }')
        return

    main_reply_markup = await add_keyboard_with_action_for_developer()
    await bot_send_message(chat_id=hse_user_id, text="Подтвердите действие", reply_markup=main_reply_markup)

    # Вызов состояния ожидания текстового ответа от пользователя


async def add_keyboard_with_action_for_developer():
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """

    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(
        'Записать файл',
        callback_data=posts_cb.new(id='-', action='s_user_set_current_file_yes'))
    )
    markup.add(types.InlineKeyboardButton(
        'Отменить запись',
        callback_data=posts_cb.new(id='-', action='s_user_set_current_file_no'))
    )

    return markup


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['s_user_set_current_file_no']))
async def s_user_set_current_file(call: types.CallbackQuery, callback_data: dict[str, str]):
    """Обработка ответов содержащихся в s_user_get_files
    """
    hse_user_id = call.message.chat.id
    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'{await fanc_name()} access fail {hse_user_id = }')
        return

    if not await check_developer_access(chat_id=hse_user_id):
        logger.error(f'{await fanc_name()} check_super_user_access fail {hse_user_id = }')
        return

    await bot_send_message(chat_id=hse_user_id, text="Запись отменена")


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['s_user_set_current_file_yes']))
async def s_user_set_current_file(call: types.CallbackQuery, callback_data: dict[str, str]):
    """Обработка ответов содержащихся в s_user_get_files
    """
    hse_user_id = call.message.chat.id
    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'{await fanc_name()} access fail {hse_user_id = }')
        return

    if not await check_developer_access(chat_id=hse_user_id):
        logger.error(f'{await fanc_name()} check_super_user_access fail {hse_user_id = }')
        return

    await bot_send_message(chat_id=hse_user_id, text=Messages.Enter.address)

    await AnswerUserState.address_set_file.set()
    return True


# Сюда приходит ответ с description, state=состояние
@MyBot.dp.message_handler(state=AnswerUserState.address_set_file, content_types=['document'])
async def process_description(message: types.Message = None, state: FSMContext = None,
                              user_id: int | str = None, test_path: str | Path = None):
    """Обработчик состояния address
    """
    current_state = await state.get_state()
    logger.info(f'{await fanc_name()} Cancelling state {current_state}')
    await state.finish()

    hse_user_id = message.chat.id if message else user_id
    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'{await fanc_name()} access fail {hse_user_id = }')
        return

    if not await check_developer_access(chat_id=hse_user_id):
        logger.error(f'{await fanc_name()} check_super_user_access fail {hse_user_id = }')
        return

    main_path: str | Path = message.caption if message else test_path
    if not sa_check_path(main_path):
        logger.error(f'{await fanc_name()} path {main_path} is not exists!')
        await bot_send_message(chat_id=hse_user_id, text=f'path {main_path} is not exists!')
        return

    save_path: str | Path = await sa_get_file_path(main_path)
    await sa_check_or_create_dir(save_path)

    destination_file_path: str = str(await sa_get_file_path(save_path, message.document.file_name))

    try:
        await message.document.download(make_dirs=False, destination_file=destination_file_path)

    except Exception as err:
        logger.error(f'{await fanc_name()} {destination_file_path = } {repr(err)}')


async def get_today() -> str:
    return (datetime.today() + timedelta(hours=0)).strftime("%d.%m.%Y")


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])


async def test():
    user_id: int = 373084462
    test_path = input()
    await process_description(user_id=user_id, test_path=test_path)


if __name__ == "__main__":
    asyncio.run(test())
