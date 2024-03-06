from __future__ import annotations

from loader import logger

logger.debug(f"{__name__} start import")

import asyncio
import math
import traceback
from aiogram.dispatcher import FSMContext
from aiogram import types

from apps.MyBot import MyBot, bot_send_message
from apps.core.database.query_constructor import QueryConstructor
from apps.core.database.db_utils import db_get_data_list
from apps.core.bot.filters.custom_filters import filter_is_hashtag
from apps.core.bot.data.board_config import BoardConfig as board_config
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import (build_inlinekeyboard,
                                                                        build_text_for_inlinekeyboard)
from apps.core.bot.messages.messages import Messages
from apps.core.bot.callbacks.sequential_action.data_answer import notify_user_for_choice
from apps.core.bot.callbacks.sequential_action.category import (_PREFIX_ND,
                                                                _PREFIX_POZ,
                                                                get_data_with_hashtags)
from apps.core.bot.reports.report_data import ViolationData

logger.debug(f"{__name__} finish import")


@MyBot.dp.callback_query_handler(filter_is_hashtag, state=ViolationData.all_states)
async def hashtags_answers(call: types.CallbackQuery, state: FSMContext = None,
                           user_id: str = None, test_data: dict = None, hashtag_data: str = None) -> bool:
    """Обработка ответов содержащихся в hashtags
    """
    hse_user_id = call.message.chat.id if call else user_id
    # logger.info(f'{call.data = }')

    if call: await notify_user_for_choice(call, data_answer=call.data)

    v_data: dict = test_data if test_data else  await state.get_data() or {}
    hashtag_data = hashtag_data if hashtag_data else call.data

    if hashtag_data in await get_data_with_hashtags("core_normativedocuments", item_id=v_data.get('category_id', None)):
        datas_query: list = await is_normativedocument_hashtag(v_data, hashtag=hashtag_data)
        result: bool = await hash_tag_answer(
            datas_query, hse_user_id, previous_level='category', prefix=_PREFIX_ND, state=state,
            message_text=Messages.Choose.normative_documents
        )
        return result

    if hashtag_data in await get_data_with_hashtags("core_sublocation", item_id=v_data.get('main_location_id', None)):
        datas_query: list = await is_sublocation_hashtag(v_data, hashtag=hashtag_data)
        result: bool = await hash_tag_answer(
            datas_query, hse_user_id, previous_level='main_location', prefix=_PREFIX_POZ, state=state,
            message_text=Messages.Choose.sub_location
        )
        return result


async def is_sublocation_hashtag(v_data: dict, hashtag: str) -> list:
    logger.info(f'{__name__} {await fanc_name()}')
    kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "main_location_id": v_data.get('main_location_id', None),
            "hashtag": hashtag,
            "hashtag_condition": 'like',
        }
    }
    query: str = await QueryConstructor(table_name='core_sublocation', **kwargs).prepare_data()
    datas_query: list = await db_get_data_list(query=query)
    return datas_query


async def is_normativedocument_hashtag(v_data: dict, hashtag: str) -> list:
    logger.info(f'{__name__} {await fanc_name()}')
    kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "category_id": v_data.get('category_id', None),
            "hashtag": hashtag,
            "hashtag_condition": 'like',
        }
    }
    query: str = await QueryConstructor(table_name='core_normativedocuments', **kwargs).prepare_data()
    datas_query: list = await db_get_data_list(query=query)
    return datas_query


async def get_character_text(param_list: list | str) -> list | str:
    if isinstance(param_list, list):
        if not param_list: return []

        text_list: list = [
            f"item {item.get('id')} {item.get('title')} " for item in param_list if item.get('id') is not None
        ]
        return text_list

    if isinstance(param_list, dict):
        if not param_list: return ''

        text_list: str = f"item {param_list.get('id')} {param_list.get('title')} {param_list.get('comment')} "
        return text_list

    if isinstance(param_list, tuple):
        if not param_list: return ''
        if param_list[0][0] == '#': return ''

        text_list: str = f"{param_list[0]} : {param_list[1]}"
        return text_list


async def text_processor(text: str = None) -> list:
    """Принимает text для формирования list ответа
    Если len(text) <= 3500 - отправляет [сообщение]
    Если len(text) > 3500 - формирует list_with_parts_text = []

    :param text:
    :return: list - list_with_parts_text
    """
    if not text: return []

    step: int = 3500
    if len(text) <= step:
        return [text]

    len_parts: int = math.ceil(len(text) / step)
    list_with_parts_text: list = [text[step * (i - 1):step * i] for i in range(1, len_parts + 1)]
    return list_with_parts_text


async def hash_tag_answer(datas_query: list, user_id: int, previous_level: str, prefix: str, state: FSMContext,
                          message_text: str):
    """Формирование ответа с хештегом

    """
    menu_level = await board_config(state, "menu_level", 1).set_data(call_func=await fanc_name())
    menu_list = await board_config(state, "menu_list", [prefix + str(item[0]) for item in datas_query]).set_data(
        call_func=await fanc_name())
    count_col = await board_config(state, "count_col", 2).set_data(call_func=await fanc_name())
    await board_config(state, "previous_level", previous_level).set_data(call_func=await fanc_name())

    short_title = [prefix + str(item[0]) for item in datas_query]
    data_list = [str(item[2]) for item in datas_query]

    zipped_list: list = list(zip(short_title, data_list))
    text_list: list = [f"{await get_character_text(item)}" for item in zipped_list]
    menu_text_list = await board_config(state, "menu_text_list", text_list).set_data(call_func=await fanc_name())

    reply_markup = await build_inlinekeyboard(
        some_list=menu_list, num_col=count_col, level=menu_level, previous_level=previous_level, state=state
    )
    reply_text = await build_text_for_inlinekeyboard(
        some_list=menu_text_list, level=menu_level
    )
    text: str = f'{message_text}\n\n{reply_text}'
    result: bool = await bot_send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
    return result


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])


async def test_1():
    db_table_name = 'core_normativedocuments'
    hashtag_test = '#Огнетушители'
    query_test: str = f"SELECT * FROM {db_table_name} WHERE `category_id` == {16} AND `hashtags` LIKE '%{hashtag_test}%'"
    logger.info(f'{__name__} {await fanc_name()} {query_test}')

    datas_query_test: list = await db_get_data_list(query=query_test)
    clean_datas_query_test: list = [item[1] for item in datas_query_test]
    short_title = [_PREFIX_ND + str(item[0]) for item in datas_query_test]

    data_list = [item[2] for item in clean_datas_query_test]
    data_text: str = '\n\n'.join(
        f'{item[0]} : {item[1]}' for item in list(zip(short_title, data_list))
    )

    text_list: list = await text_processor(data_text)

    for txt in text_list:
        logger.info(f'{__name__} {await fanc_name()} {txt = }')


async def test_2():
    test_dict = {
        "category_id": 2,
    }
    t_call: types.CallbackQuery = None
    user_id = '373084462'
    hashtag_data: str = '#Удостоверения'
    state = None

    result: bool = await hashtags_answers(
        call=t_call, state=state, user_id=user_id, test_data=test_dict, hashtag_data=hashtag_data
    )
    logger.info(f'{__name__} {await fanc_name()} {result = }')


if __name__ == '__main__':
    # asyncio.run(test_1())
    asyncio.run(test_2())
