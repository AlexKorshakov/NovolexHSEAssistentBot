from __future__ import annotations

import traceback
from itertools import chain
from pprint import pprint

from aiogram import types
from aiogram.dispatcher import FSMContext

from apps.MyBot import MyBot
from apps.core.bot.data.board_config import BoardConfig as board_config
from apps.core.bot.filters.custom_filters import filter_is_group
from apps.core.bot.handlers.group.group_text_processing import (data_text_reader,
                                                                processing_text_violation,
                                                                processing_data_text_work)
from loader import logger


# @MyBot.dp.message_handler(filter_is_group, content_types=['text'], state='*')
@MyBot.dp.message_handler(filter_is_group, content_types=types.ContentType.ANY, state='*')
async def text_message_handler_in_group(message: types.Message, album: list[types.Message] = None,
                                        state: FSMContext = None, chat_id: str | int = None,
                                        user_id: str | int = None) -> bool:
    chat_id = chat_id if chat_id else message.chat.id
    user_id = user_id if user_id else message.from_user.id

    if not message.caption and not message.photo:
        return False

    # if not await check_user_access(chat_id=user_id): return

    current_state = MyBot.dp.current_state(user=user_id)
    v_data: dict = await current_state.get_data()
    # pprint(f'{__name__} {await fanc_name()} {v_data = }', width=200)

    await current_state.finish()
    logger.debug(f'{await fanc_name()} state is finish {current_state = }')

    start_text_mes_id = await board_config(current_state).set_data("start_text_mes_id", message.message_id)
    logger.debug(f"{__name__} {await fanc_name()} start_text_mes_id {chat_id=} {user_id=} {start_text_mes_id}")

    data_text_list: list = await data_text_reader(message, user_id, chat_id, text_message=message.caption)
    if not data_text_list or not isinstance(data_text_list, list):
        return False

    result = await processing_text_violation(message, album=album, user_id=user_id, chat_id=chat_id, state=state)
    return result
    # data_text = [item for item in data_text_list if '#нарушение' in item]
    # if data_text and data_text_list[0] == '#нарушение':
    #     result = await processing_text_violation(message, album=album, user_id=user_id, chat_id=chat_id, state=state)
    #     return result
    #
    # data_text = [item for item in list(chain(*data_text_list)) if '#нарушение' in item]
    # if data_text and data_text_list[0] == '#нарушение':
    #     result = await processing_text_violation(message, album=album, user_id=user_id, chat_id=chat_id, state=state)
    #     return result
    #
    # data_text = [item for item in data_text_list if '#работа' in item]
    # if data_text and data_text_list[0] == '#работа':
    #     result = await processing_data_text_work(message, album=album, user_id=user_id, chat_id=chat_id, state=state)
    #     return result
    #
    # data_text = [item for item in list(chain(*data_text_list)) if '#работа' in item]
    # if data_text and data_text_list[0] == '#работа':
    #     result = await processing_data_text_work(message, album=album, user_id=user_id, chat_id=chat_id, state=state)
    #     return result


# @MyBot.dp.message_handler(filter_is_group, content_types=["photo"], state='*')
# async def photo_handler_in_group(message: types.Message, state: FSMContext, chat_id: str | int = None,
#                                  user_id: str | int = None):
#     """Обработчик сообщений с фото
#     """
#     chat_id = chat_id if chat_id else message.chat.id
#     user_id = user_id if user_id else message.from_user.id
#
#     # if not await check_user_access(chat_id=user_id): return
#
#     current_state = MyBot.dp.current_state(user=user_id)
#     v_data: dict = await current_state.get_data()
#     pprint(f'{__name__} {await fanc_name()} {v_data = }', width=200)
#
#     await current_state.finish()
#     logger.info(f'{await fanc_name()} state is finish {current_state = }')
#
#     # if not get_sett(cat='enable_features', param='use_photo_handler').get_set():
#     #     msg_text: str = f"{await msg(chat_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
#     #     await bot_send_message(chat_id=chat_id, text=msg_text, disable_web_page_preview=True)
#     #     return
#     #
#     # logger.info("photo_handler get photo")
#     # if await qr_code_processing(message, state=state):
#     #     return
#
#     start_photo_message_id = await board_config(state).set_data("start_violation_mes_id", message.message_id)
#     logger.info(f"start_photo_message_id message.from_user.id {start_photo_message_id}")
#
#     # await preparing_violation_data(message=message, state=state, chat_id=hse_user_id)
#     #
#     # await download_photo(message, hse_user_id)
#
#
# @MyBot.dp.message_handler(filter_is_group, content_types=types.ContentType.ANY, state='*')
# async def text_message_handler_in_group(message: types.Message, state: FSMContext = None, chat_id: str | int = None,
#                                         user_id: str | int = None) -> bool:
#     if message.chat.type not in ['group', 'supergroup']:
#         return False
#
#     chat_id = chat_id if chat_id else message.chat.id
#     user_id = user_id if user_id else message.from_user.id
#
#     # if not await check_user_access(chat_id=user_id): return
#
#     current_state = MyBot.dp.current_state(user=user_id)
#     v_data: dict = await current_state.get_data()
#     pprint(f'{__name__} {await fanc_name()} {v_data = }', width=200)
#
#     await current_state.finish()
#     logger.info(f'{await fanc_name()} state is finish {current_state = }')


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])
