from __future__ import annotations

import asyncio
import math
import traceback
from datetime import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from pandas import DataFrame

from apps.MyBot import bot_send_message, MyBot, bot_send_photo
from apps.core.bot.data.board_config import BoardConfig as board_config
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import build_inlinekeyboard, posts_cb
from apps.core.bot.messages.messages import LogMessage, Messages
from apps.core.bot.messages.messages_test import msg
from apps.core.database.db_utils import (db_get_data_list,
                                         db_get_data_dict_from_table_with_id,
                                         db_get_clean_headers)
from apps.core.database.query_constructor import QueryConstructor
from apps.core.settyngs import get_sett
from apps.core.utils.secondary_functions.get_filepath import Novolex_media_path
from config.config import REPORT_NAME, SEPARATOR
from loader import logger


async def periodic_check_unclosed_points_for_subcontractor(state: FSMContext = None):
    """Периодическая проверка незакрытых пунктов и актов"""

    while True:

        offset_hour: int = get_sett(cat='param', param='offset_hour').get_set()
        work_period: int = get_sett(cat='param', param='check_work_period').get_set()

        await asyncio.sleep(1)

        if not get_sett(cat='enable_feature', param='check_unclosed_points_for_subcontractor').get_set():
            logger.warning(f'{await fanc_name()} not access')
            await asyncio.sleep(work_period)
            continue

        now = datetime.now()
        if not 18 + offset_hour > now.hour + 1 > 9 + offset_hour:
            logger.info(f"{LogMessage.Check.time_period_error} ::: {await get_now()}")
            await asyncio.sleep(work_period)
            continue

        result_check_list: bool = await check_acts_prescriptions_status_for_subcontractor(state=state)
        if result_check_list:
            logger.info(f"{LogMessage.Check.periodic_check_unclosed_points} ::: {await get_now()}")
        else:
            logger.error(
                f'Error periodic_check_unclosed_points_for_subcontractor {result_check_list = } ::: {await get_now()}')

        await asyncio.sleep(work_period)


async def check_acts_prescriptions_status_for_subcontractor(*args, state: FSMContext = None):
    """

    :return:
    """
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
    if not await check_dataframe(violations_dataframe, hse_user_id=None):
        return False

    subcontractor_role_receive_notifications_list: list = await get_subcontractor_role_receive_notifications_list(
        violations_dataframe)

    if not subcontractor_role_receive_notifications_list:
        return False

    notifications_list: list = await get_notifications_list_list(
        violations_df=violations_dataframe, scr_list=subcontractor_role_receive_notifications_list
    )

    if not notifications_list:
        return False

    for item_dict in notifications_list:
        for chat_id, user_violations in item_dict.items():

            text_item: str = await text_processor_item_violations(user_violations)
            text_violations: str = await text_processor_user_violations(user_violations, text_item)

            if not text_violations:
                continue

            for item_txt in await text_processor(text=text_violations):
                await bot_send_message(chat_id=chat_id, text=item_txt)

            text_notification: str = 'Выберите пункт'
            unique_violations_numbers: list = user_violations.id.unique().tolist()
            unique_violations_numbers: list = [f'sub_con_vio_number_{item}' for item in unique_violations_numbers if
                                               item]

            menu_level = await board_config(state, "menu_level", 1).set_data()
            menu_list = await board_config(state, "menu_list", unique_violations_numbers).set_data()
            count_col = await board_config(state, "count_col", 2).set_data()

            reply_markup = await build_inlinekeyboard(some_list=menu_list, num_col=count_col, level=menu_level)
            await bot_send_message(chat_id=chat_id, text=text_notification, reply_markup=reply_markup)

    return True


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


async def text_processor_user_violations(user_violations: DataFrame, item_text: str = None) -> str:
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
        if not await check_dataframe(violations_dataframe, hse_user_id=None):
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
        if not await check_dataframe(violations_dataframe, hse_user_id=None):
            continue

        act_date = violations_dataframe.act_date.unique().tolist()[0]

        general_constractor_id = violations_dataframe.act_general_contractor_id.unique().tolist()[-1]

        general_constractor: str = await get_item_title_for_id(
            table_name='core_generalcontractor', item_id=general_constractor_id
        )

        item_info = f'Ном: {act_number} от {act_date} {general_constractor}' \
                    f' Всего пунктов: {len_act_violations}. Незакрыто: {unclosed_points}'

        act_description.append(item_info)
        len_unique_acts += 1

    non_acts_items_df: DataFrame = user_violations.loc[user_violations['act_number'] == '']
    non_acts_items: int = len(non_acts_items_df)
    non_acts_text: str = f'Записей вне актов всего: {non_acts_items}'

    header_text: str = f'У вас есть незакрытые акты: Всего актов {len_unique_acts}'

    acts_text: str = '\n'.join(act_description)

    final_text_list: list = [header_text, acts_text, item_text, non_acts_text]
    final_text: str = '\n\n'.join(final_text_list)
    return final_text


