from __future__ import annotations

import asyncio

from aiogram.dispatcher import FSMContext

from apps.core.bot.filters.custom_filters import filter_is_private
from loader import logger

logger.debug(f"{__name__} start import")

import traceback
from aiogram import types
from aiogram.dispatcher.filters import Command
from pandas import DataFrame

from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.bot_utils.bot_admin_notify import admin_notify
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages_test import msg
from apps.core.bot.messages.messages import Messages
from apps.core.database.db_utils import (db_get_data_list,
                                         db_get_clean_headers)
from apps.core.database.query_constructor import QueryConstructor
from apps.core.settyngs import get_sett
from apps.core.utils.misc import rate_limit
from apps.MyBot import MyBot, bot_send_message

logger.debug(f"{__name__} finish import")


@rate_limit(limit=10)
@MyBot.dp.message_handler(Command('bagration'), filter_is_private, state='*')
async def bagration_func_handler(message: types.Message, state: FSMContext = None):
    """Административные функции

    :param message:
    :param state:
    """
    if message.chat.type in ['group', 'supergroup']:
        return
    # if message.from_user.id not in [member.user.id for member in await message.chat.get_administrators()]:
    #     return
    chat_id = message.chat.id

    current_state = await state.get_state()
    await state.finish()
    logger.info(f'{await fanc_name()} state is finish {current_state = }')

    if not await check_user_access(chat_id=chat_id):
        logger.error(f'access fail {chat_id = }')
        return

    if not get_sett(cat='enable_features', param='use_bagration_func').get_set():
        msg_text: str = f"{await msg(chat_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=chat_id, text=msg_text, disable_web_page_preview=True)
        return

    main_reply_markup = types.InlineKeyboardMarkup()
    hse_role_df: DataFrame = await get_bagration_role_receive_df()

    if not await check_user_access(chat_id=chat_id, role_df=hse_role_df):
        logger.error(f'access fail {chat_id = }')
        return

    main_reply_markup = await add_correct_inline_keyboard_with_action(main_reply_markup)

    if await check_admin_access(chat_id=chat_id, role_df=hse_role_df):
        main_reply_markup = await add_inline_keyboard_with_action_for_admin(main_reply_markup)

    if await check_super_user_access(chat_id=chat_id, role_df=hse_role_df):
        main_reply_markup = await add_correct_inline_keyboard_with_action_for_super_user(main_reply_markup)

    text: str = 'Выберите действие'
    await bot_send_message(chat_id=chat_id, text=text, reply_markup=main_reply_markup)


async def add_correct_inline_keyboard_with_action(markup: types.InlineKeyboardMarkup):
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    """
    if not markup:
        markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(
        'получить данные',
        callback_data=posts_cb.new(id='-', action='bagration_user_get_data'))
    )

    return markup


async def add_inline_keyboard_with_action_for_admin(markup: types.InlineKeyboardMarkup):
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """
    markup.add(types.InlineKeyboardButton(
        'BG AD Выгрузить отчет по пропускам',
        callback_data=posts_cb.new(id='-', action='bagration_admin_get_pass_report'))
    )
    markup.add(types.InlineKeyboardButton(
        text='BG AD Добавить пользователя',
        callback_data=posts_cb.new(id='-', action='bagration_admin_add_user')))
    return markup


