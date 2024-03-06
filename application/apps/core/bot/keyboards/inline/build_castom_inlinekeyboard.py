from __future__ import annotations

from aiogram.dispatcher.filters import ChatTypeFilter

from loader import logger

logger.debug(f"{__name__} start import")

import traceback
from pprint import pprint
from pandas import DataFrame

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.callback_data import CallbackData
from aiogram.types import (InlineKeyboardButton,
                           InlineKeyboardMarkup, ChatType)

from apps.core.bot.data.board_config import BoardConfig
from apps.core.bot.reports.report_data import ViolationData
from apps.MyBot import MyBot, bot_send_message, bot_edit_message

logger.debug(f"{__name__} finish import")


async def is_private(message: types.Message = None):
    """Фильтр состояния"""
    pprint(f"{__file__} {await fanc_name()} {message =}", width=200)
    return ChatTypeFilter(ChatType.PRIVATE)


NUM_COL: int = 2
STEP_MENU: int = 8
move_action: CallbackData = CallbackData("desc", "action", "pre_val")
posts_cb: CallbackData = CallbackData('post', 'id', 'action')


async def build_inlinekeyboard(*, some_list: list = None, num_col: int = None, level: int = None, step: int = None,
                               called_prefix: str = None, addition: list = None, previous_level: str = None,
                               postfix: str = None, use_search=None, state: FSMContext = None) -> InlineKeyboardMarkup:
    """Создание кнопок в чате для пользователя на основе some_list.
    Количество кнопок = количество элементов в списке some_list
    Расположение в n_cols столбцов
    Текст на кнопках text=ss
    Возвращаемое значение, при нажатии кнопки в чате callback_data=ss
    """
    num_col: int = num_col if num_col else 1
    level: int = level if level else 1
    use_search: bool = use_search if use_search else False
    called_prefix: str = called_prefix if called_prefix else ''
    postfix: str = postfix if postfix else ''

    button_list: list = []

    if not some_list:
        reply_markup = await add_previous_paragraph_button(previous_level=previous_level)
        return reply_markup

    some_list: list = await check_list_bytes_len(list_for_check=some_list)

    if addition:
        button_list: list = [item for item in addition if item is not None]

    if step:
        button_list: list = button_list + [
            InlineKeyboardButton(text=ss, callback_data=f'{called_prefix}{ss}{postfix}') for ss in some_list
        ]

        menu: list = await _build_menu(buttons=button_list, n_cols=num_col)
        reply_markup = InlineKeyboardMarkup(resize_keyboard=True, inline_keyboard=menu)

        if previous_level:
            reply_markup = await add_previous_paragraph_button(
                reply_markup=reply_markup, previous_level=previous_level
            )
        return reply_markup

    param_dict: dict = {
        'some_list': some_list,
        'button_list': button_list,
        'level': level,
        'num_col': num_col,
        'prefix': called_prefix,
        'postfix': postfix,
        'previous_level': previous_level,
        'use_search': use_search
    }

    if len(some_list) <= STEP_MENU:
        logger.debug(f'len(some_list) <= STEP_MENU {len(some_list) <= STEP_MENU}')
        await BoardConfig(state).set_data('use_search', False)
        param_dict[use_search] = False

        reply_markup: InlineKeyboardMarkup = await get_short_markup(
            some_list=some_list, state=state, param_dict=param_dict
        )
        return reply_markup

    if len(some_list) > STEP_MENU:
        logger.debug(f'STEP_MENU > len(some_list) {STEP_MENU < len(some_list)}')
        await BoardConfig(state).set_data('use_search', True)
        param_dict[use_search] = True
        # param_dict: dict = {
        #     'some_list': some_list,
        #     'button_list': button_list,
        #     'level': level,
        #     'num_col': num_col,
        #     'prefix': called_prefix,
        #     'postfix': postfix,
        #     'previous_level': previous_level,
        #     'use_search': use_search
        # }

        reply_markup: InlineKeyboardMarkup = await get_long_markup(
            some_list=some_list, state=state, param_dict=param_dict
        )
        return reply_markup


