from __future__ import annotations

import re
import traceback
from datetime import datetime, timedelta

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from loader import logger
from apps.MyBot import MyBot, bot_send_message, bot_edit_message
from apps.core.bot.data.board_config import BoardConfig as board_config
from apps.core.bot.handlers.admin_func.admin_write_data_in_database import write_new_user_data_in_database
from apps.core.bot.filters.custom_filters import (is_admin_add_user_progress,
                                                  admin_add_user_role_item,
                                                  admin_add_user_role_update_role,
                                                  admin_add_user_stop
                                                  )
from apps.core.bot.messages.messages import Messages
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import (move_action,
                                                                        build_inlinekeyboard,
                                                                        build_text_for_inlinekeyboard,
                                                                        posts_cb)
from apps.core.database.db_utils import (db_get_data_list,
                                         db_get_clean_headers,
                                         db_update_column_value_for_query)
from apps.core.database.query_constructor import QueryConstructor


class AdminAddUserState(StatesGroup):
    hse_full_name = State()
    hse_full_name_dative = State()
    hse_short_name = State()
    hse_full_name_telegram = State()
    hse_function = State()
    hse_function_dative = State()
    hse_department = State()
    hse_department_dative = State()
    hse_add_roles = State()

    hse_add_finish = State()


hse_user_data_dict_default: list[dict] = [
    {'id': 1, 'title': 'hse_is_work', 'value': 1},
    {'id': 2, 'title': 'hse_status', 'value': 1},
    {'id': 3, 'title': 'hse_status_comment', 'value': "на вахте"},
    {'id': 4, 'title': 'hse_organization', 'value': 1},
    {'id': 5, 'title': 'hse_role_is_author', 'value': 0},
    {'id': 6, 'title': 'hse_role_is_developer', 'value': 0},
    {'id': 7, 'title': 'hse_role_is_admin', 'value': 0},
    {'id': 8, 'title': 'hse_role_is_coordinating_person', 'value': 0},
    {'id': 9, 'title': 'hse_role_is_super_user', 'value': 0},
    {'id': 10, 'title': 'hse_role_is_user', 'value': 1},
    {'id': 11, 'title': 'hse_role_is_subcontractor', 'value': 0},
    {'id': 12, 'title': 'hse_role_receive_notifications', 'value': 0},
    {'id': 13, 'title': 'hse_role_is_user_bagration', 'value': 1},
    {'id': 14, 'title': 'hse_role_is_emploee_tc', 'value': 1},
    {'id': 15, 'title': 'hse_location', 'value': 1},
    {'id': 16, 'title': 'hse_work_shift', 'value': 1},
]


@MyBot.dp.callback_query_handler(move_action.filter(action=["pre_paragraph"]), state=AdminAddUserState.all_states)
async def previous_paragraph_answer(call: types.CallbackQuery, callback_data: dict,
                                    user_id: int | str = None, state: FSMContext = None):
    """Обработка ответов содержащихся в previous_paragraph
    """
    if callback_data['pre_val'] == 'admin_add_user_progress':
        await admin_add_user_progress(call, callback_data, state=state)

    elif callback_data['pre_val'] == 'hse_full_name':
        await process_hse_full_name(call.message, state=state)

    elif callback_data['pre_val'] == "hse_full_name_dative":
        await process_hse_full_name_dative(call.message, state=state)

    elif callback_data['pre_val'] == "hse_short_name":
        await process_hse_short_name(call.message, state=state)

    elif callback_data['pre_val'] == "hse_full_name_telegram":
        await process_hse_full_name_telegram(call.message, state=state)

    elif callback_data['pre_val'] == "hse_function":
        await process_hse_function(call.message, state=state)

    elif callback_data['pre_val'] == "hse_function_dative":
        await process_hse_function_dative(call.message, state=state)

    elif callback_data['pre_val'] == "hse_department":
        await process_hse_department(call.message, state=state)

    elif callback_data['pre_val'] == "hse_department_dative":
        await process_hse_department_dative(call.message, state=state)

    elif callback_data['pre_val'] == "hse_add_stoped":
        await process_hse_add_finish(call.message, state=state)


