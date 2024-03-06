from __future__ import annotations

import traceback
from datetime import datetime, timedelta
from pathlib import Path

from aiogram import types
from aiogram.dispatcher import FSMContext

from apps.MyBot import MyBot, bot_send_message, bot_send_document
from apps.core.bot.bot_utils.check_access import check_developer_access, check_user_access
from apps.core.bot.handlers.s_user_fanc.s_admin_support_paths import sa_check_path
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages import Messages
from apps.core.bot.states import AnswerUserState
from loader import logger


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['s_user_get_current_file']))
async def s_user_get_current_file(call: types.CallbackQuery, callback_data: dict[str, str]):
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

    # Вызов состояния ожидания текстового ответа от пользователя
    await AnswerUserState.current_file.set()
    return True


# Сюда приходит ответ с description, state=состояние
@MyBot.dp.message_handler(state=AnswerUserState.current_file)
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

    main_path: str | Path = message.text if message else test_path
    if not sa_check_path(main_path):
        logger.error(f'{await fanc_name()} path {main_path} is not exists!')
        await bot_send_message(chat_id=hse_user_id, text=f'path {main_path} is not exists!')
        return

    await bot_send_document(
        chat_id=hse_user_id,
        doc_path=main_path,
        caption='Файл',
        calling_fanc_name=await fanc_name()
    )


async def get_today() -> str:
    return (datetime.today() + timedelta(hours=0)).strftime("%d.%m.%Y")


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])
