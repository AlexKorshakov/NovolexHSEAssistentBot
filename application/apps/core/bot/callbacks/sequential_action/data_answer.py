from __future__ import annotations

from pprint import pprint

from loader import logger

logger.debug(f"{__name__} start import")

import traceback
from aiogram import types
from aiogram.dispatcher import FSMContext

from apps.MyBot import bot_send_message
from apps.core.database.transformation_category import CATEGORY_ID_TRANSFORM
from apps.core.bot.data.board_config import BoardConfig as board_config
from apps.core.bot.callbacks.sequential_action.category import get_data_list
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import (build_inlinekeyboard,
                                                                        build_text_for_inlinekeyboard,
                                                                        send_error_message)
from apps.core.bot.reports.report_data import ViolationData

logger.debug(f"{__name__} finish import")


async def get_and_send_start_location_data(call: types.CallbackQuery, user_id: int | str = None,
                                           state: FSMContext = None, context: str = None) -> bool:
    """Получение данных main_locations

    :param context: str (опционально) - переключатель - this / next level 
    :param state: FSMContext - текущее состояние пользователя chat_id
    :param user_id: int | str id пользователя
    :param call:
    :return: bool
    """
    hse_user_id = call.message.chat.id if call else user_id

    call_func, _ = await get_part_name(await fanc_name())
    this_level_data_dict = CATEGORY_ID_TRANSFORM[call_func]

    await notify_user_for_choice(call, data_answer=call.data)

    context = context if context else 'this_level'
    call_func = await fanc_name()
    answer_dict = await prepare_answer_data(
        hse_user_id, this_level_data_dict, state=state, call_func=call_func, context=context,
    )
    if not answer_dict: return False

    await set_board_config(hse_user_id, answer_dict, state=state, call_func=call_func)
    await check_and_send_message(hse_user_id, answer_dict, state=state, call_func=call_func)

    return True


async def get_and_send_location_data(call: types.CallbackQuery, user_id: int | str = None,
                                     state: FSMContext = None, context: str = None) -> bool:
    """Получение данных main_locations

    :param context: str (опционально) - переключатель - this / next level
    :param state: FSMContext - текущее состояние пользователя chat_id
    :param user_id: int | str id пользователя
    :param call:
    :return: bool
    """
    hse_user_id = call.message.chat.id if call else user_id

    call_func, _ = await get_part_name(await fanc_name())
    this_level_data_dict = CATEGORY_ID_TRANSFORM[call_func]

    await notify_user_for_choice(call, data_answer=call.data)

    call_func = await fanc_name()
    context = context if context else 'next_level'
    answer_dict = await prepare_answer_data(
        hse_user_id, this_level_data_dict, state=state, call_func=call_func, context=context
    )
    if not answer_dict: return False

    await set_board_config(hse_user_id, answer_dict, state=state, call_func=call_func)
    await check_and_send_message(hse_user_id, answer_dict, state=state, call_func=call_func)
    return True