async def add_correct_inline_keyboard_with_action_for_super_user(markup: types.InlineKeyboardMarkup):
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """
    markup.add(types.InlineKeyboardButton(
        text='SU BG сменить роль',
        callback_data=posts_cb.new(id='-', action='bagration_super_user_change_role')))

    return markup


async def check_admin_access(chat_id: int | str, role_df: DataFrame = None):
    """

    :param role_df:
    :param chat_id:
    :return:
    """
    admin_id_list: list = await get_id_list(
        hse_user_id=chat_id, user_role='hse_role_is_admin', hse_role_df=role_df
    )
    if not admin_id_list:
        logger.warning(f'{await fanc_name()} access fail {chat_id = }')
        await user_access_fail(chat_id, hse_id=chat_id)
        return False

    if chat_id not in admin_id_list:
        logger.warning(f'{await fanc_name()} access fail {chat_id = }')
        return False

    logger.info(f"user_access_granted for {chat_id = }")
    await user_access_granted(chat_id, role=await fanc_name(), notify=True)
    return True


async def check_super_user_access(chat_id: int | str, role_df: DataFrame = None):
    """

    :param role_df:
    :param chat_id:
    :return:
    """
    super_user_id_list: list = await get_id_list(
        hse_user_id=chat_id, user_role='hse_role_is_super_user', hse_role_df=role_df
    )
    if not super_user_id_list:
        logger.warning(f'{await fanc_name()} access fail {chat_id = }')
        await user_access_fail(chat_id, hse_id=chat_id)
        return False

    if chat_id not in super_user_id_list:
        logger.warning(f'{await fanc_name()} access fail {chat_id = }')
        return False

    logger.info(f"user_access_granted for {chat_id = }")
    await user_access_granted(chat_id, role=await fanc_name())
    return True


async def user_access_fail(chat_id: int, notify_text: str = None, hse_id: str = None):
    """Отправка сообщения о недостатке прав
    """
    hse_id = hse_id if hse_id else chat_id

    try:
        part_1 = f"{await msg(hse_id, cat='error', msge='access_fail', default=Messages.default_answer_text).g_mas()}"
        part_2 = f"{await msg(hse_id, cat='help', msge='help_message', default=Messages.help_message).g_mas()}"
        answer_text = f'{part_1}\n\n{part_2}'
        print(f'{answer_text = }')

        await bot_send_message(chat_id=chat_id, text=answer_text, disable_web_page_preview=True)
        return

    except Exception as err:
        logger.error(f'User {chat_id} ошибка уведомления пользователя {repr(err)}')
        await admin_notify(user_id=chat_id, notify_text=notify_text)

    finally:
        if not notify_text:
            notify_text: str = f'User {chat_id} попытка доступа к функциям без регистрации'

        logger.error(notify_text)
        button = types.InlineKeyboardButton('user_actions',
                                            callback_data=posts_cb.new(id='-', action=f'admin_user_actions_{chat_id}'))
        await admin_notify(
            user_id=chat_id,
            notify_text=notify_text,
            button=button
        )


async def user_access_granted(chat_id: int, role: str = None, notify=False):
    """Отправка сообщения - доступ разрешен"""

    reply_markup = types.InlineKeyboardMarkup()
    reply_markup.add(types.InlineKeyboardButton(text=f'{chat_id}', url=f"tg://user?id={chat_id}"))

    notify_text: str = f'доступ разрешен {chat_id = } {role = }'
    logger.debug(notify_text)
    if notify:
        await admin_notify(user_id=chat_id, notify_text=notify_text)


async def get_id_list(hse_user_id: str | int, user_role: str = None, hse_role_df: DataFrame = None) -> list:
    """Получение id"""

    if not await check_dataframe_role(hse_role_df, hse_user_id):
        hse_role_df: DataFrame = await get_bagration_role_receive_df()
        if not await check_dataframe_role(hse_role_df, hse_user_id):
            return []

    try:
        current_act_violations_df: DataFrame = hse_role_df.loc[
            hse_role_df[user_role] == 1]

    except Exception as err:
        logger.error(f"loc dataframe {repr(err)}")
        return []

    unique_hse_telegram_id: list = current_act_violations_df.hse_telegram_id.unique().tolist()
    if not unique_hse_telegram_id:
        return []

    return unique_hse_telegram_id


async def get_bagration_role_receive_df() -> DataFrame | None:
    """Получение df с ролями пользователя

    :return:
    """

    db_table_name: str = 'core_hseuser'
    kwargs: dict = {
        "action": 'SELECT',
        "subject": '*',
    }
    query: str = await QueryConstructor(table_name=db_table_name, **kwargs).prepare_data()
    datas_query: list = await db_get_data_list(query=query)
    if not datas_query:
        return None

    if not isinstance(datas_query, list):
        return None

    clean_headers: list = await db_get_clean_headers(table_name=db_table_name)
    if not clean_headers:
        return None

    try:
        hse_role_receive_df: DataFrame = DataFrame(datas_query, columns=clean_headers)
    except Exception as err:
        logger.error(f"create_dataframe {repr(err)}")
        return None

    return hse_role_receive_df


async def check_dataframe_role(dataframe: DataFrame, hse_user_id: str | int) -> bool:
    """Проверка dataframe на наличие данных

    :param dataframe:
    :param hse_user_id: id пользователя
    :return:
    """
    if dataframe is None:
        # text_violations: str = 'не удалось получить данные!'
        # logger.error(f'{hse_user_id = } {text_violations}')
        return False

    if dataframe.empty:
        logger.error(f'{hse_user_id = } {Messages.Error.dataframe_is_empty}')
        return False

    return True


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])


async def test():
    chat_id = '373084462'

    # if not notify_text:
    notify_text: str = f'User {chat_id} попытка доступа к функциям без регистрации'

    logger.error(notify_text)
    button = types.InlineKeyboardButton('user_actions',
                                        callback_data=posts_cb.new(id='-', action=f'admin_user_actions_{chat_id}'))
    await admin_notify(
        user_id=chat_id,
        notify_text=notify_text,
        button=button
    )


if __name__ == '__main__':
    asyncio.run(test())