async def get_short_markup(some_list: list, state: FSMContext = None, param_dict: dict = None) -> InlineKeyboardMarkup:
    """Сборка reply_markup их небольшого набора данных some_list с параметрами param_dict и состоянием state

    :return: reply_markup : собранная клавиатура с данными для сообщения
     """
    logger.debug('len(some_list) <= STEP_MENU')
    await BoardConfig(state).set_data('use_search', False)

    button_list: list[InlineKeyboardButton] = await get_param('button_list', param_dict)

    called_prefix: str = await get_param('called_prefix', param_dict)
    postfix: str = await get_param('postfix', param_dict)
    num_col: int = await get_param('num_col', param_dict)
    previous_level: str = await get_param('previous_level', param_dict)
    use_search: str = await get_param('use_search', param_dict)

    button_list = button_list + [
        InlineKeyboardButton(text=ss, callback_data=f'{called_prefix}{ss}{postfix}') for ss in some_list
    ]

    menu: list = await _build_menu(buttons=button_list, n_cols=num_col)
    reply_markup = InlineKeyboardMarkup(resize_keyboard=True, inline_keyboard=menu)

    if previous_level:
        reply_markup = await add_previous_paragraph_button(
            reply_markup=reply_markup, previous_level=previous_level
        )
    if use_search:
        reply_markup = await add_use_search_button(
            reply_markup=reply_markup, previous_level=previous_level,
        )

    return reply_markup


async def get_long_markup(some_list: list, state: FSMContext = None, param_dict: dict = None) -> InlineKeyboardMarkup:
    """Сборка reply_markup их большого набора данных some_list с параметрами param_dict и состоянием state

    :return: reply_markup : собранная клавиатура с данными для сообщения
    """
    logger.debug('len(some_list) > STEP_MENU')
    await BoardConfig(state).set_data('use_search', True)

    previous_level: str = await get_param('previous_level', param_dict)
    use_search: bool = await get_param('use_search', param_dict)

    button_list: list[InlineKeyboardButton] = await get_param('button_list', param_dict)
    button_list: list = await get_button_list(some_list, button_list, param_dict=param_dict)

    reply_markup = await _build_markup(buttons=button_list, param_dict=param_dict)
    reply_markup = await add_action_button(reply_markup=reply_markup, some_list=some_list, param_dict=param_dict)

    if previous_level:
        reply_markup = await add_previous_paragraph_button(
            reply_markup=reply_markup, previous_level=previous_level, param_dict=param_dict
        )
    if use_search:
        reply_markup = await add_use_search_button(
            reply_markup=reply_markup, previous_level=previous_level,
        )

    return reply_markup


async def get_param(param_name: str, param_dict: dict) -> any:
    """Определение нулевых значений в зависимости от типа данных

    :param param_name: str - наименование параметра
    :param param_dict: dict - Дополнительные параметры
    :return: any
    """
    null_value: any = ''

    if param_name in {'previous_level', 'use_search', 'postfix', 'called_prefix', 'prefix'}:
        null_value: str = ''
    if param_name in {'some_list', 'button_list'}:
        null_value: list = []
    if param_name in {'use_search', }:
        null_value: bool = False
    if param_name in {'level', 'num_col'}:
        null_value: int = 1

    if isinstance(param_dict, dict):
        param = param_dict.get(param_name, null_value)
        return param if param else null_value


async def get_button_list(some_list: list, button_list: list, param_dict: dict = None) -> list:
    """Формирование list с кнопками действий

    :param param_dict: dict - дополнительные параметры
    :param some_list: list с данными для формирования button_list с InlineKeyboardButton
    :param button_list: dict - list c дополнительными кнопками
    :return: List button_list с кнопками действий
    """
    if not some_list:
        return button_list

    if not isinstance(some_list, list):
        return []

    button_list: list = button_list + await get_button_list_for_list(some_list=some_list, param_dict=param_dict)
    return button_list