async def get_and_send_main_location_data(call: types.CallbackQuery, user_id: int | str = None,
                                          state: FSMContext = None, context: str = None) -> bool:
    """Получение данных main_locations

    :param context: str (опционально) - переключатель - this / next level
    :param state: FSMContext - текущее состояние пользователя chat_id
    :param user_id: int | str id пользователя
    :param call:
    :return: bool
    """
    hse_user_id = call.message.chat.id if call else user_id

    call_func, _ = await get_part_name(await fanc_name())
    this_level_data_dict = CATEGORY_ID_TRANSFORM[call_func]

    await notify_user_for_choice(call, data_answer=call.data)

    previous_level = this_level_data_dict['previous_level']
    v_data: dict = await state.get_data()

    level = ''
    level_message = ''
    context = context if context else 'next_level'

    if context == 'this_level':
        text: str = this_level_data_dict['this_level_message']
        level_message: str = text

    if context == 'next_level':
        text: str = this_level_data_dict['next_level_message']
        level_message: str = text

        level = this_level_data_dict['next_level']

    menu_list = await get_data_list(level,
                                    category=v_data[this_level_data_dict['item']],
                                    condition='short_title'
                                    )
    logger.debug(f'{menu_list = }')
    data_list = await get_data_list(level,
                                    category=v_data[this_level_data_dict['item']],
                                    condition='data_list'
                                    )
    call_func = await fanc_name()
    menu_level = await board_config(state, "menu_level", 1).set_data(call_func=call_func)
    menu_list = await board_config(state, "menu_list", menu_list).set_data(call_func=call_func)
    count_col = await board_config(state, "count_col", 2).set_data(call_func=call_func)

    level_message = await board_config(state, "level_message", level_message).set_data(call_func=call_func)
    await board_config(state, "use_list_message", True).set_data(call_func=call_func)
    await board_config(state, "previous_level", previous_level).set_data(call_func=call_func)

    zipped_list: list = list(zip(menu_list, data_list))
    text_list: list = [f"{await get_character_text(item)}" for item in zipped_list]
    menu_text_list = await board_config(state, "menu_text_list", text_list).set_data(call_func=call_func)

    reply_markup = await build_inlinekeyboard(
        some_list=menu_list, num_col=count_col, level=menu_level, previous_level=previous_level, use_search=True,
        state=state
    )
    reply_text = await build_text_for_inlinekeyboard(
        some_list=menu_text_list, level=menu_level
    )

    text = f"{level_message}\n\n{reply_text}"
    # await bot_send_message(chat_id=hse_user_id, text=text, reply_markup=reply_markup)
    answer_dict = {'reply_markup': reply_markup, 'text': text, }
    if not answer_dict: return False

    await check_and_send_message(hse_user_id, answer_dict, state=state, call_func=call_func)
    return True


async def get_and_send_null_sub_locations_data(call: types.CallbackQuery, user_id: int | str = None,
                                               state: FSMContext = None, context: str = None) -> bool:
    """Получение данных sub_location

    :param context: str (опционально) - переключатель - this / next level
    :param state: FSMContext - текущее состояние пользователя chat_id
    :param user_id: int | str id пользователя
    :param call:
    :return: bool
    """
    hse_user_id = call.message.chat.id if call else user_id

    call_func, _ = await get_part_name(await fanc_name())
    this_level_data_dict = CATEGORY_ID_TRANSFORM[call_func]

    await notify_user_for_choice(call, data_answer=call.data)

    call_func = await fanc_name()
    context = context if context else 'next_level'
    answer_dict = await prepare_answer_data(
        hse_user_id, this_level_data_dict, state=state, call_func=call_func, context=context
    )
    if not answer_dict:
        return False

    await set_board_config(hse_user_id, answer_dict, state=state, call_func=call_func)
    await check_and_send_message(hse_user_id, answer_dict, state=state, call_func=call_func)
    return True


async def get_and_send_sub_locations_data(call: types.CallbackQuery, user_id: int | str = None,
                                          state: FSMContext = None, context: str = None) -> bool:
    """Получение данных sub_location

    :param context: str (опционально) - переключатель - this / next level
    :param state: FSMContext - текущее состояние пользователя chat_id
    :param user_id: int | str id пользователя
    :param call:
    :return: bool
    """
    hse_user_id = call.message.chat.id if call else user_id

    call_func, _ = await get_part_name(await fanc_name())
    this_level_data_dict = CATEGORY_ID_TRANSFORM[call_func]

    await notify_user_for_choice(call, data_answer=call.data)

    call_func = await fanc_name()
    context = context if context else 'next_level'
    answer_dict = await prepare_answer_data(
        hse_user_id, this_level_data_dict, state=state, call_func=call_func, context=context
    )
    if not answer_dict: return False

    await set_board_config(hse_user_id, answer_dict, state=state, call_func=call_func)
    await check_and_send_message(hse_user_id, answer_dict, state=state, call_func=call_func)
    return True


async def get_and_send_main_category_data(call: types.CallbackQuery, user_id: int | str = None,
                                          state: FSMContext = None, context: str = None) -> bool:
    """Получение данных sub_location

    :param context: str (опционально) - переключатель - this / next level
    :param state: FSMContext - текущее состояние пользователя chat_id
    :param user_id: int | str id пользователя
    :param call:
    :return: bool
    """
    hse_user_id = call.message.chat.id if call else user_id

    call_func, _ = await get_part_name(await fanc_name())
    this_level_data_dict = CATEGORY_ID_TRANSFORM[call_func]

    await notify_user_for_choice(call, data_answer=call.data)

    call_func = await fanc_name()
    context = context if context else 'next_level'
    answer_dict = await prepare_answer_data(
        hse_user_id, this_level_data_dict, state=state, call_func=call_func, context=context
    )
    if not answer_dict: return False

    await set_board_config(hse_user_id, answer_dict, state=state, call_func=call_func)
    await check_and_send_message(hse_user_id, answer_dict, state=state, call_func=call_func)
    return True