async def text_processor_item_violations(user_violations_df: DataFrame) -> str:
    """Формирование текста для отправки пользователю

    """
    unique_items_ids: list = user_violations_df.id.unique().tolist()

    items_description: list = []

    for item_id in unique_items_ids:

        item_violations_dataframe = user_violations_df.copy(deep=True)
        item_df = item_violations_dataframe.loc[item_violations_dataframe['id'] == item_id]

        if not await check_dataframe(item_violations_dataframe):
            continue

        created_at = item_df['created_at'].values[0]
        item_status = await get_item_title_for_id(
            'core_status', item_id=item_df['status_id'].values[0]
        )
        item_main_category = await get_item_title_for_id(
            table_name='core_maincategory', item_id=item_df['main_category_id'].values[0]
        )
        item_category = await get_item_title_for_id(
            table_name='core_category', item_id=item_df['category_id'].values[0]
        )
        item_general_contractor_id = await get_item_title_for_id(
            table_name='core_generalcontractor', item_id=item_df['general_contractor_id'].values[0]
        )
        item_main_location = await get_item_title_for_id(
            table_name='core_mainlocation', item_id=item_df['main_location_id'].values[0]
        )
        item_sub_location = await get_item_title_for_id(
            table_name='core_sublocation', item_id=item_df['sub_location_id'].values[0]
        )
        item_description = item_df['description'].values[0]
        elimination_time = await get_item_title_for_id(
            table_name='core_eliminationtime', item_id=item_df['elimination_time_id'].values[0]
        )
        normative_documents_title = await get_item_title_for_id(
            table_name='core_normativedocuments', item_id=item_df['normative_documents_id'].values[0],
        )

        normative_documents_desc = await get_item_title_for_id(
            table_name='core_normativedocuments', item_id=item_df['normative_documents_id'].values[0],
            item_name='normative'
        )

        item_info = f'Ном пункта: {item_id} от {created_at} Статус: {item_status} \n\n' \
                    f'Устранить до: {elimination_time} \n' \
                    f'Подрядчик: {item_general_contractor_id} \n' \
                    f'Территория: {item_main_location} - {item_sub_location} \n' \
                    f'Направление: {item_main_category} \n' \
                    f'Категория: {item_category} \n' \
                    f'Описание: {item_description} \n' \
                    f'Подкатегория: {normative_documents_title} \n' \
                    f'Нормативка: {normative_documents_desc}\n'

        items_description.append(item_info)

    items_text: str = '\n'.join(items_description)

    # header_text: str = 'Выбранный пункт:'
    footer_text: str = 'Выберите характеристику для изменения'

    final_text_list: list = [
        # header_text,
        items_text,
        # footer_text
    ]
    final_text: str = '\n\n'.join(final_text_list)
    return final_text


async def get_subcontractor_role_receive_notifications_list(violations_dataframe: DataFrame = None) -> list:
    """Получение списка пользователей кому отправляются уведомления
    """

    if not await check_dataframe(violations_dataframe, hse_user_id=None):
        # await bot_send_message(chat_id=hse_user_id, text='Данные не найдены dataframe')
        return []

    db_table_name: str = 'core_subcontractoruser'
    kwargs: dict = {
        "action": 'SELECT',
        "subject": '*',
    }
    query: str = await QueryConstructor(table_name=db_table_name, **kwargs).prepare_data()
    subc_role_receive_df: DataFrame = await create_lite_dataframe_from_query(query=query, table_name=db_table_name)
    if not await check_dataframe(subc_role_receive_df, hse_user_id=None):
        return []

    clean_headers = await db_get_clean_headers(table_name=db_table_name)

    subc_list: list = []
    for _, subc_data in enumerate(subc_role_receive_df.itertuples(index=False), start=1):
        subc_list.append(dict(zip(clean_headers, subc_data)))

    return subc_list


