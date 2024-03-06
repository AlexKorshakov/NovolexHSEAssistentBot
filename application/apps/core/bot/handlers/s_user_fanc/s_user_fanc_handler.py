from __future__ import annotations

import traceback

from aiogram.dispatcher import FSMContext

from loader import logger

logger.debug(f"{__name__} start import")

from pandas import DataFrame
from aiogram import types
from aiogram.dispatcher.filters import Command

from apps.MyBot import MyBot, bot_send_message
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb, is_private
from apps.core.bot.bot_utils.check_access import check_super_user_access, check_admin_access, check_developer_access, \
    get_hse_role_receive_df, check_user_access
from apps.core.utils.misc import rate_limit

logger.debug(f"{__name__} finish import")


@rate_limit(limit=10)
@MyBot.dp.message_handler(Command('super_user_fanc'), is_private, state='*')
async def super_user_fanc_handler(message: types.Message = None, *, hse_user_id: int | str = None,
                                  state: FSMContext = None) -> None:
    """Проверка доступа, получение файлов для отправки, получение списка адресатов для отправки писем
    формирование тела письма, добавление вложений

    Отправка сообщения с отчетом

    :param state:
    :param hse_user_id:
    :param message: объект сообщения от бота,
    :return: сообщение об успешной отправке письма / сообщение об ошибке
    """
    if message.chat.type in ['group', 'supergroup']:
        return
    # if message.from_user.id not in [member.user.id for member in await message.chat.get_administrators()]:
    #     return

    chat_id = message.chat.id if message else hse_user_id

    hse_role_df: DataFrame = await get_hse_role_receive_df()

    if not await check_user_access(chat_id=chat_id, role_df=hse_role_df):
        logger.error(f'access fail {chat_id = }')
        return

    current_state = await state.get_state()
    await state.finish()
    logger.info(f'{await fanc_name()} state is finish {current_state = }')

    main_reply_markup = types.InlineKeyboardMarkup()

    if not await check_admin_access(chat_id=chat_id, role_df=hse_role_df):
        logger.error(f'check_admin_access fail {chat_id = }')
        return

    main_reply_markup = await add_inline_keyboard_with_action_for_admin(main_reply_markup)

    if await check_super_user_access(chat_id=chat_id, role_df=hse_role_df):
        main_reply_markup = await add_correct_inline_keyboard_with_action_for_super_user(main_reply_markup)

    if await check_developer_access(chat_id=chat_id, role_df=hse_role_df):
        main_reply_markup = await add_correct_inline_keyboard_with_action_for_developer(main_reply_markup)

    text: str = 'Выберите действие'
    await bot_send_message(chat_id=chat_id, text=text, reply_markup=main_reply_markup)


async def add_inline_keyboard_with_action_for_admin(markup):
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """
    markup.add(types.InlineKeyboardButton(
        'ADM Проверить статус Актов',
        callback_data=posts_cb.new(id='-', action='check_acts_prescriptions_status'))
    )
    # markup.add(types.InlineKeyboardButton(
    #     'ADM Отправить статус Актов подрядчикам',
    #     callback_data=posts_cb.new(id='-', action='check_acts_prescriptions_status_for_subcontractor'))
    # )
    # markup.add(types.InlineKeyboardButton(
    #     'ADM Проверить нормативку',
    #     callback_data=posts_cb.new(id='-', action='check_indefinite_normative'))
    # )

    return markup


async def add_correct_inline_keyboard_with_action_for_super_user(markup):
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """
    # markup.add(types.InlineKeyboardButton(
    #     text='SU Включение функций',
    #     callback_data=posts_cb.new(id='-', action='s_user_enable_features')))

    return markup


async def add_correct_inline_keyboard_with_action_for_developer(markup):
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """
    markup.add(types.InlineKeyboardButton(
        text='DEV Включение функций',
        callback_data=posts_cb.new(id='-', action='s_user_enable_features')))

    markup.add(types.InlineKeyboardButton(
        text='DEV резервное копирование всех БД',
        callback_data=posts_cb.new(id='-', action='s_user_backup_all_databases')))

    markup.add(types.InlineKeyboardButton(
        text='DEV Получить список файлов',
        callback_data=posts_cb.new(id='-', action='s_user_get_files')))

    markup.add(types.InlineKeyboardButton(
        text='DEV Получить файл',
        callback_data=posts_cb.new(id='-', action='s_user_get_current_file')))

    markup.add(types.InlineKeyboardButton(
        text='DEV Записать файл',
        callback_data=posts_cb.new(id='-', action='s_user_set_current_file')))

    markup.add(types.InlineKeyboardButton(
        text='DEV Выключить бот',
        callback_data=posts_cb.new(id='-', action='s_user_shutdown')))

    return markup


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])