async def get_and_send_category_data(call: types.CallbackQuery, user_id: int | str = None,
                                     state: FSMContext = None, context: str = None) -> bool:
    """ Получение данных category

    :param context: str (опционально) - переключатель - this / next level
    :param state: FSMContext - текущее состояние пользователя chat_id
    :param user_id: int | str id пользователя
    :param call:
    :return: bool
    """
    hse_user_id = call.message.chat.id if call else user_id

    call_func, _ = await get_part_name(await fanc_name())
    this_level_data_dict = CATEGORY_ID_TRANSFORM[call_func]

    await notify_user_for_choice(call, data_answer=call.data)

    previous_level = this_level_data_dict['previous_level']

    level = ''
    level_message = ''
    context = context if context else 'next_level'

    if context == 'this_level':
        text: str = this_level_data_dict['this_level_message']
        level_message: str = text

    if context == 'next_level':
        text: str = this_level_data_dict['next_level_message']
        level_message: str = text

        level = this_level_data_dict['next_level']

    v_data: dict = await state.get_data()

    menu_list = await get_data_list(level,
                                    category=v_data[this_level_data_dict['item']],
                                    condition='short_title'
                                    )
    data_list = await get_data_list(level,
                                    category=v_data[this_level_data_dict['item']],
                                    condition='data_list'
                                    )

    menu_level = await board_config(state, "menu_level", 1).set_data(call_func=await fanc_name())
    menu_list = await board_config(state, "menu_list", menu_list).set_data(call_func=await fanc_name())
    count_col = await board_config(state, "count_col", 2).set_data(call_func=await fanc_name())
    await board_config(state, "previous_level", previous_level).set_data(call_func=await fanc_name())
    await board_config(state, "use_list_message", True).set_data(call_func=call_func)

    level_message = await board_config(state, "level_message", level_message).set_data(call_func=call_func)

    zipped_list: list = list(zip(menu_list, data_list))

    text_list: list = [f"{await get_character_text(item)}" for item in zipped_list]
    menu_text_list = await board_config(state, "menu_text_list", text_list).set_data(call_func=await fanc_name())

    reply_markup = await build_inlinekeyboard(
        some_list=menu_list, num_col=count_col, level=menu_level, previous_level=previous_level, use_search=True,
        state=state
    )
    reply_text = await build_text_for_inlinekeyboard(
        some_list=menu_text_list, level=menu_level
    )

    text = f"{level_message}\n\n{reply_text}"
    # await bot_send_message(chat_id=hse_user_id, text=text, reply_markup=reply_markup)

    answer_dict = {'reply_markup': reply_markup, 'text': text, }
    if not answer_dict: return False

    await check_and_send_message(hse_user_id, answer_dict, state=state, call_func=call_func)
    return True


async def get_and_send_null_normative_documents_data(call: types.CallbackQuery, user_id: int | str = None,
                                                     state: FSMContext = None, context: str = None) -> bool:
    """ Получение данных normative_documents

    :param context: str (опционально) - переключатель - this / next level
    :param state: FSMContext - текущее состояние пользователя chat_id
    :param user_id: int | str id пользователя
    :param call:
    :return: bool
    """
    hse_user_id = call.message.chat.id if call else user_id

    call_func, _ = await get_part_name(await fanc_name())
    this_level_data_dict = CATEGORY_ID_TRANSFORM[call_func]

    await notify_user_for_choice(call, data_answer=call.data)

    call_func = await fanc_name()
    context = context if context else 'next_level'
    answer_dict = await prepare_answer_data(
        hse_user_id, this_level_data_dict, state=state, call_func=call_func, context=context
    )
    if not answer_dict: return False

    await set_board_config(hse_user_id, answer_dict, state=state, call_func=call_func)
    await check_and_send_message(hse_user_id, answer_dict, state=state, call_func=call_func)
    return True


