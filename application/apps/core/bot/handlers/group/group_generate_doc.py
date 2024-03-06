from __future__ import annotations

from loader import logger

logger.debug(f"{__name__} start import")
import traceback
from pandas import DataFrame
from aiogram import types
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher import FSMContext

from apps.MyBot import MyBot, bot_send_message
from apps.core.utils.misc import rate_limit
from apps.core.settyngs import get_sett
from apps.core.bot.messages.messages_test import msg
from apps.core.bot.messages.messages import Messages
from apps.core.bot.bot_utils.check_access import (check_user_access,
                                                  check_admin_access,
                                                  check_super_user_access,
                                                  get_hse_role_receive_df)
from apps.core.bot.filters.custom_filters import filter_is_private
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb

logger.debug(f"{__name__} finish import")


@rate_limit(limit=10)
@MyBot.dp.message_handler(Command('group_generate'), filter_is_private, state='*')
async def generate_handler(message: types.Message, state: FSMContext = None):
    """Обработка команд генерации документов

    :return:
    """
    chat_id = message.chat.id
    if not await check_user_access(chat_id=chat_id):
        return

    current_state = await state.get_state()
    await state.finish()
    logger.info(f'{await fanc_name()} state is finish {current_state = }')

    if not get_sett(cat='enable_features', param='use_generate_handler').get_set():
        msg_text: str = f"{await msg(chat_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=chat_id, text=msg_text, disable_web_page_preview=True)
        return

    main_reply_markup = types.InlineKeyboardMarkup()
    hse_role_df: DataFrame = await get_hse_role_receive_df()

    if not await check_user_access(chat_id=chat_id, role_df=hse_role_df):
        logger.error(f'access fail {chat_id = }')
        return

    main_reply_markup = await add_period_inline_keyboard_with_action(main_reply_markup)

    if await check_admin_access(chat_id=chat_id, role_df=hse_role_df):
        main_reply_markup = await add_inline_keyboard_with_action_for_admin(main_reply_markup)

    if await check_super_user_access(chat_id=chat_id, role_df=hse_role_df):
        main_reply_markup = await add_inline_keyboard_with_action_for_super_user(main_reply_markup)

    await bot_send_message(chat_id=chat_id, text=Messages.Choose.period, reply_markup=main_reply_markup)


async def add_period_inline_keyboard_with_action(markup: types.InlineKeyboardMarkup):
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """
    markup.add(
            types.InlineKeyboardButton(
                    text='Акт-предписание',
                    callback_data=posts_cb.new(id='-', action='group_generate_act'))
    )
    # markup.add(
    #     types.InlineKeyboardButton(
    #         text='Общий отчет',
    #         callback_data=posts_cb.new(id='-', action='group_generate_report'))
    # )
    # markup.add(
    #     types.InlineKeyboardButton(
    #         text='Статистика',
    #         callback_data=posts_cb.new(id='-', action='group_generate_stat'))
    # )
    return markup


async def add_inline_keyboard_with_action_for_admin(markup: types.InlineKeyboardMarkup):
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """
    # markup.add(
    #     types.InlineKeyboardButton(
    #         text='Статистика',
    #         callback_data=posts_cb.new(id='-', action='group_generate_stat'))
    # )
    markup.add(types.InlineKeyboardButton(
            text='AD за текущую КН',
            callback_data=posts_cb.new(id='-', action='group_generate_stat_current_week_all'))
    )
    return markup


async def add_inline_keyboard_with_action_for_super_user(markup: types.InlineKeyboardMarkup):
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """
    # markup.add(types.InlineKeyboardButton(
    #     text='SU за текущую КН',
    #     callback_data=posts_cb.new(id='-', action=group_generate_act_current_week_all'))
    # )
    return markup


# async def get_role_receive_df() -> DataFrame | None:
#     """Получение df с ролями пользователя
#
#     :return:
#     """
#     db_table_name: str = 'core_hseuser'
#     kwargs: dict = {
#         "action": 'SELECT',
#         "subject": '*',
#     }
#     query: str = await QueryConstructor(table_name=db_table_name, **kwargs).prepare_data()
#     datas_query: list = await db_get_data_list(query=query)
#     if not datas_query:
#         return None
#
#     if not isinstance(datas_query, list):
#         return None
#
#     clean_headers: list = await db_get_clean_headers(table_name=db_table_name)
#     if not clean_headers:
#         return None
#
#     try:
#         hse_role_receive_df: DataFrame = DataFrame(datas_query, columns=clean_headers)
#
#     except Exception as err:
#         logger.error(f"create_dataframe {repr(err)}")
#         return None
#
#     return hse_role_receive_df
#
#
# async def get_id_list(hse_user_id: str | int, user_role: str = None, hse_role_df: DataFrame = None) -> list:
#     """Получение id"""
#
#     if not await check_dataframe_role(hse_role_df, hse_user_id):
#         hse_role_df: DataFrame = await get_hse_role_receive_df()
#         if not await check_dataframe_role(hse_role_df, hse_user_id):
#             return []
#
#     try:
#         current_act_violations_df: DataFrame = hse_role_df.loc[
#             hse_role_df[user_role] == 1]
#
#     except Exception as err:
#         logger.error(f"loc dataframe {repr(err)}")
#         return []
#
#     unique_hse_telegram_id: list = current_act_violations_df.hse_telegram_id.unique().tolist()
#     if not unique_hse_telegram_id:
#         return []
#
#     return unique_hse_telegram_id
#
#
# async def check_dataframe_role(dataframe: DataFrame, hse_user_id: str | int) -> bool:
#     """Проверка dataframe на наличие данных
#
#     :param dataframe:
#     :param hse_user_id: id пользователя
#     :return:
#     """
#     if dataframe is None:
#         # text_violations: str = 'не удалось получить данные!'
#         # logger.error(f'{hse_user_id = } {text_violations}')
#         return False
#
#     if dataframe.empty:
#         logger.error(f'{hse_user_id = } {Messages.Error.dataframe_is_empty}')
#         return False
#
#     return True


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])