@MyBot.dp.callback_query_handler(is_admin_add_user_progress, state='*')
async def admin_add_user_progress(call: types.CallbackQuery, callback_data: dict[str, str] = None,
                                  state: FSMContext = None, user_id: int | str = None):
    """Обработка ответов содержащихся в admin_add_user_progress
    """
    hse_user_id: int | str = call.message.chat.id if call else user_id
    await notify_user_for_choice(call, data_answer=call.data)

    user_for_action: str = call.data.split(':')[-1].replace('admin_add_add_user_progress_', '')
    print(f'{user_for_action = }')

    await set_add_user_atr_data("title", user_for_action, state=state)
    await set_add_user_atr_data("user_telegram_id", user_for_action, state=state)
    await set_add_user_atr_data("hse_telegram_id", user_for_action, state=state)
    await set_add_user_atr_data("hse_is_work", 1, state=state)
    await set_add_user_atr_data("hse_status", 1, state=state)
    await set_add_user_atr_data("hse_language_code", 'ru', state=state)

    await bot_send_message(chat_id=hse_user_id, text=Messages.AddUser.hse_full_name)

    # Вызов состояния ожидания текстового ответа от пользователя
    await AdminAddUserState.hse_full_name.set()
    return True


@MyBot.dp.message_handler(content_types=["text"], state=AdminAddUserState.hse_full_name)
async def process_hse_full_name(message: types.Message, state: FSMContext = None, user_id: int | str = None):
    """Обработчик состояния process_hse_full_name
    """
    hse_user_id: int | str = message.chat.id if message else user_id
    await notify_user_for_choice(message, data_answer=message.text)
    await set_add_user_atr_data("hse_full_name", message.text, state=state)

    previous_level: str = 'admin_add_user_progress'
    await board_config(state, "previous_level", previous_level).set_data()

    reply_markup = await build_inlinekeyboard(previous_level=previous_level, state=state)
    await bot_send_message(chat_id=hse_user_id, text=Messages.AddUser.hse_full_name_dative, reply_markup=reply_markup)

    await AdminAddUserState.hse_full_name_dative.set()
    return True


@MyBot.dp.message_handler(content_types=["text"], state=AdminAddUserState.hse_full_name_dative)
async def process_hse_full_name_dative(message: types.Message, state: FSMContext = None, user_id: int | str = None):
    """Обработчик состояния process_hse_full_name_dative
    """
    hse_user_id: int | str = message.chat.id if message else user_id
    await notify_user_for_choice(message, data_answer=message.text)
    await set_add_user_atr_data("hse_full_name_dative", message.text, state=state)

    previous_level: str = 'hse_full_name'
    await board_config(state, "previous_level", previous_level).set_data()

    reply_markup = await build_inlinekeyboard(previous_level=previous_level, state=state)
    await bot_send_message(chat_id=hse_user_id, text=Messages.AddUser.hse_short_name, reply_markup=reply_markup)

    await AdminAddUserState.hse_short_name.set()
    return True


@MyBot.dp.message_handler(content_types=["text"], state=AdminAddUserState.hse_short_name)
async def process_hse_short_name(message: types.Message, state: FSMContext = None, user_id: int | str = None):
    """Обработчик состояния process_hse_short_name
    """
    hse_user_id: int | str = message.chat.id if message else user_id
    await notify_user_for_choice(message, data_answer=message.text)
    await set_add_user_atr_data("hse_short_name", message.text, state=state)

    previous_level: str = 'hse_full_name_dative'
    await board_config(state, "previous_level", previous_level).set_data()

    reply_markup = await build_inlinekeyboard(previous_level=previous_level, state=state)
    await bot_send_message(chat_id=hse_user_id, text=Messages.AddUser.hse_full_name_telegram, reply_markup=reply_markup)

    await AdminAddUserState.hse_full_name_telegram.set()
    return True


@MyBot.dp.message_handler(content_types=["text"], state=AdminAddUserState.hse_full_name_telegram)
async def process_hse_full_name_telegram(message: types.Message, state: FSMContext = None, user_id: int | str = None):
    """Обработчик состояния process_hse_full_name_telegram
    """
    hse_user_id: int | str = message.chat.id if message else user_id
    await notify_user_for_choice(message, data_answer=message.text)
    await set_add_user_atr_data("hse_full_name_telegram", message.text, state=state)

    previous_level: str = 'hse_short_name'
    await board_config(state, "previous_level", previous_level).set_data()

    reply_markup = await build_inlinekeyboard(previous_level=previous_level, state=state)
    await bot_send_message(chat_id=hse_user_id, text=Messages.AddUser.hse_function, reply_markup=reply_markup)

    await AdminAddUserState.hse_function.set()
    return True