async def get_and_send_normative_documents_data(call: types.CallbackQuery, user_id: int | str = None,
                                                state: FSMContext = None, context: str = None) -> bool:
    """ Получение данных normative_documents

    :param context: str (опционально) - переключатель - this / next level
    :param state: FSMContext - текущее состояние пользователя chat_id
    :param user_id: int | str id пользователя
    :param call:
    :return: bool
    """
    hse_user_id = call.message.chat.id if call else user_id

    call_func, _ = await get_part_name(await fanc_name())
    this_level_data_dict = CATEGORY_ID_TRANSFORM[call_func]

    await notify_user_for_choice(call, data_answer=call.data)

    call_func = await fanc_name()
    context = context if context else 'next_level'
    answer_dict = await prepare_answer_data(
        hse_user_id, this_level_data_dict, state=state, call_func=call_func, context=context
    )
    if not answer_dict: return False

    await set_board_config(hse_user_id, answer_dict, state=state, call_func=call_func)
    await check_and_send_message(hse_user_id, answer_dict, state=state, call_func=call_func)
    return True


async def get_and_send_violation_category_data(call: types.CallbackQuery, user_id: int | str = None,
                                               state: FSMContext = None, context: str = None) -> bool:
    """Получение данных violation_category

    :param context: str (опционально) - переключатель - this / next level
    :param state: FSMContext - текущее состояние пользователя chat_id
    :param user_id: int | str id пользователя
    :param call:
    :return: bool
    """
    hse_user_id = call.message.chat.id if call else user_id

    call_func, _ = await get_part_name(await fanc_name())
    this_level_data_dict = CATEGORY_ID_TRANSFORM[call_func]

    await notify_user_for_choice(call, data_answer=call.data)

    call_func = await fanc_name()
    context = context if context else 'next_level'
    answer_dict = await prepare_answer_data(
        hse_user_id, this_level_data_dict, state=state, call_func=call_func, context=context
    )
    if not answer_dict: return False

    await set_board_config(hse_user_id, answer_dict, state=state, call_func=call_func)
    await check_and_send_message(hse_user_id, answer_dict, state=state, call_func=call_func)
    return True


async def get_and_send_general_contractor_data(call: types.CallbackQuery, user_id: int | str = None,
                                               state: FSMContext = None, context: str = None) -> bool:
    """Получение данных general_contractor

    :param context: str (опционально) - переключатель - this / next level
    :param state: FSMContext - текущее состояние пользователя chat_id
    :param user_id: int | str id пользователя
    :param call:
    :return: bool
    """
    hse_user_id = call.message.chat.id if call else user_id

    call_func, _ = await get_part_name(await fanc_name())
    this_level_data_dict = CATEGORY_ID_TRANSFORM[call_func]

    await notify_user_for_choice(call, data_answer=call.data)

    call_func = await fanc_name()
    context = context if context else 'next_level'
    answer_dict = await prepare_answer_data(
        hse_user_id, this_level_data_dict, state=state, call_func=call_func, context=context
    )
    if not answer_dict: return False

    await set_board_config(hse_user_id, answer_dict, state=state, call_func=call_func)
    await check_and_send_message(hse_user_id, answer_dict, state=state, call_func=call_func)
    return True


async def get_and_send_incident_level_data(call: types.CallbackQuery, user_id: int | str = None,
                                           state: FSMContext = None, context: str = None) -> bool:
    """Получение данных incident_level

    :param context: str (опционально) - переключатель - this / next level
    :param state: FSMContext - текущее состояние пользователя chat_id
    :param user_id: int | str id пользователя
    :param call:
    :return: bool
    """
    hse_user_id = call.message.chat.id if call else user_id

    call_func, _ = await get_part_name(await fanc_name())
    this_level_data_dict = CATEGORY_ID_TRANSFORM[call_func]

    await notify_user_for_choice(call, data_answer=call.data)

    call_func = await fanc_name()
    context = context if context else 'next_level'
    answer_dict = await prepare_answer_data(
        hse_user_id, this_level_data_dict, state=state, call_func=call_func, context=context
    )
    if not answer_dict: return False

    await set_board_config(hse_user_id, answer_dict, state=state, call_func=call_func)
    await check_and_send_message(hse_user_id, answer_dict, state=state, call_func=call_func)
    return True