async def get_notifications_list_list(violations_df: DataFrame = None, scr_list: list = None) -> list:
    """

    :return:
    """
    if not await check_dataframe(violations_df, hse_user_id=None):
        return []

    if not scr_list:
        return []

    notyf_list: list = []
    for subc_item in scr_list:

        if not subc_item['subcontractor_telegram_id']:
            continue

        v_df = violations_df.copy(deep=True)
        gen_cons_id: int = subc_item.get('subcontractor_organization', None)
        subL_id: int = subc_item.get('subcontractor_sub_locations', None)

        v_df = v_df.loc[v_df['general_contractor_id'] == gen_cons_id]
        if not await check_dataframe(v_df, hse_user_id=None):
            continue

        v_df = v_df.loc[v_df['sub_location_id'] == subL_id]
        if not await check_dataframe(v_df, hse_user_id=None):
            continue

        # v_list: list = [dict(zip(clean_headers, subc_data)) for subc_data in v_df.itertuples(index=False)]

        notyf_list.append(
            {
                subc_item['subcontractor_telegram_id']: v_df,
            }
        )

    return notyf_list


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


async def check_dataframe(dataframe: DataFrame, hse_user_id: str | int = None) -> bool:
    """Проверка dataframe на наличие данных

    :param dataframe:
    :param hse_user_id: id пользователя
    :return:
    """
    if dataframe is None:
        text_violations: str = 'не удалось получить данные!'
        logger.error(f'{hse_user_id = } {text_violations}')
        return False

    if dataframe.empty:
        logger.error(f'{hse_user_id = } {Messages.Error.dataframe_is_empty}')
        return False

    return True


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


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])


@MyBot.dp.callback_query_handler(lambda call: 'sub_con_vio_number_' in call.data)
async def sub_con_vio_number_answer(call: types.CallbackQuery, user_id: str = None) -> None:
    """Обработка ответов
    """
    chat_id = user_id if user_id else call.message.chat.id
    language = call.from_user.language_code
    sub_con_vio_number = call.data.split('_')[-1]

    query_kwargs: dict = {
        "action": 'SELECT',
        "subject": '*',
        "conditions": {
            "id": sub_con_vio_number,
        },
    }
    query: str = await QueryConstructor(None, 'core_violations', **query_kwargs).prepare_data()
    violations_dataframe: DataFrame = await create_lite_dataframe_from_query(query=query, table_name='core_violations')
    if not await check_dataframe(violations_dataframe, hse_user_id=None):
        message_txt: str = 'error'
        await bot_send_message(chat_id=chat_id, text=message_txt)
        return

    violations_text: str = await text_processor_violations(violations_dataframe, sub_con_vio_number)
    if not violations_text:
        message_txt: str = 'error'
        await bot_send_message(chat_id=chat_id, text=message_txt)
        return

    reply_markup = await add_inline_keyboard_with_action(user_id=chat_id, language=language)
    await bot_send_message(chat_id=chat_id, text=violations_text, reply_markup=reply_markup)


async def text_processor_violations(violations_df, violation_id):
    """

    :param violations_df:
    :param violation_id:
    :return:
    """
    unique_items_ids: list = violations_df.id.unique().tolist()

    items_description: list = []

    for item_id in unique_items_ids:

        item_violations_dataframe = violations_df.copy(deep=True)
        item_df = item_violations_dataframe.loc[item_violations_dataframe['id'] == item_id]

        if not await check_dataframe(item_violations_dataframe):
            continue

        created_at = item_df['created_at'].values[0]
        item_status = await get_item_title_for_id(
            'core_status', item_id=item_df['status_id'].values[0]
        )
        item_main_category = await get_item_title_for_id(
            table_name='core_maincategory', item_id=item_df['main_category_id'].values[0]
        )
        item_category = await get_item_title_for_id(
            table_name='core_category', item_id=item_df['category_id'].values[0]
        )
        item_general_contractor_id = await get_item_title_for_id(
            table_name='core_generalcontractor', item_id=item_df['general_contractor_id'].values[0]
        )
        item_main_location = await get_item_title_for_id(
            table_name='core_mainlocation', item_id=item_df['main_location_id'].values[0]
        )
        item_sub_location = await get_item_title_for_id(
            table_name='core_sublocation', item_id=item_df['sub_location_id'].values[0]
        )
        item_description = item_df['description'].values[0]
        elimination_time = await get_item_title_for_id(
            table_name='core_eliminationtime', item_id=item_df['elimination_time_id'].values[0]
        )
        normative_documents_title = await get_item_title_for_id(
            table_name='core_normativedocuments', item_id=item_df['normative_documents_id'].values[0],
        )

        normative_documents_desc = await get_item_title_for_id(
            table_name='core_normativedocuments', item_id=item_df['normative_documents_id'].values[0],
            item_name='normative'
        )

        item_info: list = [
            f'Ном пункта: {item_id} от {created_at} Статус: {item_status} \n',
            f'Время на устранение: {elimination_time}',
            f'Подрядчик: {item_general_contractor_id} ',
            f'Территория: {item_main_location} - {item_sub_location} ',
            # f'Направление: {item_main_category} ' ,
            # f'Категория: {item_category} ',
            f'Описание: {item_description} ',
            # f'Подкатегория: {normative_documents_title} ' ,
            # f'Нормативка: {normative_documents_desc}',
        ]
        items_description.append('\n'.join(item_info))

    items_text: str = ''.join(items_description)

    # header_text: str = 'Выбранный пункт:'
    footer_text: str = f"sub_con_vio_number_{violation_id}"

    final_text_list: list = [
        # header_text,
        items_text,
        footer_text
    ]
    final_text: str = '\n\n'.join(final_text_list)
    return final_text


