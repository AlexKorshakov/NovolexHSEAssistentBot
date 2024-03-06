from __future__ import annotations
import asyncio
import math
import traceback
from datetime import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup
from pandas import DataFrame

from apps.MyBot import MyBot, bot_send_message, bot_delete_markup
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.data.board_config import BoardConfig as board_config
from apps.core.bot.handlers.correct_entries.correct_support import create_user_dataframe, check_dataframe
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb, build_inlinekeyboard
from apps.core.bot.messages.messages import Messages, LogMessage
from apps.core.database.db_utils import (db_get_data_list,
                                         db_get_clean_headers,
                                         db_get_data_dict_from_table_with_id)
from apps.core.database.query_constructor import QueryConstructor
from loader import logger


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['correct_acts']), state='*')
async def call_correct_acts(call: types.CallbackQuery = None, callback_data: dict = None, state: FSMContext = None,
                            user_id: int | str = None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST
    """

    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {callback_data = }')

    # await bot_delete_markup(message=call.message)

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    query_kwargs: dict = {
        "action": 'SELECT',
        "subject": '*',
        "conditions": {
            "finished_id": "!= 1",
            "status_id": "!= 1",
        },
    }
    query: str = await QueryConstructor(None, 'core_violations', **query_kwargs).prepare_data()

    violations_dataframe: DataFrame = await create_lite_dataframe_from_query(query=query, table_name='core_violations')
    if not await check_dataframe(violations_dataframe, hse_user_id):
        text_violations: str = 'Незакрытых актов не обнаружено!'
        await bot_send_message(chat_id=hse_user_id, text=text_violations)
        return True

    user_violations: DataFrame = await create_user_dataframe(hse_user_id, violations_dataframe)
    if not await check_dataframe(user_violations, hse_user_id):
        text_violations: str = 'Незакрытых актов не обнаружено!'
        await bot_send_message(chat_id=hse_user_id, text=text_violations)
        return True

    if user_violations.empty:
        return False

    text_violations: str = await text_processor_user_violations(user_violations)

    reply_markup: types.InlineKeyboardMarkup = await add_correct_inline_keyboard_with_action(user_violations,
                                                                                             state=state)

    await bot_send_message(chat_id=hse_user_id, text=text_violations, reply_markup=reply_markup)

    # msg_id = call.message.message_id
    # await bot_delete_message(chat_id=hse_user_id, message_id=msg_id, sleep_sec=15)

    return True


@MyBot.dp.callback_query_handler(lambda call: 'act_number_' in call.data)
async def act_number_answer(call: types.CallbackQuery, user_id: str = None) -> None:
    """Обработка ответов
    """

    act_number = call.data.split('_')[-1]

    hse_user_id = call.message.chat.id if call else user_id
    logger.info(f'{hse_user_id = } {call.data = }')

    await bot_delete_markup(message=call.message)

    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "act_number": act_number,
        },
    }
    query: str = await QueryConstructor(None, 'core_violations', **query_kwargs).prepare_data()

    violations_dataframe: DataFrame = await create_lite_dataframe_from_query(query=query, table_name='core_violations')
    if not await check_dataframe(violations_dataframe, hse_user_id):
        return

    text_act: str = await text_processor_items_act_violations(violations_dataframe, act_number=act_number)

    for item_txt in await text_processor(text=text_act):
        await bot_send_message(chat_id=hse_user_id, text=item_txt)

    text_violations = f'Выбрано {act_number}'

    reply_markup: InlineKeyboardMarkup = await add_act_inline_keyboard_with_action()

    reply_markup.add(types.InlineKeyboardButton(
        text='Скачать акт',
        callback_data=posts_cb.new(id='-', action='correct_act_download')))

    await bot_send_message(chat_id=hse_user_id, text=f'{text_violations}', reply_markup=reply_markup)


async def add_act_inline_keyboard_with_action():
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """

    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton('Финализировать и записать',
                                          callback_data=posts_cb.new(id='-', action='correct_act_finalize')))
    markup.add(types.InlineKeyboardButton('Исправить отдельные пункты',
                                          callback_data=posts_cb.new(id='-', action='correct_act_item_correct')))
    markup.add(types.InlineKeyboardButton('Удалить номер из базы',
                                          callback_data=posts_cb.new(id='-', action='correct_act_delete_from_base')))
    markup.add(types.InlineKeyboardButton('Удалить акт и пункты',
                                          callback_data=posts_cb.new(id='-', action='correct_act_delete')))
    return markup