async def get_and_send_act_required_data(call: types.CallbackQuery, user_id: int | str = None,
                                         state: FSMContext = None, context: str = None) -> bool:
    """Получение данных act_required

    :param context: str (опционально) - переключатель - this / next level
    :param state: FSMContext - текущее состояние пользователя chat_id
    :param user_id: int | str id пользователя
    :param call:
    :return: bool
    """
    hse_user_id = call.message.chat.id if call else user_id

    call_func, _ = await get_part_name(await fanc_name())
    this_level_data_dict = CATEGORY_ID_TRANSFORM[call_func]

    await notify_user_for_choice(call, data_answer=call.data)

    call_func = await fanc_name()
    context = context if context else 'next_level'
    answer_dict = await prepare_answer_data(
        hse_user_id, this_level_data_dict, state=state, call_func=call_func, context=context
    )
    if not answer_dict: return False

    await set_board_config(hse_user_id, answer_dict, state=state, call_func=call_func)
    await check_and_send_message(hse_user_id, answer_dict, state=state, call_func=call_func)
    return True


async def get_and_send_elimination_time_data(call: types.CallbackQuery, user_id: int | str = None,
                                             state: FSMContext = None, context: str = None) -> bool:
    """Получение данных elimination_time

    :param context: str (опционально) - переключатель - this / next level
    :param state: FSMContext - текущее состояние пользователя chat_id
    :param user_id: int | str id пользователя
    :param call:
    :return: bool
    """
    hse_user_id = call.message.chat.id if call else user_id

    call_func, _ = await get_part_name(await fanc_name())
    this_level_data_dict = CATEGORY_ID_TRANSFORM[call_func]

    previous_level = this_level_data_dict['previous_level']
    await board_config(state, "previous_level", previous_level).set_data(call_func=await fanc_name())

    await notify_user_for_choice(call, data_answer=call.data)

    context = context if context else 'next_level'
    answer_dict = await prepare_answer_data(
        hse_user_id, this_level_data_dict, state=state, call_func=call_func, context=context
    )
    await set_board_config(hse_user_id, answer_dict, state=state, call_func=call_func)
    await check_and_send_message(hse_user_id, answer_dict, state=state, call_func=call_func)

    # Вызов состояния ожидания текстового ответа от пользователя
    await ViolationData.description.set()
    return True


async def prepare_answer_data(chat_id: int | str, level_data: dict, state: FSMContext, call_func: str,
                              context: str = None, condition: str = None) -> dict:
    """Подготовка данных для отправки ответа пользователю.
    
    :param condition: str (опционально) - дополнительные параметры
    :param context: str (опционально) - переключатель - this / next level
    :param chat_id: int | str id пользователя
    :param level_data: dict - dict с данными для формирования ответа str
    :param state: FSMContext - текущее состояние пользователя chat_id
    :param call_func: str - имя вызывающей функции

    :return: dict - словарь с данными для формирования ответа
    """
    if not chat_id:
        logger.error(f'Error level_data not found! {call_func = }')
        return {}

    if not level_data:
        error_text: str = f'Error level_data not found! {call_func = }'
        await send_error_message(chat_id, error_text, state=state)
        return {}

    if not state:
        error_text: str = f'Error state not found! {call_func = }'
        await send_error_message(chat_id, error_text, state=state)
        return {}

    menu_list = []
    text: str = ''
    level_message: str = ''

    if context == 'this_level':
        menu_list = await get_data_list(category_in_db=level_data.get('this_level'))
        text: str = level_data['this_level_message']
        level_message: str = text

    if context == 'next_level':
        menu_list = await get_data_list(category_in_db=level_data.get('next_level'))
        text: str = level_data['next_level_message']
        level_message: str = text

    count_col: int = level_data.get('this_level_count_col')
    menu_level: int = level_data['menu_level'] if level_data.get('menu_level', None) else 1
    previous_level: str = level_data.get('previous_level')

    use_list_message: bool = False

    if condition == 'short_title':
        v_data: dict = await state.get_data()

        next_level = v_data['next_level']
        menu_list = await get_data_list(next_level,
                                        category=v_data[level_data['item']],
                                        condition='short_title'
                                        )
        data_list = await get_data_list(next_level,
                                        category=v_data[level_data['item']],
                                        condition='data_list'
                                        )
        zipped_list: list = list(zip(menu_list, data_list))
        text_list: list = [f"{await get_character_text(item)}" for item in zipped_list]
        menu_text_list = await board_config(state, "menu_text_list", text_list).set_data(call_func=await fanc_name())

        reply_text = await build_text_for_inlinekeyboard(some_list=menu_text_list, level=menu_level)
        text = f"{level_data['next_level_message']}\n\n{reply_text}"

        use_list_message = True

    reply_markup = await build_inlinekeyboard(
        some_list=menu_list, num_col=count_col, level=menu_level, previous_level=previous_level,
        state=state
    )

    level_data_dict: dict = {
        'menu_list': menu_list,
        'count_col': count_col,
        'menu_level': menu_level,
        'previous_level': previous_level,

        'text': text,
        'reply_markup': reply_markup,

        'this_level': level_data['this_level'],
        'level_message': level_message,
        'next_level': level_data['next_level'],
        'use_list_message': use_list_message
    }

    return level_data_dict