async def text_processor_violation_item(violations_df, violation_id):
    """

    :param violations_df:
    :param violation_id:
    :return:
    """
    unique_items_ids: list = violations_df.id.unique().tolist()

    items_description: list = []

    for item_id in unique_items_ids:

        item_violations_dataframe = violations_df.copy(deep=True)
        item_df = item_violations_dataframe.loc[item_violations_dataframe['id'] == item_id]

        if not await check_dataframe(item_violations_dataframe):
            continue

        created_at = item_df['created_at'].values[0]

        item_status = await get_item_title_for_id(
            'core_status', item_id=item_df['status_id'].values[0]
        )
        item_main_category = await get_item_title_for_id(
            table_name='core_maincategory', item_id=item_df['main_category_id'].values[0]
        )
        item_category = await get_item_title_for_id(
            table_name='core_category', item_id=item_df['category_id'].values[0]
        )
        item_general_contractor_id = await get_item_title_for_id(
            table_name='core_generalcontractor', item_id=item_df['general_contractor_id'].values[0]
        )
        item_main_location = await get_item_title_for_id(
            table_name='core_mainlocation', item_id=item_df['main_location_id'].values[0]
        )
        item_sub_location = await get_item_title_for_id(
            table_name='core_sublocation', item_id=item_df['sub_location_id'].values[0]
        )
        item_description = item_df['description'].values[0]
        elimination_time = await get_item_title_for_id(
            table_name='core_eliminationtime', item_id=item_df['elimination_time_id'].values[0]
        )
        normative_documents_title = await get_item_title_for_id(
            table_name='core_normativedocuments', item_id=item_df['normative_documents_id'].values[0],
        )
        normative_documents_desc = await get_item_title_for_id(
            table_name='core_normativedocuments', item_id=item_df['normative_documents_id'].values[0],
            item_name='normative'
        )
        item_comment = item_df['comment'].values[0]

        incident_level = await get_item_title_for_id(
            table_name='core_incidentlevel', item_id=item_df['incident_level_id'].values[0],
        )
        hse_full_name = await get_item_title_for_id(
            table_name='core_hseuser', item_id=item_df['hse_id'].values[0],
            item_name='hse_full_name'
        )
        hse_function = await get_item_title_for_id(
            table_name='core_hseuser', item_id=item_df['hse_id'].values[0],
            item_name='hse_function'
        )

        item_info: list = [
            f'Ном пункта: {item_id} от {created_at} Статус: {item_status} \n',
            f'Время на устранение: {elimination_time}',
            f'Подрядчик: {item_general_contractor_id} ',
            f'Территория: {item_main_location} - {item_sub_location} ',
            f'Направление: {item_main_category} ',
            f'Уровень происшествия: {incident_level} ',
            f'Категория: {item_category} ',
            f'Описание: {item_description} ',
            f'Мероприятия по устранению: {item_comment} ',
            f'Подкатегория: {normative_documents_title} ',
            f'Нормативный документ: {normative_documents_desc}',
            f'Выдал: {hse_function} {hse_full_name}',
        ]
        items_description.append('\n'.join(item_info))

    items_text: str = ''.join(items_description)

    # header_text: str = 'Выбранный пункт:'
    footer_text: str = f"sub_con_vio_number_{violation_id}"

    final_text_list: list = [
        # header_text,
        items_text,
        footer_text
    ]
    final_text: str = '\n\n'.join(final_text_list)
    return final_text


