from __future__ import annotations

import asyncio

from aiogram import types
from aiogram.dispatcher import FSMContext
from pandas import DataFrame

from apps.core.bot.messages.messages_test import msg
from loader import logger
from apps.MyBot import MyBot, bot_send_message, bot_delete_message, bot_delete_markup
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages import Messages
from apps.core.database.query_constructor import QueryConstructor
from apps.core.database.transformation_category import CATEGORY_ID_TRANSFORM

from apps.core.bot.handlers.correct_entries.correct_acts import call_correct_acts
from apps.core.bot.handlers.correct_entries.correct_non_act_item_item_correct import (create_lite_dataframe_from_query,
                                                                                      COLUMNS_DICT)
from apps.core.bot.handlers.correct_entries.correct_support_updater import update_column_value
from apps.core.bot.handlers.correct_entries.correct_violations_complex_meaning_handler import complex_meaning_handler
from apps.core.bot.handlers.correct_entries.correct_violations_special_meaning_handler import special_meaning_handler
from apps.core.bot.handlers.correct_entries.correct_violations_simple_meaning_handler import simple_meaning_handler
from apps.core.bot.handlers.correct_entries.correct_violations_text_meaning_handler import text_meaning_handler
from apps.core.bot.handlers.correct_entries.correct_support import (spotter_data,
                                                                    get_item_number_from_call,
                                                                    check_dataframe,
                                                                    check_spotter_data,
                                                                    get_violations_df)


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['correct_characteristic_not']))
async def call_correct_characteristic_not(call: types.CallbackQuery, callback_data: dict[str, str],
                                          user_id: int | str = None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {callback_data = }')

    await bot_delete_markup(message=call.message)

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    await bot_delete_message(chat_id=hse_user_id, message_id=call.message.message_id, sleep_sec=15)


@MyBot.dp.callback_query_handler(lambda call: 'correct_character' in call.data, state='*')
async def call_correct_character_answer(call: types.CallbackQuery, user_id: int | str = None,
                                        state: FSMContext = None) -> None:
    """Обработка ответов
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {call.data = }')

    await bot_delete_markup(message=call.message)

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    item_number_text = await get_item_number_from_call(call, hse_user_id)
    if not item_number_text: return

    character_part: list = call.message.values['text'].split('_')[1:-1]
    character: str = '_'.join(character_part)
    character_id: None = None

    logger.debug(f'{hse_user_id = } {item_number_text = } {character = } {character_id = }')

    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "id": item_number_text,
        },
    }
    query: str = await QueryConstructor(None, 'core_violations', **query_kwargs).prepare_data()

    violations_dataframe: DataFrame = await create_lite_dataframe_from_query(query=query, table_name='core_violations')
    if not await check_dataframe(violations_dataframe, hse_user_id):
        return

    type_character = await determine_type_characteristic(character)

    if type_character == 'other_meaning':
        # TODO Delete
        logger.error(f'{hse_user_id = } Messages.Error.error_action')
        msg_text = await msg(hse_user_id, cat='error', msge='error_action', default=Messages.Error.error_action).g_mas()
        await bot_send_message(chat_id=hse_user_id, text=msg_text)

    elif type_character == 'complex_meaning':
        result = await complex_meaning_handler(
            hse_user_id, character, item_number_text, violations_dataframe, state=state
        )
    elif type_character == 'simple_meaning':
        result = await simple_meaning_handler(
            hse_user_id, character, item_number_text, violations_dataframe, state=state
        )
    elif type_character == 'text_meaning':
        result = await text_meaning_handler(
            hse_user_id, character, item_number_text, violations_dataframe, state=state
        )
    elif type_character == 'special_meaning':
        result = await special_meaning_handler(
            hse_user_id, character, item_number_text, violations_dataframe, state=state
        )
    return result

    # character_table_name = RESULT_DICT.get(character, None)
    #
    # if not character_table_name:
    #     logger.error(f'{hse_user_id = } {item_number_text = } {character = } not character in character_table_name')
    #     await bot_send_message(chat_id=hse_user_id, text=f'Ошибка при изменении показателя {character = }')
    #     return
    #
    # if character_table_name:
    #     query_kwargs: dict = {
    #         "action": 'SELECT', "subject": '*',
    #     }
    #     query: str = await QueryConstructor(None, character_table_name, **query_kwargs).prepare_data()
    #     table_dataframe: DataFrame = await create_lite_dataframe_from_query(
    #         query=query, table_name=character_table_name
    #     )
    #     if not await check_dataframe(table_dataframe, hse_user_id):
    #         return
    #
    #     if 'title' not in table_dataframe.columns.values.tolist():
    #         return
    #
    #     title_list: list = table_dataframe['id'].tolist()
    #     title_list: list = [f"item_{item}" for item in title_list if item is not None]
    #
    #     menu_level = board_config.menu_level = 1
    #     count_col = board_config.count_col = 1
    #
    #     reply_markup = await build_inlinekeyboard(
    #         some_list=title_list, num_col=count_col, level=menu_level, calld_prefix=f"corr_{character_table_name}_"
    #     )
    #
    #     character_text: str = await text_processor_character_text(
    #         table_dataframe, character, item_number_text, hse_user_id
    #     )
    #
    #     await bot_send_message(
    #         chat_id=hse_user_id, text=character_text, reply_markup=reply_markup
    #     )
    #
    #     spotter_data['calld_prefix'] = f"corr_{character_table_name}_"
    #     spotter_data['character_table_name'] = f"{character_table_name}"
    #     spotter_data['hse_user_id'] = f"{hse_user_id}"
    #     spotter_data['item_number_text'] = f"{item_number_text}"
    #     spotter_data['character'] = f"{character}"
    #
    # await bot_delete_message(chat_id=hse_user_id, message_id=call.message.message_id, sleep_sec=15)


#
#
# async def text_processor_character_text(table_dataframe: DataFrame, character: str,
#                                         item_number_text: str | int, hse_user_id: str | int) -> str:
#     """Формирование текста для отправки пользователю
#
#     """
#
#     unique_items_ids: list = table_dataframe.id.unique().tolist()
#     unique_items_titles: list = table_dataframe.title.unique().tolist()
#
#     items_text_list: list = []
#     for i, (item_id, item_title) in enumerate(zip(unique_items_ids, unique_items_titles), 1):
#         item_info: str = f'item_{item_id} : {item_title}'
#         items_text_list.append(item_info)
#         logger.debug(f'{i} :: {item_info}')
#
#     items_text: str = '\n'.join(items_text_list)
#     # Todo нахера это здесь?
#     if '_id' in character:
#         CATEGORY_ID_TRANSFORM
#
#     # item_number_text = await get_item_number_from_call(call, hse_user_id)
#     # if not item_number_text: return
#
#     query_kwargs: dict = {
#         "action": 'SELECT', "subject": '*',
#         "conditions": {
#             "id": item_number_text,
#         },
#     }
#     query: str = await QueryConstructor(None, 'core_violations', **query_kwargs).prepare_data()
#
#     violations_dataframe: DataFrame = await create_lite_dataframe_from_query(query=query, table_name='core_violations')
#     if not await check_dataframe(violations_dataframe, hse_user_id):
#         return ''
#
#     text_violations_decription: str = await get_item_title_for_id(
#         table_name='core_sublocation', item_id=violations_dataframe.sub_location_id.values[0]
#     )
#
#     character_title: str = COLUMNS_DICT.get(character, None)
#
#     header_text: str = f'Выберите значение для показателя Изменить "{character_title}" для ' \
#                        f'записи item_number_{item_number_text}'
#
#     old_text: str = f'Значение в базе {text_violations_decription}'
#
#     footer_text: str = 'Нажмите на кнопку с номером выбранного значения'
#
#     final_text: str = f'{header_text} \n\n{old_text}\n\n{items_text}  \n\n{footer_text}'
#     return final_text


@MyBot.dp.callback_query_handler(lambda call: 'characteristic_' in call.data)
async def call_characteristic_answer(call: types.CallbackQuery, user_id: str = None) -> None:
    """Обработка ответов

    """
    characteristic_text = call.data

    hse_user_id = call.message.chat.id if call else user_id
    logger.info(f'{hse_user_id = } {call.data = }')

    await bot_delete_markup(message=call.message)

    text_violations = f'Выбрано {characteristic_text}\n\n'
    reply_markup = await add_act_inline_keyboard_with_action()
    await bot_send_message(chat_id=hse_user_id, text=text_violations, reply_markup=reply_markup)

    await bot_delete_message(chat_id=hse_user_id, message_id=call.message.message_id, sleep_sec=15)


@MyBot.dp.callback_query_handler(lambda call: 'corr_' in call.data)
async def call_correct_item_answer(call: types.CallbackQuery, user_id: str | int = None):
    """Обработка ответов
    """

    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {call.data = }')

    await bot_delete_markup(message=call.message)

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    if not await check_spotter_data():
        return

    item_number: str = spotter_data.get('item_number_text', None)
    character: str = spotter_data.get('character', None)
    character_id: str = call.data.split('_')[-1]

    violations_dataframe = await get_violations_df(item_number, hse_user_id)
    if not await check_dataframe(violations_dataframe, hse_user_id):
        return

    await update_column_value(
        hse_user_id, character, character_id, item_number, violations_dataframe
    )

    # type_character = await determine_type_characteristic(character)
    #
    # if type_character == 'other_meaning':
    #     await bot_send_message(chat_id=hse_user_id, text=Messages.Error.error_action)
    #
    # elif type_character == 'complex_meaning':
    #     result = await complex_meaning_handler(hse_user_id, character, character_id, item_number, violations_dataframe)
    #
    # elif type_character == 'simple_meaning':
    #     result = await simple_meaning_handler(hse_user_id, character, character_id, item_number, violations_dataframe)
    #
    # elif type_character == 'text_meaning':
    #     result = await text_meaning_handler(hse_user_id, character, item_number, violations_dataframe)

    await call_correct_acts(user_id=hse_user_id)

    # await bot_delete_message(chat_id=hse_user_id, message_id=call.message.message_id, sleep_sec=15)


async def determine_type_characteristic(characteristic: str) -> str:
    """Определение вида характеристики


    :return:
    """

    if characteristic in ['normative_documents_id', 'sub_location_id']:
        type_char = 'complex_meaning'
        return type_char

    if characteristic in ['comment', 'description', ]:
        type_char = 'text_meaning'
        return type_char

    if characteristic in ['photo', 'json', 'act_number', 'is_published', 'agreed_id']:
        type_char = 'special_meaning'
        return type_char

    if characteristic in ['normative_documents_id', 'sub_location_id']:
        type_char = 'simple_meaning'
        return type_char

    if characteristic in ['title', 'file_id', 'is_published', 'violation_id']:
        type_char = 'other_meaning'
        return type_char


async def add_act_inline_keyboard_with_action():
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Изменить значение',
                                          callback_data=posts_cb.new(id='-', action='correct_character')))
    markup.add(types.InlineKeyboardButton('Отмена',
                                          callback_data=posts_cb.new(id='-', action='correct_characteristic_not')))
    return markup


async def test():
    keys = COLUMNS_DICT.keys()

    des_list: list = []
    for key in keys:
        if '_id' in key:
            key_i = key.replace('_id', '')
            if not CATEGORY_ID_TRANSFORM.get(key_i, None):
                print(f'{key = }')
                continue

            des_list.append(CATEGORY_ID_TRANSFORM[key_i].get('description', None))
        else:
            if not CATEGORY_ID_TRANSFORM.get(key, None):
                print(f'{key = }')
                continue

            des_list.append(CATEGORY_ID_TRANSFORM[key].get('description', None))

    print('\n'.join(des_list))


if __name__ == '__main__':
    asyncio.run(test())