async def get_button_list_for_list(some_list: list, param_dict: dict = None) -> list:
    """Функция формирования данных button_list с InlineKeyboardButton из some_list с использованием prefix и postfix

    :param param_dict: dict - дополнительные параметры
    :param some_list: list с данными для формирования button_list с InlineKeyboardButton
    :return:
    """
    if not some_list:
        return []

    if not isinstance(some_list, list):
        return []

    prefix: str = await get_param('prefix', param_dict=param_dict)
    postfix: str = await get_param('postfix', param_dict=param_dict)
    level: int = await get_param('level', param_dict=param_dict)

    end_list: int = len(some_list)
    start_index, stop_index = await define_indices(level, end_list)

    button_list_full: list = []

    for item in some_list[start_index:stop_index]:

        if isinstance(item, str):
            button = InlineKeyboardButton(text=item, callback_data=f'{prefix}{item}{postfix}')
            button_list_full.append(button)
            continue

        if isinstance(item, list):
            button = InlineKeyboardButton(text=item[0], callback_data=f'{prefix}{item[1]}{postfix}')
            button_list_full.append(button)
            continue

        if isinstance(item, tuple):
            button = InlineKeyboardButton(text=item[0], callback_data=f'{prefix}{item[1]}{postfix}')
            button_list_full.append(button)
            continue

        if isinstance(item, dict):
            text, val = ((k, v) for k, v in item.items())
            button = InlineKeyboardButton(text=text, callback_data=f'{prefix}{val}{postfix}')
            button_list_full.append(button)

    return button_list_full


async def check_list_bytes_len(list_for_check: list[str], target_parameter: int = 60) -> list:
    """Проверка длинны записи в байтах для формирования надписей кнопок
    текст длиннее 64 байт обрезается, добавляются точки

    :param target_parameter: int максимальная длина строки
    :param list_for_check: list с данными для проверки
    :return: list - лист с проверенными данными
    """
    processed_values: len = []
    for item in list_for_check:
        if len(item.encode('utf-8')) > target_parameter:
            logger.debug(f" {item} : {len(item.encode('utf-8'))}")

            while int(len(item.encode('utf-8'))) > target_parameter - 1:
                item = item[:-1]
                logger.debug(f" {item} : {len(item.encode('utf-8'))}")

            item = item[:-2] + '...'
            logger.debug(f" {item} : {len(item.encode('utf-8'))}")

        processed_values.append(item)

    return processed_values


async def define_indices(level: int, end_list: int) -> (int, int):
    """Определение начального и конечного индекса для среза на основе level

    :param level: int уровень
    :param end_list: int - индекс окончания листа
    :return: (int, int) - индекс начало и конц среза
    """
    start_index: int = 0 if level == 1 else (STEP_MENU * level) - STEP_MENU

    if level == 1:
        start_index = 0

    stop_index: int = STEP_MENU if start_index == 0 else start_index + STEP_MENU
    stop_index: int = end_list if stop_index > end_list else start_index + STEP_MENU

    return start_index, stop_index


async def add_action_button(reply_markup: InlineKeyboardMarkup, some_list: list, param_dict: dict
                            ) -> InlineKeyboardMarkup:
    """Добавление кнопок навигации в зависимости от начального (start_index),
    конечного индекса (stop_index) и конца списка list (end_list)

    :param some_list: - лист со значениями
    :param reply_markup: InlineKeyboardMarkup - объект InlineKeyboardMarkup
    :param param_dict: dict -  дополнительные параметры
    :return: reply_markup
    """
    bt_down = InlineKeyboardButton(text="<--", callback_data=move_action.new(action="move_down", pre_val=''))
    bt_up = InlineKeyboardButton(text="-->", callback_data=move_action.new(action="move_up", pre_val=''))

    level: int = await get_param('level', param_dict)

    start_index, stop_index, end_list = 0, 0, 0
    if some_list:
        end_list: int = len(some_list)
        start_index, stop_index = await define_indices(level, end_list)

    if start_index == 0:
        reply_markup.row(bt_up)
        return reply_markup

    if stop_index == end_list:
        reply_markup.row(bt_down)  # добавление кнопок в новую строку # ПРИОРИТЕТ
        return reply_markup

    reply_markup.row(bt_down, bt_up)

    return reply_markup