@MyBot.dp.message_handler(content_types=["text"], state=AdminAddUserState.hse_function)
async def process_hse_function(message: types.Message, state: FSMContext = None, user_id: int | str = None):
    """Обработчик состояния process_hse_function
    """
    hse_user_id: int | str = message.chat.id if message else user_id
    await notify_user_for_choice(message, data_answer=message.text)
    await set_add_user_atr_data("hse_function", message.text, state=state)

    previous_level: str = 'hse_full_name_telegram'
    await board_config(state, "previous_level", previous_level).set_data()

    reply_markup = await build_inlinekeyboard(previous_level=previous_level, state=state)
    await bot_send_message(chat_id=hse_user_id, text=Messages.AddUser.hse_function_dative, reply_markup=reply_markup)

    await AdminAddUserState.hse_function_dative.set()
    return True


@MyBot.dp.message_handler(content_types=["text"], state=AdminAddUserState.hse_function_dative)
async def process_hse_function_dative(message: types.Message, state: FSMContext = None, user_id: int | str = None):
    """Обработчик состояния process_hse_function_dative
    """
    hse_user_id: int | str = message.chat.id if message else user_id
    await notify_user_for_choice(message, data_answer=message.text)
    await set_add_user_atr_data("hse_function_dative", message.text, state=state)

    previous_level: str = 'hse_function'
    await board_config(state, "previous_level", previous_level).set_data()

    reply_markup = await build_inlinekeyboard(previous_level=previous_level, state=state)
    await bot_send_message(chat_id=hse_user_id, text=Messages.AddUser.hse_department, reply_markup=reply_markup)

    await AdminAddUserState.hse_department.set()
    return True


@MyBot.dp.message_handler(content_types=["text"], state=AdminAddUserState.hse_department)
async def process_hse_department(message: types.Message, state: FSMContext = None, user_id: int | str = None):
    """Обработчик состояния process_hse_department
    """
    hse_user_id: int | str = message.chat.id if message else user_id
    await notify_user_for_choice(message, data_answer=message.text)
    await set_add_user_atr_data("hse_department", message.text, state=state)

    previous_level: str = 'hse_function_dative'
    await board_config(state, "previous_level", previous_level).set_data()

    reply_markup = await build_inlinekeyboard(previous_level=previous_level, state=state)
    await bot_send_message(chat_id=hse_user_id, text=Messages.AddUser.hse_department_dative, reply_markup=reply_markup)

    await AdminAddUserState.hse_department_dative.set()
    return True


@MyBot.dp.message_handler(content_types=["text"], state=AdminAddUserState.hse_department_dative)
async def process_hse_department_dative(message: types.Message, state: FSMContext = None, user_id: int | str = None):
    """Обработчик состояния process_hse_department_dative
    """
    hse_user_id: int | str = message.chat.id if message else user_id
    await notify_user_for_choice(message, data_answer=message.text)
    await set_add_user_atr_data("hse_department_dative", message.text, state=state)

    previous_level: str = 'hse_department'
    await board_config(state, "previous_level", previous_level).set_data()

    reply_markup = await build_inlinekeyboard(previous_level=previous_level, state=state)
    await bot_send_message(chat_id=hse_user_id, text=Messages.AddUser.hse_add_finish, reply_markup=reply_markup)
    await AdminAddUserState.hse_add_roles.set()
    await process_hse_add_finish(message, state, user_id)
    return True


