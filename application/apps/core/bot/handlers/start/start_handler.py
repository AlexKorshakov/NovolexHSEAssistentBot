from __future__ import annotations

import traceback
from loader import logger

logger.debug(f"{__name__} start import")

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command

from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.filters.custom_filters import filter_is_private
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import build_inlinekeyboard
from apps.core.bot.messages.messages_test import msg
from apps.core.bot.messages.messages import Messages
from apps.core.bot.reports.report_data import user_data
from apps.core.database.db_utils import db_update_hse_user_language
from apps.core.settyngs import get_sett
from apps.core.utils.secondary_functions.get_filepath import get_user_registration_file, create_file_path
from apps.core.utils.misc import rate_limit
from apps.MyBot import MyBot, bot_send_message

logger.debug(f"{__name__} finish import")


@rate_limit(limit=20)
@MyBot.dp.message_handler(Command('start'), filter_is_private, state='*')
async def start(message: types.Message, user_id: int | str = None, state: FSMContext = None):
    """Начало регистрации пользователя

    :param state:
    :param user_id: id пользователя
    :param message:
    :return:
    """
    if message.chat.type in ['group', 'supergroup']:
        return
    # if message.from_user.id not in [member.user.id for member in await message.chat.get_administrators()]:
    #     return
    hse_user_id = message.chat.id if message else user_id
    logger.info(f'User @{message.from_user.username} : {hse_user_id} start work')

    if not await check_user_access(chat_id=hse_user_id, message=message):
        return

    current_state = await state.get_state()
    await state.finish()
    logger.info(f'{await fanc_name()} state is finish {current_state = }')

    if not get_sett(cat='enable_features', param='choose_language').get_set():
        await bot_send_message(chat_id=hse_user_id, text=Messages.HSEUserAnswer.user_access_success)
        user_data["user_id"] = hse_user_id
        user_data['reg_user_file'] = await get_user_registration_file(user_id=str(hse_user_id))

        await create_file_path(path=user_data['reg_user_file'])

        hi_text: str = f'{Messages.hi} {message.chat.username}! \n\n' \
                       f'{Messages.user_greeting}\n{Messages.help_message}'

        await bot_send_message(chat_id=hse_user_id, text=hi_text)
        return

    language_list: list = await get_language_list(message, user_id=hse_user_id)
    text_violations: str = 'Выберите язык / Choose language'

    reply_markup = await build_inlinekeyboard(
        some_list=language_list, num_col=1, level=1, called_prefix='select_lang_'
    )

    await bot_send_message(chat_id=hse_user_id, text=text_violations, reply_markup=reply_markup)


@MyBot.dp.callback_query_handler(lambda call: 'select_lang_' in call.data)
async def call_correct_item_answer(call: types.CallbackQuery, user_id: str | int = None, state: FSMContext = None):
    """Обработка ответов
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } ::: {call.data = }')

    character_language: str = call.data.split('_')[-1]
    result: bool = await db_update_hse_user_language(value=character_language, hse_id=hse_user_id)

    if result:
        text_violations: str = await msg(hse_user_id, cat='main', msge="application_language",
                                         default=Messages.application_language).g_mas()
        await bot_send_message(chat_id=hse_user_id, text=f'{text_violations}')

    user_data["user_id"] = hse_user_id
    user_data['reg_user_file'] = await get_user_registration_file(user_id=str(hse_user_id))

    await create_file_path(path=user_data['reg_user_file'])

    hi_text: str = f'{await msg(hse_user_id, cat="main", msge="hi", default=Messages.hi).g_mas()} ' \
                   f'{call.message.chat.username}! \n\n' \
                   f'{await msg(hse_user_id, cat="main", msge="user_access_success", default=Messages.HSEUserAnswer.user_access_success).g_mas()} \n\n' \
                   f'{await msg(hse_user_id, cat="main", msge="user_greeting", default=Messages.user_greeting).g_mas()} \n\n' \
                   f'{await msg(hse_user_id, cat="help", msge="help_message", default=Messages.help_message).g_mas()}'

    await bot_send_message(chat_id=hse_user_id, text=hi_text)


async def get_language_list(message: types.Message, user_id: int | str = None):
    """Выбор языка интерфейса бота

    """
    hse_user_id = message.chat.id if message else user_id

    lang_list: list = await msg(hse_user_id).get_lang_in_main()
    return lang_list


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])