async def add_previous_paragraph_button(reply_markup: InlineKeyboardMarkup = None, previous_level: str = None,
                                        param_dict: dict = None) -> InlineKeyboardMarkup:
    """Добавление кнопки - предыдущее действий"""
    logger.debug(f"{reply_markup = } {previous_level = }")
    logger.debug(f"{param_dict = }")

    if not reply_markup:
        reply_markup = InlineKeyboardMarkup(resize_keyboard=True)

    if not previous_level:
        return reply_markup

    previous_level_list: list = await check_list_bytes_len(list_for_check=[previous_level], target_parameter=45)
    previous_level: str = previous_level_list[0]

    btn_previous = InlineKeyboardButton(
        text="previous",
        callback_data=move_action.new(action="pre_paragraph", pre_val=previous_level)
    )
    reply_markup.row(btn_previous)

    return reply_markup


async def add_use_search_button(reply_markup: InlineKeyboardMarkup, previous_level: str = '') -> InlineKeyboardMarkup:
    """Добавление кнопки - предыдущее действий
    """
    search_button = InlineKeyboardButton(
        text="поиск",
        callback_data=move_action.new(action="search", pre_val=previous_level)
    )
    reply_markup.inline_keyboard.insert(0, [search_button])

    return reply_markup


async def _build_menu(buttons: list, n_cols: int = 1, header_buttons: list = None, footer_buttons: list = None) -> list:
    """Создание меню кнопок
    """
    menu: list = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]

    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])

    return menu


async def _build_markup(buttons: list, num_col: int = None, param_dict=None) -> InlineKeyboardMarkup:
    """Создание меню кнопок
    """
    num_col: int = num_col if num_col else await get_param('num_col', param_dict=param_dict)

    menu: list = await _build_menu(buttons=buttons, n_cols=num_col)
    reply_markup = InlineKeyboardMarkup(resize_keyboard=True, inline_keyboard=menu)

    return reply_markup


@MyBot.dp.callback_query_handler(move_action.filter(action=["move_down", "move_up"]), state='*')
async def build_inlinekeyboard_answer(call: types.CallbackQuery, callback_data: dict, state: FSMContext = None,
                                      user_id: str | int = None) -> bool:
    """Обработка ответа клавиш переключения уровня меню в inlinekeyboard в сообщении

    :param user_id:
    :param state:
    :param call:
    :param callback_data:
    :return: bool
    """
    hse_user_id: int = user_id if user_id else call.message.chat.id

    v_data: dict = await state.get_data()

    menu_level: int = v_data.get('menu_level')
    if menu_level is None:
        logger.warning(f'{await fanc_name()} WARNING {menu_level = }')
        return False

    menu_list: list = v_data.get('menu_list', [])
    menu_text_list: list = v_data.get('menu_text_list', menu_list)
    use_search: bool = v_data.get('use_search', False)
    count_col: int = v_data.get('count_col')
    call_fanc_name: str = v_data.get('call_fanc_name', '')
    previous_level: str = v_data.get('previous_level', '')
    level_message: str = v_data.get('level_message', '')
    use_list_message = v_data.get('use_list_message', False)

    prefix: str = v_data.get('prefix')

    if call_fanc_name == 'enable_features':
        prefix = 'features_'
    if call_fanc_name == 'hse_add_roles':
        prefix = 'hse_role_'

    message_id: int = call.message.message_id

    if callback_data.get('action') == "move_down":
        menu_level: int = await BoardConfig(state, "menu_level", menu_level - 1).set_data()

    if callback_data.get('action') == "move_up":
        menu_level: int = await BoardConfig(state, "menu_level", menu_level + 1).set_data()

    reply_markup: InlineKeyboardMarkup = await build_inlinekeyboard(
        some_list=menu_list, num_col=count_col, level=menu_level, called_prefix=prefix, use_search=use_search,
        state=state
    )
    reply_text: str = await build_text_for_inlinekeyboard(
        some_list=menu_text_list, level=menu_level
    )
    if level_message:
        reply_text = f"{level_message}\n\n{reply_text}"

    if level_message and not use_list_message:
        reply_text = level_message

    if previous_level:
        reply_markup: InlineKeyboardMarkup = await add_previous_paragraph_button(
            reply_markup=reply_markup, previous_level=previous_level
        )
    result: bool = await bot_edit_message(
        hse_user_id=hse_user_id, message_id=message_id,
        reply_markup=reply_markup, reply_text=reply_text, kvargs={'fanc_name': await fanc_name()}
    )

    await BoardConfig(state, "call_fanc_name", '').set_data()
    return result