async def add_correct_inline_keyboard_with_action(user_violations: DataFrame, state: FSMContext = None):
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """

    unique_acts_numbers: list = user_violations.act_number.unique().tolist()
    unique_acts_numbers: list = [f'act_number_{item}' for item in unique_acts_numbers if item]

    menu_level = await board_config(state, "menu_level", 1).set_data()
    menu_list = await board_config(state, "menu_list", unique_acts_numbers).set_data()
    count_col = await board_config(state, "count_col", 2).set_data()

    reply_markup = await build_inlinekeyboard(some_list=menu_list, num_col=count_col, level=menu_level)
    return reply_markup


async def get_hse_role_receive_notifications_list() -> list:
    """Получение списка пользователей кому отправляются уведомления
    """
    db_table_name: str = 'core_hseuser'
    kwargs: dict = {
        "action": 'SELECT',
        "subject": '*',
    }
    query: str = await QueryConstructor(table_name=db_table_name, **kwargs).prepare_data()
    datas_query: list = await db_get_data_list(query=query)

    if not datas_query:
        return []

    if not isinstance(datas_query, list):
        return []

    clean_headers: list = await db_get_clean_headers(table_name=db_table_name)
    if not clean_headers:
        return []

    try:
        hse_role_receive_df: DataFrame = DataFrame(datas_query, columns=clean_headers)
    except Exception as err:
        logger.error(f"create_dataframe {repr(err)}")
        return []

    current_act_violations_df: DataFrame = hse_role_receive_df.loc[
        hse_role_receive_df['hse_role_receive_notifications'] == 1
        ]

    unique_hse_telegram_id: list = current_act_violations_df.hse_telegram_id.unique().tolist()

    return unique_hse_telegram_id


async def text_processor_user_violations(user_violations: DataFrame) -> str:
    """Формирование текста для отправки пользователю"""

    unique_acts_numbers: list = user_violations.act_number.unique().tolist()

    act_description: list = []
    len_unique_acts: int = 0
    for act_number in unique_acts_numbers:

        if not act_number:
            continue

        query_kwargs: dict = {
            "action": 'SELECT', "subject": '*',
            "conditions": {
                "act_number": act_number,
            },
        }
        query: str = await QueryConstructor(None, 'core_violations', **query_kwargs).prepare_data()

        violations_dataframe: DataFrame = await create_lite_dataframe_from_query(
            query=query, table_name='core_violations')

        if violations_dataframe.empty:
            logger.error(f'{Messages.Error.dataframe_is_empty}  \n{query = }')

        len_act_violations: int = len(violations_dataframe) if not violations_dataframe.empty else 0

        act_violations_df = user_violations.copy(deep=True)
        current_act_violations: DataFrame = act_violations_df.loc[act_violations_df['act_number'] == act_number]

        unclosed_points_df = current_act_violations.loc[current_act_violations['status_id'] != 1]
        unclosed_points: int = len(unclosed_points_df)

        query_kwargs: dict = {
            "action": 'SELECT',
            "subject": '*',
            "conditions": {
                "act_number": act_number,
            },
        }
        query: str = await QueryConstructor(None, 'core_actsprescriptions', **query_kwargs).prepare_data()

        violations_dataframe: DataFrame = await create_lite_dataframe_from_query(
            query=query, table_name='core_actsprescriptions')

        if violations_dataframe is None:
            logger.error(f'{Messages.Error.dataframe_is_empty}  \n{query = }')
            continue

        if violations_dataframe.empty:
            logger.error(f'{Messages.Error.dataframe_is_empty}  \n{query = }')
            continue

        act_date = violations_dataframe.act_date.unique().tolist()[0]

        general_constractor_id = violations_dataframe.act_general_contractor_id.unique().tolist()[-1]

        general_constractor: str = await get_item_title_for_id(
            table_name='core_generalcontractor', item_id=general_constractor_id
        )

        item_info = f'Ном: {act_number} от {act_date} {general_constractor} всего пунктов: {len_act_violations} Незакрыто: {unclosed_points}'
        act_description.append(item_info)
        len_unique_acts += 1

    non_acts_items_df: DataFrame = user_violations.loc[user_violations['act_number'] == '']
    non_acts_items: int = len(non_acts_items_df)
    non_acts_text: str = f'Записей вне актов всего: {non_acts_items}'

    header_text: str = f'У вас есть незакрытые акты: Всего актов {len_unique_acts}'

    acts_text: str = '\n'.join(act_description)

    final_text: str = f'{header_text} \n\n{acts_text} \n\n{non_acts_text}'
    return final_text


async def create_lite_dataframe_from_query(query: str, table_name: str) -> DataFrame or None:
    """Возвращает list с нарушениями

    :return: DataFrame or None
    """

    if not query:
        logger.error(f"{LogMessage.Check.no_query} ::: {await get_now()}")
        return None

    violations_data: list = await db_get_data_list(query=query)

    if not violations_data:
        logger.debug(f"{LogMessage.Check.no_violations} ::: {await get_now()}")
        return None

    clean_headers = await db_get_clean_headers(table_name=table_name)

    try:
        dataframe = DataFrame(violations_data, columns=clean_headers)
        return dataframe
    except Exception as err:
        logger.error(f"create_dataframe {repr(err)}")
        return None


async def text_processor_items_act_violations(user_violations_df: DataFrame, act_number: str | int) -> str:
    """Формирование текста для отправки пользователю"""

    if not act_number:
        return ''

    if user_violations_df.empty:
        logger.error(f'{Messages.Error.dataframe_is_empty}')
        return ''

    items_description: list = []

    unique_name: list = user_violations_df.name.unique().tolist()
    unique_created_at: list = user_violations_df.created_at.unique().tolist()

    unique_status_id: list = user_violations_df.status_id.unique().tolist()
    item_status_id = max(unique_status_id)

    unique_general_contractor_id: list = user_violations_df.general_contractor_id.unique().tolist()
    unique_main_location_id: list = user_violations_df.main_location_id.unique().tolist()

    unique_id: list = user_violations_df.id.unique().tolist()

    unique_sub_location_id: list = user_violations_df.sub_location_id.unique().tolist()

    sub_location = [await get_item_title_for_id(table_name='core_sublocation', item_id=item)
                    for item in unique_sub_location_id]

    created_at = unique_created_at[-1]

    item_status = await get_item_title_for_id(
        'core_status', item_id=item_status_id
    )
    # item_main_category = await get_item_title_for_id(
    #     table_name='core_maincategory', item_id=item_df['main_category_id'].values[0]
    # )
    # item_category = await get_item_title_for_id(
    #     table_name='core_category', item_id=item_df['category_id'].values[0]
    # )
    item_general_contractor_id = await get_item_title_for_id(
        table_name='core_generalcontractor', item_id=unique_general_contractor_id[0]
    )
    item_main_location = await get_item_title_for_id(
        table_name='core_mainlocation', item_id=unique_main_location_id[-1]
    )
    # item_sub_location = await get_item_title_for_id(
    #     table_name='core_sublocation', item_id=item_df['sub_location_id'].values[0]
    # )
    # item_description = item_df['description'].values[0]
    #
    # elimination_time = await get_item_title_for_id(
    #     table_name='core_eliminationtime', item_id=item_df['elimination_time_id'].values[0]
    # )
    # normative_documents_title = await get_item_title_for_id(
    #     table_name='core_normativedocuments', item_id=item_df['normative_documents_id'].values[0],
    # )
    # normative_documents_desc = await get_item_title_for_id(
    #     table_name='core_normativedocuments', item_id=item_df['normative_documents_id'].values[0],
    #     item_name='normative'
    # )

    item_info = f'Акт Ном: {act_number} от {created_at}\n Статус: {item_status} \n\n' \
                f'количество пунктов {len(unique_id)} \n' \
                f'Выдал {unique_name[-1]} \n' \
                f'Подрядчик: {item_general_contractor_id} \n' \
                f'Территория: {item_main_location} - {", ".join(sub_location)} \n' \
        # f'Устранить до: {elimination_time} ' \
    # f'Направление: {item_main_category} - Категория: {item_category}\n' \
    # f'Описание: {item_description} \n' \
    # f'Подкатегория: {normative_documents_title} ' \
    # f'Нормативка: {normative_documents_desc}\n'

    items_description.append(item_info)

    items_text: str = '\n'.join(items_description)

    header_text: str = f'Пункты акта {act_number}'
    final_text: str = f'{header_text} \n\n{items_text}'
    return final_text


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


async def get_item_title_for_id(table_name: str, item_id: int, item_name: str = None) -> str:
    """

    :param item_name:
    :param table_name:
    :param item_id:
    :return:
    """
    item_dict: dict = await db_get_data_dict_from_table_with_id(
        table_name=table_name,
        post_id=item_id
    )

    item_name = item_name if item_name else 'title'
    item_text: str = item_dict.get(item_name, '')
    return item_text


async def get_now() -> str:
    """Возвращает текущую дату и время.
    :return: str
    """
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")


def say_fanc_name():
    stack = traceback.extract_stack()
    return str(stack[-2][2])


async def test():
    await call_correct_acts(user_id='373084462')


if __name__ == '__main__':
    asyncio.run(test())