async def set_board_config(chat_id: int | str, data_dict: dict, call_func: str, state: FSMContext) -> bool:
    """Запись данных пользователя chat_id из data_dict в state.

    :param chat_id: int | str id пользователя
    :param data_dict: dict - dict с данными для записи
    :param state: FSMContext - текущее состояние пользователя chat_id
    :param call_func: str - имя вызывающей функции
    :return:
    """
    if not state:
        error_text: str = f'Error state not found! {call_func = }'
        await send_error_message(chat_id, error_text)
        return False

    call_func: str = f'{await fanc_name()} :: {call_func}' if call_func else await fanc_name()

    menu_list: list = [] if not data_dict.get('menu_list') else await get_data_list(data_dict['next_level'])
    if menu_list:
        await board_config(state, "menu_list", menu_list).set_data(call_func=call_func)

    menu_level: int = 1 if not data_dict.get('data_dict') else data_dict.get('data_dict')
    if menu_level:
        await board_config(state, "menu_level", menu_level).set_data(call_func=call_func)

    count_col: int = 1 if not data_dict.get('count_col') else data_dict.get('count_col')
    if count_col:
        await board_config(state, "count_col", count_col).set_data(call_func=call_func)

    previous_level: str = '' if not data_dict.get('previous_level') else data_dict.get('previous_level')
    if previous_level:
        await board_config(state, "previous_level", previous_level).set_data(call_func=call_func)

    menu_text_list: list = [] if not data_dict.get('this_level_message') else [data_dict.get('this_level_message')]
    if menu_text_list:
        await board_config(state, "menu_text_list", menu_text_list).set_data(call_func=call_func)

    level_message: str = '' if not data_dict.get('level_message') else data_dict['level_message']
    if level_message:
        await board_config(state, "level_message", level_message).set_data(call_func=call_func)

    use_list_message: bool = False if not data_dict.get('use_list_message') else data_dict['use_list_message']
    if use_list_message:
        await board_config(state, "use_list_message", use_list_message).set_data(call_func=call_func)

    return True


async def check_and_send_message(chat_id: str, answer_dict: dict, call_func: str = None,
                                 state: FSMContext = None) -> bool:
    """Проверка основных данных answer_dict и отправка сообщения пользователю chat_id.
     Возвращает статус bool отправки result
     
    :param chat_id: int | str id пользователя
    :param answer_dict:
    :param state: FSMContext - текущее состояние пользователя chat_id
    :param call_func: str - имя вызывающей функции
    :return:
    """
    if not chat_id:
        error_text: str = f'Error chat_id not found! {call_func = }'
        await send_error_message(chat_id, error_text, state=state)
        return False

    if not answer_dict:
        error_text: str = f'Error answer_dict not found! {call_func = }'
        await send_error_message(chat_id, error_text, state=state)
        return False

    answer_text: str = answer_dict['text']
    if not isinstance(answer_text, str):
        error_text: str = f'Error chat_id not found! {call_func = }'
        await send_error_message(chat_id, error_text, state=state)
        return False

    answer_reply_markup: types.InlineKeyboardMarkup = answer_dict['reply_markup']
    if not isinstance(answer_reply_markup, types.InlineKeyboardMarkup):
        error_text: str = f'Error answer_reply_markup not found! {call_func = }'
        await send_error_message(chat_id, error_text, state=state)
        return False

    result = await bot_send_message(chat_id=chat_id, text=answer_text, reply_markup=answer_reply_markup)
    return result