async def add_inline_keyboard_with_action(*, user_id: int, language: str = None):
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """

    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(
        text=await msg(
            user_id, cat='msg_main', msge='get_complete_data', default='Получить полные данные', lang=language
        ).g_mas(),
        callback_data=posts_cb.new(id='-', action='sub_con_get_data'))
    )
    markup.add(types.InlineKeyboardButton(
        text=await msg(
            user_id, cat='msg_main', msge='get_photo', default='Получить фото', lang=language
        ).g_mas(),
        callback_data=posts_cb.new(id='-', action='sub_con_get_photo'))
    )
    # markup.add(types.InlineKeyboardButton(
    #     text=await msg(
    #         user_id, cat='msg_main', msge='upload_fix_photo', default='Загрузить фото устранения', lang=language
    #     ).g_mas(),
    #     callback_data=posts_cb.new(id='-', action='sub_con_upload_photo'))
    # )
    return markup


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['sub_con_get_data']))
async def call_sub_con_get_data(call: types.CallbackQuery, callback_data: dict[str, str], language: str = None,
                                user_id: str = None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST
    """
    hse_user_id = call.message.chat.id
    language = language if language else call.from_user.language_code

    # msg_text = await msg(hse_user_id, cat='error', msge='error_action', default=Messages.Error.error_action,
    #                      lang=language).g_mas()
    # await bot_send_message(chat_id=hse_user_id, text=msg_text)

    chat_id = user_id if user_id else call.message.chat.id
    language = call.from_user.language_code
    sub_con_vio_number = call.message.text.split('_')[-1]

    query_kwargs: dict = {
        "action": 'SELECT',
        "subject": '*',
        "conditions": {
            "id": sub_con_vio_number,
        },
    }
    query: str = await QueryConstructor(None, 'core_violations', **query_kwargs).prepare_data()
    violations_dataframe: DataFrame = await create_lite_dataframe_from_query(query=query, table_name='core_violations')

    if not await check_dataframe(violations_dataframe, hse_user_id=None):
        message_txt: str = 'error'
        await bot_send_message(chat_id=chat_id, text=message_txt)
        return

    violations_text: str = await text_processor_violation_item(violations_dataframe, sub_con_vio_number)
    if not violations_text:
        message_txt: str = 'error'
        await bot_send_message(chat_id=chat_id, text=message_txt)
        return

    # reply_markup = await add_inline_keyboard_with_action(user_id=chat_id, language=language)
    await bot_send_message(
        chat_id=chat_id, text=violations_text,
        # reply_markup=reply_markup
    )


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['sub_con_get_photo']))
async def call_sub_con_get_photo(call: types.CallbackQuery, callback_data: dict[str, str], language: str = None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST
    """
    user_id = call.message.chat.id
    sub_con_vio_number = call.message.text.split('_')[-1]

    language = language if language else call.from_user.language_code

    query_kwargs: dict = {
        "action": 'SELECT',
        "subject": '*',
        "conditions": {
            "id": sub_con_vio_number,
        },
    }
    query: str = await QueryConstructor(None, 'core_violations', **query_kwargs).prepare_data()
    violations_dataframe: DataFrame = await create_lite_dataframe_from_query(query=query, table_name='core_violations')
    if not await check_dataframe(violations_dataframe, hse_user_id=None):
        message_txt: str = 'error'
        await bot_send_message(chat_id=user_id, text=message_txt)
        return

    file_id = violations_dataframe.file_id.values[0]
    date = violations_dataframe.file_id.values[0].split(SEPARATOR)[0]
    hse_id = violations_dataframe.user_id.values[0]

    name = f'{REPORT_NAME}{file_id}.jpg'
    full_photo_path = f"{Novolex_media_path}\\HSE\\{hse_id}\\data_file\\{date}\\photo\\{name}"

    try:
        with open(full_photo_path, 'rb') as photo:
            caption: str = f"{await msg(user_id, cat='msg_main', default='Фото пункта нарушения', lang=language).g_mas()}: {sub_con_vio_number} от {date}"
            await bot_send_photo(
                chat_id=user_id, photo=photo, caption=caption
            )

    except Exception as err:
        logger.error(f"send_report_from_user {repr(err)}")


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['sub_con_upload_photo']))
async def call_sub_con_upload_photo(call: types.CallbackQuery, callback_data: dict[str, str], language: str = None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST
    """
    hse_user_id = call.message.chat.id
    language = language if language else call.from_user.language_code

    msg_text = await msg(hse_user_id, cat='error', msge='error_action', default=Messages.Error.error_action,
                         lang=language).g_mas()
    await bot_send_message(chat_id=hse_user_id, text=msg_text)


async def test():
    # query_kwargs: dict = {
    #     "action": 'SELECT',
    #     "subject": '*',
    #     "conditions": {
    #         "id": sub_con_vio_number,
    #     },
    # }
    # query: str = await QueryConstructor(None, 'core_violations', **query_kwargs).prepare_data()
    # violations_dataframe: DataFrame = await create_lite_dataframe_from_query(query=query, table_name='core_violations')

    await check_acts_prescriptions_status_for_subcontractor()


if __name__ == '__main__':
    asyncio.run(test())