@MyBot.dp.callback_query_handler(move_action.filter(action=["search"]), state='*')
async def build_inlinekeyboard_search_answer(call: types.CallbackQuery, callback_data: dict,
                                             state: FSMContext = None) -> bool:
    """Обработка ответа клавиш переключения уровня меню в inlinekeyboard в сообщении

    :param state: FSMContext - объект состояния
    :param call: CallbackQuery - объект CallbackQuery
    :param callback_data: dict - dict со значениями сообщения
    :return: result bool -  результат изменения сообщения True or False
    """
    item_txt: str = 'введите текстовый зарос'
    pprint(f'{__name__}{await fanc_name()} {callback_data = }', width=200)

    chat_id = call.message.chat.id
    message_id = call.message.message_id

    await ViolationData.inquiry.set()

    await state.update_data(chat_id=chat_id)
    await state.update_data(message_id=message_id)

    v_data: dict = await state.get_data()
    previous_level: str = v_data.get('previous_level', '')

    reply_markup = InlineKeyboardMarkup(resize_keyboard=True)
    reply_markup: InlineKeyboardMarkup = await add_previous_paragraph_button(
        reply_markup=reply_markup, previous_level=previous_level
    )

    result: bool = await bot_edit_message(
        hse_user_id=chat_id,
        message_id=message_id,
        reply_text=item_txt,
        reply_markup=reply_markup,
        kvargs={'fanc_name': await fanc_name()}
    )
    return result


@MyBot.dp.message_handler(is_private, state=ViolationData.inquiry)
async def search_data_all_states_answer(message: types.Message = None, text: str = None,
                                        state: FSMContext = None) -> bool:
    """Обработка поиск text во всех состояниях state по команде search (поиск) на клавиатуре в message

    :param text: str - текст для поиска
    :param message: Message - сообщение с текстом из которого берется текст
    :param state: FSMContext - состояние пользователя
    :return: bool - True if successfully else False
    """
    text_too_search: str = message.text if message else text

    v_data: dict = await state.get_data()

    menu_level: int = v_data.get('menu_level')
    if menu_level is None:
        logger.warning(f'{await fanc_name()} WARNING {menu_level = }')
        return False

    menu_list: list = v_data.get('menu_list', [])
    menu_text_list: list = v_data.get('menu_text_list', menu_list[0])
    use_search = v_data.get('use_search')
    count_col: int = v_data.get('count_col')
    call_fanc_name: str = v_data.get('call_fanc_name', '')
    previous_level: str = v_data.get('previous_level', '')
    level_message: str = v_data.get('level_message', '')
    use_list_message = v_data.get('use_list_message', False)

    prefix: str = ''
    if call_fanc_name == 'enable_features':
        prefix = 'features_'
    if call_fanc_name == 'hse_add_roles':
        prefix = 'hse_role_'

    chat_id: str = v_data.get('chat_id')

    menu_list: list = [item for item in menu_list if item[0] != '#']
    menu_text_list: list = [item for item in menu_text_list if item[0] != '#']

    dataframe: DataFrame = await create_dataframe(menu_list, menu_text_list)

    menu_list, menu_text_list = await processor_search_if_str(
        dataframe, text_too_search=text_too_search
    )

    await BoardConfig(state).set_data('menu_list', menu_list)

    reply_markup: InlineKeyboardMarkup = await build_inlinekeyboard(
        some_list=menu_list, num_col=count_col, level=menu_level, called_prefix=prefix, use_search=use_search,
        previous_level=previous_level, state=state
    )
    reply_text: str = await build_text_for_inlinekeyboard(
        some_list=menu_text_list, level=menu_level
    )

    if not reply_text:
        reply_text = 'Нет данных для отображения'

        reply_markup = InlineKeyboardMarkup(resize_keyboard=True)
        reply_markup: InlineKeyboardMarkup = await add_previous_paragraph_button(
            reply_markup=reply_markup, previous_level=previous_level
        )

        result: bool = await bot_send_message(text=reply_text, chat_id=chat_id, reply_markup=reply_markup)
        await BoardConfig(state, "call_fanc_name", '').set_data()
        return result

    if level_message:
        reply_text = f"{level_message}\n\n{reply_text}"
    if level_message and not use_list_message:
        reply_text = level_message

    result: bool = await bot_send_message(text=reply_text, chat_id=chat_id, reply_markup=reply_markup)
    await BoardConfig(state, "call_fanc_name", '').set_data()
    return result