async def get_part_name(func_n: str) -> (str, bool):
    """Получение имени параметра из имени вызываемой функции func_n.
    Возвращает имя параметра func_n str и результат проверки в CATEGORY_ID_TRANSFORM bool

    :param func_n: имя вызываемой функции
    :return: str, bool - тмя параметра, результат проверки наличия в CATEGORY_ID_TRANSFORM
    """
    if not isinstance(func_n, str):
        return func_n

    replace_list: list = ['get_and_send_', '_data', '_null', 'start_', 'null_']
    for i in replace_list:
        func_n = func_n.replace(i, '')

    result = CATEGORY_ID_TRANSFORM.get(func_n)
    pprint(f"{__name__} {bool(result)= } {await get_level_characteristics(level_dict=CATEGORY_ID_TRANSFORM[func_n])}",
           width=200)
    return func_n, bool(result)


async def get_level_characteristics(level_dict: dict) -> str:
    """Получение характеристик текущего уровня из level_dict.
    Возвращает готовый текст.

    :param level_dict: dict - dict с данными для формирования ответа str
    :return: text str - сформированный ответ
    """
    this_level_number = level_dict.get('this_level_number', None)
    this_level = level_dict.get('this_level', None)
    item = level_dict.get('item', None)

    list_characteristics = [
        f'{item = }' if item else 'item is None',
        f'{this_level = }' if this_level else 'this_level is None',
        f'{this_level_number = }' if this_level_number else 'this_level_number is None',
    ]
    text: str = ": ".join([item for item in list_characteristics if item is not None])
    return text


async def notify_user_for_choice(call_msg: types.CallbackQuery | types.Message, user_id: int | str = None,
                                 data_answer: str = None) -> bool:
    """Уведомление пользователя о выборе + логирование

    :param data_answer:
    :param user_id: int | str id пользователя
    :param call_msg: types.CallbackQuery | types.Message - сообщения для изменения в зависимости от типа
    :return result: bool : результат изменения
    """
    if isinstance(call_msg, types.CallbackQuery):
        user_id = user_id if user_id else call_msg.from_user.id
        result: bool = await is_callbackquery(call_msg, data_answer, user_id)
        return result

    if isinstance(call_msg, types.Message):
        user_id = user_id if user_id else call_msg.from_user.id
        result: bool = await is_message(call_msg, data_answer, user_id)
        return result


async def is_callbackquery(callbackquery: types.CallbackQuery, data_answer: str, user_id: int | str = None) -> bool:
    """Изменение сообщения types.CallbackQuery
    """
    for i in ('previous_paragraph', 'move_up', 'move_down'):
        if i in callbackquery.data: return True

    mesg_text: str = f"Выбрано: {data_answer}"
    if callbackquery.data in callbackquery.message.text:
        mesg_list: list = [item for item in callbackquery.message.text.split('\n\n') if callbackquery.data in item]
        mesg_text = f"Выбрано: {mesg_list[0]}"

    try:
        hse_user_id = callbackquery.message.chat.id if callbackquery else user_id
        logger.debug(f"{hse_user_id = } Выбрано: {data_answer} {callbackquery.data}")
        await callbackquery.message.edit_text(text=mesg_text, reply_markup=None)
        return True

    except Exception as err:
        logger.debug(f"{callbackquery.message.chat.id = } {repr(err)}")
        return False


async def is_message(message: types.Message, data_answer: str, user_id: int | str = None) -> bool:
    """Изменение сообщения types.Message
    """
    for i in ('previous_paragraph', 'move_up', 'move_down'):
        if i in message.text: return True

    mesg_text: str = f"Выбрано: {data_answer}"
    if message.text:
        mesg_list: list = [item for item in message.text.split('\n\n') if message.text in item]
        mesg_text = f"Выбрано: {mesg_list[0] if mesg_list else ''}"

    hse_user_id = message.chat.id if message else user_id
    logger.debug(f"{hse_user_id = } Выбрано: {data_answer} {message.text}")

    try:
        await message.edit_text(text=mesg_text, reply_markup=None)
        return True

    except Exception as err:
        logger.debug(f"{message.chat.id = } {repr(err)}")
        return False


async def get_character_text(param_list: list | str) -> list | str:
    """Формирование ответа text_list из параметров param_list в зависимости от типа param_list

    :param param_list: list | str - параметры для формирования ответа
    :return: list | str text_list в зависимости от типа param_list
    """
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
        text_list: str = f"{param_list[0]} : {param_list[1]}"
        return text_list


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])
