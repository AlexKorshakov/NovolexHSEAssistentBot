from __future__ import annotations

import asyncio

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, InlineKeyboardMarkup
from pandas import DataFrame

from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.handlers.correct_entries.correct_support_updater import update_column_value
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages_test import msg
from loader import logger
import apps.xxx
from apps.MyBot import bot_send_message, MyBot
from apps.core.bot.filters.custom_filters import filter_is_private
from apps.core.bot.handlers.correct_entries.correct_non_act_item_item_correct import RESULT_DICT, COLUMNS_DICT
from apps.core.bot.handlers.correct_entries.correct_support import check_dataframe, create_lite_dataframe_from_query, \
    spotter_data, check_spotter_data, get_violations_df
from apps.core.bot.messages.messages import Messages
from apps.core.bot.states import CorrectViolationsState
from apps.core.database.query_constructor import QueryConstructor


async def special_meaning_handler(hse_user_id: int | str, character: str, item_number: int | str,
                                  violations_dataframe: DataFrame, state: FSMContext = None) -> bool:
    """Обработка специальных характеристик

    :param hse_user_id: int | str id пользователя.
    :param violations_dataframe: DataFrame - DataFrame с данными записи
    :param item_number:  int | str номер записи в база данных
    :param character: str - название изменяемой характеристики записи.
    :return: bool - True если успешно or False
    """
    character_table_name: str = RESULT_DICT.get(character, None)

    if not character_table_name:
        logger.error(f'{hse_user_id = } {item_number = } {character = } not character in character_table_name')
        await bot_send_message(chat_id=hse_user_id, text=f'Ошибка при изменении показателя {character = }')
        return False

    # TODO Delete
    logger.error(f'{hse_user_id = } Messages.Error.error_action')
    msg_text = await msg(hse_user_id, cat='error', msge='error_action', default=Messages.Error.error_action).g_mas()
    await bot_send_message(chat_id=hse_user_id, text=msg_text)
