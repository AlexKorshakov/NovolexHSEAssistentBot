from __future__ import annotations

import math
import traceback

from aiogram import types
from aiogram.dispatcher import FSMContext

from apps.MyBot import MyBot, bot_send_message, bot_edit_message
from apps.core.bot.bot_utils.check_access import check_super_user_access, check_user_access
from apps.core.bot.data.board_config import BoardConfig as board_config
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb, build_inlinekeyboard, \
    build_text_for_inlinekeyboard
from apps.core.settyngs import get_sett, DataBaseSettings
from apps.core.utils.misc import rate_limit
from loader import logger


@rate_limit(limit=2)
@MyBot.dp.callback_query_handler(posts_cb.filter(action=['s_user_enable_features']))
async def call_s_user_enable_features(call: types.CallbackQuery, callback_data: dict[str, str],
                                      state: FSMContext = None):
    """Обработка ответов содержащихся в s_user_enable_features
    """
    hse_user_id = call.message.chat.id
    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    if not await check_super_user_access(chat_id=hse_user_id):
        logger.error(f'check_super_user_access fail {hse_user_id = }')
        return

    param_list: list = await get_sett(cat='enable_features').get_all_features()

    title_list: list = [f"item_{item.get('id')}" for item in param_list if item.get('id') is not None]
    text_list: list = [f"{await get_character_text(item)}" for item in param_list if item.get('id') is not None]

    menu_level = await board_config(state, "menu_level", 1).set_data()
    menu_list = await board_config(state, "menu_list", title_list).set_data()
    menu_text_list = await board_config(state, "menu_text_list", text_list).set_data()
    count_col = await board_config(state, "count_col", 2).set_data()
    prefix = await board_config(state, "prefix", 'features_').set_data()
    await board_config(state, "call_fanc_name", 'enable_features').set_data()

    reply_markup = await build_inlinekeyboard(
        some_list=menu_list, num_col=count_col, level=menu_level,
        called_prefix=prefix, use_search=True, state=state
    )

    reply_text: str = await build_text_for_inlinekeyboard(
        some_list=menu_text_list, level=menu_level
    )

    await bot_send_message(
        chat_id=hse_user_id, text=reply_text, reply_markup=reply_markup
    )


async def get_character_text(param_list: list | str) -> list | str:
    """

    :return:
    """

    if isinstance(param_list, list):
        if not param_list: return []

        text_list: list = [
            f"item {item.get('id')} {item.get('title')} {item.get('comment')} \nvalue : " \
            f"{'on' if item.get('value') == 1 else 'off'}"
            for item in param_list if
            item.get('id') is not None
        ]
        return text_list

    if isinstance(param_list, dict):
        if not param_list: return ''

        text_list: str = f"item {param_list.get('id')} {param_list.get('title')} " \
                         f"{param_list.get('comment')} \nvalue : {'on' if param_list.get('value') == 1 else 'off'}"

        return text_list


async def text_processor(text: str = None) -> list:
    """Принимает data_list_to_text[] для формирования текста ответа
    Если len(text) <= 3500 - отправляет [сообщение]
    Если len(text) > 3500 - формирует list_with_parts_text = []

    :param text:
    :return: list - list_with_parts_text
    """
    if not text:
        return []

    step = 3500
    if len(text) <= step:
        return [text]

    len_parts = math.ceil(len(text) / step)
    list_with_parts_text: list = [text[step * (i - 1):step * i] for i in range(1, len_parts + 1)]
    return list_with_parts_text


@MyBot.dp.callback_query_handler(lambda call: 'features_item_' in call.data, state='*')
async def item_number_answer(call: types.CallbackQuery, user_id: str = None, state: FSMContext = None) -> None:
    """Обработка ответов
    """

    hse_user_id = call.message.chat.id if call else user_id
    logger.info(f'{hse_user_id = } {call.data = }')
    logger.info(f'msg: {call.message.message_id}')

    v_data: dict = await state.get_data()

    item_number = call.data.split('_')[-1]

    param_list: list = await get_sett(cat='enable_features').get_all_features()
    title_list: list = [item.get('title') for item in param_list if item.get('id') == int(item_number)]
    value_list: list = [item.get('value') for item in param_list if item.get('id') == int(item_number)]
    item_value = 0 if value_list[0] == 1 else 1

    finished_result_execute: bool = await db_update_table_column_value(
        table_name='sett_enable_features',
        item_number=item_number,
        table_column_name='value',
        item_value=item_value,
    )
    logger.info(f'{hse_user_id = } {title_list[-1]} {item_value = } {"on" if item_value == 1 else "off"}')

    if finished_result_execute:
        param_list: list = await get_sett(cat='enable_features').get_all_features()

        title_list: list = [f"item_{item.get('id')}" for item in param_list if item.get('id') is not None]
        text_list: list = [f"{await get_character_text(item)}" for item in param_list if item.get('id') is not None]

        menu_level = v_data['menu_level']
        menu_list = await board_config(state, "menu_list", title_list).set_data()
        menu_text_list = await board_config(state, "menu_text_list", text_list).set_data()
        count_col = await board_config(state, "count_col", 2).set_data()
        prefix = await board_config(state, "prefix", 'features_').set_data()
        await board_config(state, "call_fanc_name", 'enable_features').set_data()

        reply_markup = await build_inlinekeyboard(
            some_list=menu_list, num_col=count_col, level=menu_level,
            called_prefix=prefix, state=state
        )

        reply_text = await build_text_for_inlinekeyboard(
            some_list=menu_text_list, level=menu_level
        )

        result = await bot_edit_message(
            hse_user_id=hse_user_id, message_id=call.message.message_id,
            reply_markup=reply_markup, reply_text=reply_text, kvargs={'fanc_name': await fanc_name()}
        )

        logger.info(f'msg: {call.message.message_id} {result = }')


async def db_update_table_column_value(*, table_name: str, item_number: str, table_column_name: str,
                                       item_value: str | int) -> bool:
    """Обновление значений item_value в столбце table_column_name строки item_number таблицы table_name

    :param item_number: str - id строки
    :param table_name: str  - имя таблицы для изменений
    :param table_column_name: str  - имя столбца таблицы table_name для изменений
    :param item_value: str  - значение для внесения изменений

    :return: bool true если удачно or false если не удачно
    """
    # TODO заменить на вызов конструктора QueryConstructor
    query: str = f"UPDATE {table_name} SET `{table_column_name}` = {bool(item_value)} WHERE `id` = {item_number}"

    result: bool = await DataBaseSettings().update_column_value(query=query)
    if result:
        return True
    return False


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])