@MyBot.dp.message_handler(state=AdminAddUserState.hse_add_finish)
async def process_hse_add_finish(message: types.Message, state: FSMContext = None, user_id: int | str = None):
    """Обработчик состояния process_hse_department_dative
    :param message:
    :param state:
    :param user_id:
    :return:
    """
    hse_user_id: int | str = message.chat.id if message else user_id
    await notify_user_for_choice(message, data_answer=message.text)
    await set_add_user_atr_data("hse_department_dative", message.text, state=state)

    previous_level: str = 'hse_department_dative'
    await board_config(state, "previous_level", previous_level).set_data()

    for item in hse_user_data_dict_default:
        await board_config(state, item.get('title'), item.get('value')).set_data()

    v_data: dict = await state.get_data()
    user_for_action: int | dict = v_data.get('hse_telegram_id', None)
    reply_markup: types.InlineKeyboardMarkup = await add_inline_keyboard_with_action(user_for_action)
    await bot_send_message(chat_id=hse_user_id, text=Messages.AddUser.hse_add_finish, reply_markup=reply_markup)
    return True


async def add_inline_keyboard_with_action(user_for_action=None) -> types.InlineKeyboardMarkup:
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """
    markup: types.InlineKeyboardMarkup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(
        text='Ввод обязательных данных',
        callback_data=posts_cb.new(id='-', action=f'admin_add_add_user_progress_{user_for_action}'))
    )
    markup.add(types.InlineKeyboardButton(
        text='Настройка ролей',
        callback_data=posts_cb.new(id='-', action=f'admin_add_add_user_role_item_{user_for_action}'))
    )
    markup.add(types.InlineKeyboardButton(
        text='Записать и завершить',
        callback_data=posts_cb.new(id='-', action=f'admin_add_add_user_stop_{user_for_action}'))
    )
    return markup


@MyBot.dp.callback_query_handler(admin_add_user_role_item, state='*')
async def call_admin_add_add_user_role_item(call: types.CallbackQuery, callback_data: dict[str, str] = None,
                                            state: FSMContext = None):
    """Обработка ответов содержащихся в s_user_enable_features
    """
    hse_user_id: int | str = call.message.chat.id
    await notify_user_for_choice(call, data_answer=call.data)

    param_list: list = await get_param_list(state)

    title_list: list = [f"item_{item.get('title')}" for item in param_list if item.get('title') is not None]
    text_list: list = [f"{await get_character_text(item)}" for item in param_list if item.get('title') is not None]

    menu_level: int = await board_config(state, "menu_level", 1).set_data()
    menu_list: list = await board_config(state, "menu_list", title_list).set_data()
    menu_text_list: list = await board_config(state, "menu_text_list", text_list).set_data()
    count_col: int = await board_config(state, "count_col", 2).set_data()
    prefix: str = await board_config(state, "prefix", 'hse_role_').set_data()
    await board_config(state, "call_fanc_name", 'hse_add_roles').set_data()
    previous_level: str = 'hse_add_stoped'
    await board_config(state, "previous_level", previous_level).set_data()

    reply_markup = await build_inlinekeyboard(
        some_list=menu_list, num_col=count_col, level=menu_level,
        called_prefix=prefix, use_search=True, previous_level=previous_level, state=state
    )
    reply_text: str = await build_text_for_inlinekeyboard(
        some_list=menu_text_list, level=menu_level
    )
    await bot_send_message(
        chat_id=hse_user_id, text=reply_text, reply_markup=reply_markup
    )


@MyBot.dp.callback_query_handler(admin_add_user_role_update_role, state=AdminAddUserState.all_states)
async def process_hse_add_roles(call: types.CallbackQuery, user_id: str = None, state: FSMContext = None) -> None:
    """Обработчик состояния process_hse_department_dative
    """

    hse_user_id: int | str = call.message.chat.id if call else user_id
    await notify_user_for_choice(call, data_answer=call.data)

    title = call.data.replace('hse_role_item_', '')

    v_data: dict = await state.get_data()
    user_for_action: int | str = v_data.get("hse_telegram_id", None)
    param_list: list = await get_all_role(user_for_action)

    title_list: list = [item.get('title') for item in param_list if item.get('title') == title]
    value_list: list = [item.get('value') for item in param_list if item.get('title') == title]
    item_value: int = 0 if value_list[0] == 1 else 1

    table_column_name: str = title
    finished_result_execute: bool = await db_update_column_value_for_query(
        table_name='core_hseuser',
        hse_telegram_id=user_for_action,
        table_column_name=table_column_name,
        item_value=item_value,
    )
    logger.info(f'{hse_user_id = } {title_list[-1]} {item_value = } {"on" if item_value == 1 else "off"}')

    if finished_result_execute:
        param_list: list = await get_param_list(state)

        title_list: list = [f"item_{item.get('title')}" for item in param_list if item.get('title') is not None]
        text_list: list = [f"{await get_character_text(item)}" for item in param_list if item.get('title') is not None]

        v_data: dict = await state.get_data()
        menu_level: int = v_data['menu_level']
        menu_list: list = await board_config(state, "menu_list", title_list).set_data()
        menu_text_list: list = await board_config(state, "menu_text_list", text_list).set_data()
        count_col: int = await board_config(state, "count_col", 2).set_data()
        prefix: str = await board_config(state, "prefix", 'hse_role_').set_data()
        await board_config(state, "call_fanc_name", 'hse_add_roles').set_data()
        previous_level: str = 'hse_add_stoped'
        await board_config(state, "previous_level", previous_level).set_data()

        reply_markup = await build_inlinekeyboard(
            some_list=menu_list, num_col=count_col, level=menu_level,
            called_prefix=prefix, previous_level=previous_level, state=state
        )
        reply_text = await build_text_for_inlinekeyboard(
            some_list=menu_text_list, level=menu_level
        )
        result = await bot_edit_message(
            hse_user_id=hse_user_id, message_id=call.message.message_id,
            reply_markup=reply_markup, reply_text=reply_text, kvargs={'fanc_name': await fanc_name()}
        )
        logger.info(f'msg: {call.message.message_id} {result = }')


@MyBot.dp.callback_query_handler(admin_add_user_stop, state=AdminAddUserState.all_states)
async def process_admin_add_user_stop(call: types.CallbackQuery, user_id: str = None, state: FSMContext = None) -> None:
    """Обработчик состояния process_hse_department_dative
    """

    hse_user_id = call.message.chat.id if call else user_id
    await notify_user_for_choice(call, data_answer=call.data)

    user_for_action: str = call.data.split(':')[-1].replace('admin_add_add_user_stop_', '')
    print(f'{user_for_action = }')

    user_data: dict = await state.get_data()
    result: bool = await write_new_user_data_in_database(user_data_to_db=user_data, admin_id=hse_user_id)
    if not result:
        await bot_send_message(chat_id=hse_user_id, text=Messages.Error.entry_in_bd_fail)

    await bot_send_message(chat_id=hse_user_id, text=Messages.AddUser.hse_add_finish_success)
    await state.finish()


async def notify_user_for_choice(call_msg: types.CallbackQuery | types.Message, user_id: int | str = None,
                                 data_answer: str = None) -> bool:
    """Уведомление пользователя о выборе + логирование

    :param data_answer:
    :param user_id: int | str id пользователя
    :param call_msg:
    :return: None
    """
    if isinstance(call_msg, types.CallbackQuery):
        for i in ('previous_paragraph', 'move_up', 'move_down'):
            if i in call_msg.data: return True

        mesg_text: str = f"Выбрано: {data_answer}"
        if call_msg.data in call_msg.message.text:
            mesg_list: list = [item for item in call_msg.message.text.split('\n\n') if call_msg.data in item]
            mesg_text = f"Выбрано: {mesg_list[0] if mesg_list else ''}"

        try:
            hse_user_id: int | str = call_msg.message.chat.id if call_msg else user_id
            logger.debug(f"{hse_user_id = } Выбрано: {data_answer} {call_msg.data}")
            await call_msg.message.edit_text(text=mesg_text, reply_markup=None)
            return True

        except Exception as err:
            logger.debug(f"{call_msg.message.chat.id = } {repr(err)}")

    if isinstance(call_msg, types.Message):
        for i in ('previous_paragraph', 'move_up', 'move_down'):
            if i in call_msg.text: return True

        mesg_text: str = f"Выбрано: {data_answer}"
        if call_msg.text:
            mesg_list: list = [item for item in call_msg.text.split('\n\n') if call_msg.text in item]
            mesg_text = f"Выбрано: {mesg_list[0] if mesg_list else ''}"

        try:
            hse_user_id: int | str = call_msg.chat.id if call_msg else user_id
            logger.debug(f"{hse_user_id = } Выбрано: {data_answer} {call_msg.text}")
            await call_msg.edit_text(text=mesg_text, reply_markup=None)
            return True

        except Exception as err:
            logger.debug(f"{call_msg.chat.id = } {repr(err)}")


async def get_param_list(state: FSMContext) -> list:
    """Получение параметров"""
    v_data: dict = await state.get_data()
    user_for_action: int | str = v_data.get("hse_telegram_id", None)
    param_list: list = await get_all_role(user_for_action)

    return param_list


async def get_all_role(user_id: int | str) -> list:
    """Получение ролей пользователя по user_id"""
    table_data: list = await get_list_table_values(user_id)
    if not table_data:
        logger.error(f'access fail {user_id = } {table_data =}')
        return []

    clean_headers: list = await db_get_clean_headers(table_name='core_hseuser')
    hse_user_data_dict: dict = dict(zip(clean_headers, table_data))

    if not hse_user_data_dict:
        logger.error(f'access fail {user_id = } {hse_user_data_dict =}')
        return []

    hse_user_role_dict: dict = await get_dict_hse_user_role(hse_user_data_dict)
    logger.debug(f'{user_id = } ::: {hse_user_role_dict = }')

    list_dicts: list = [{'title': k, 'value': v} for k, v in hse_user_role_dict.items()]
    return list_dicts


async def get_list_table_values(user_id: int) -> list:
    """Получение данных таблицы по chat_id

    :param user_id:
    :return:
    """
    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {"hse_telegram_id": user_id, },
    }
    query: str = await QueryConstructor(None, 'core_hseuser', **query_kwargs).prepare_data()
    datas_query: list = await db_get_data_list(query=query)

    if not datas_query:
        return []

    if not isinstance(datas_query, list):
        return []

    return list(datas_query[0])


async def get_dict_hse_user_role(hse_user_data_dict: dict) -> dict:
    """Получение ролей пользователя из hse_user_data_dict

    :param hse_user_data_dict: dict - данные для формирования ответа
    :return: dict - dict с данными о ролях пользователя
    """
    if not isinstance(hse_user_data_dict, dict):
        logger.error(f"Error in () {await fanc_name()} user_data_to_db: {hse_user_data_dict = }")
        return {}

    hse_roles: list = [name for name, value in hse_user_data_dict.items() if re.search(r'_role_', name)]
    hse_roles_dict: dict = {name: value for name, value in hse_user_data_dict.items() if name in hse_roles}

    return dict(hse_roles_dict)


async def get_character_text(param_list: list | dict) -> list | str:
    """Формирование текста из param_list

    :param param_list: list | dict - данные для формирования ответа
    :return: list | str - ответ в зависимости от входящих параметров
    """
    if isinstance(param_list, list):
        if not param_list: return []
        text_list: list = [
            f"item {item.get('id')} {item.get('title')} \nvalue : {'on' if item.get('value') else 'off'}"
            for item in param_list if item.get('id') is not None
        ]
        return text_list

    if isinstance(param_list, dict):
        if not param_list: return ''
        text_list: str = f"item {param_list.get('title')}" \
                         f"\nvalue : {'on' if param_list.get('value') else 'off'}"
        return text_list


async def set_add_user_atr_data(atr_name: str, art_val: str | int, state: FSMContext = None, **kvargs) -> bool:
    """Запись данных  атрибута 'atr_name': art_val глобального словаря violation_data в файл json

    :param atr_name: str имя ключа
    :param art_val: str|int значение ключа
    :param state: : FSMContext - текущее состояние пользователя
    :param kvargs: dict - дополнительные параметры
    :return: bool True если успешно.
    """
    logger.debug(f'set_violation_atr_data: {atr_name = } {art_val = }')

    if not atr_name:
        return False

    await state.update_data({atr_name: art_val})
    return True


async def get_today(delta: int = None) -> str:
    """Получение значения текуще даты со смещением

    :param delta: int - величина смещения в часах
    :return: str - значение текущей даты
    """
    delta: int = delta if delta else 0
    return (datetime.today() + timedelta(hours=delta)).strftime("%d.%m.%Y")


async def fanc_name() -> str:
    """Получение имени вызывающей функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])