async def build_text_for_inlinekeyboard(*, some_list: list, level: int = 1) -> str:
    """Создание текста text_list из list с данными some_list в зависимости  от level
    по условию len(some_list) <=> STEP_MENU
    Возвращает готовый текст

    :param some_list: list - лист с данными
    :param level: int -  уровень меню (влияет на отображаемую часть текста)(some_list[start_index:stop_index])
    :return: str: text_list
    """
    text_list: list = []

    if len(some_list) > STEP_MENU:
        logger.debug(f'STEP_MENU < len(some_list) {STEP_MENU < len(some_list)}')

        end_list: int = len(some_list)
        start_index, stop_index = await define_indices(level, end_list)

        text_list: list = text_list + some_list[start_index:stop_index]
        text_str: str = '\n\n'.join(text_list)

        return text_str

    if len(some_list) <= STEP_MENU:
        logger.debug(f'len(some_list) <= STEP_MENU {len(some_list) <= STEP_MENU}')

        text_list = text_list + some_list
        text_str: str = '\n\n'.join(text_list)

        return text_str


async def create_dataframe(menu_list: list, menu_text_list: list) -> DataFrame:
    """Создание create_dataframe

    :param menu_list: list - лист с данными
    :param menu_text_list: list - лист с данными
    :return: DataFrame Or None
    """
    df = None
    data_dict: dict = {'index': menu_list, 'text': menu_text_list}
    try:
        df = DataFrame(data=data_dict)

    except ValueError as err:
        logger.warning(f'Error create_dataframe {repr(err)}')

    return df


async def processor_search_if_str(table_dataframe: DataFrame, text_too_search: str) -> (list, list):
    """Поиск текста text_too_search в table_dataframe по неполному соответствию

    :param table_dataframe:
    :param text_too_search:
    :return:
    """
    menu_list, menu_text_list = [], []

    if not await check_dataframe(table_dataframe):
        return [], []

    for num_col, col_item in enumerate(table_dataframe):
        if num_col == 7: break

        mask = table_dataframe[col_item].str.contains(f"{text_too_search}", case=False, regex=True, na=False)
        df_res: DataFrame = table_dataframe.loc[mask]

        menu_list: list = list(df_res['index'])
        menu_text_list: list = list(df_res['text'])

    return menu_list, menu_text_list


async def check_dataframe(dataframe: DataFrame) -> bool:
    """Проверка dataframe на наличие данных

    :param dataframe:
    :return:
    """
    if dataframe is None:
        return False

    if dataframe.empty:
        return False

    return True


async def send_error_message(chat_id, error_text: str, state: FSMContext = None):
    logger.error(error_text)

    reply_markup = None
    if state:
        v_data: dict = await state.get_data()
        previous_level: str = v_data.get('previous_level', '')

        reply_markup = InlineKeyboardMarkup(resize_keyboard=True)
        reply_markup: InlineKeyboardMarkup = await add_previous_paragraph_button(
            reply_markup=reply_markup, previous_level=previous_level
        )

    await bot_send_message(chat_id=chat_id, text=error_text, reply_markup=reply_markup)


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])
