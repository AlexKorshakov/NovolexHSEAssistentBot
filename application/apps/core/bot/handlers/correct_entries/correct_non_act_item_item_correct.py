from __future__ import annotations

import asyncio

from aiogram import types
from pandas import DataFrame

from apps.MyBot import MyBot, bot_send_message, bot_delete_message, bot_delete_markup
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.handlers.correct_entries.correct_support import create_user_dataframe, \
    create_lite_dataframe_from_query, get_item_number_from_call, check_dataframe
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb

from apps.core.database.db_utils import db_get_data_dict_from_table_with_id
from apps.core.database.query_constructor import QueryConstructor
from apps.core.settyngs import get_sett
from apps.notify_admins import get_hse_dataframe, get_hse_role_is_admins_list
from loader import logger

COLUMNS_DICT: dict = {
    # 'id': '' # не редактируется,
    # 'function': '',
    # 'name': '',
    # 'user_id': '',
    # 'hse_id': '',
    # 'location_id': '' # не редактируется,
    # 'violation_id': 'Номер сообщения с записью' # не редактируется,
    # 'work_shift_id': '',
    # 'created_at': '',
    # 'updated_at': '',

    'comment': 'комментарий к нарушению',
    'description': 'описание нарушения',

    'main_location_id': 'основную локацию',
    'sub_location_id': 'площадку',
    'main_category_id': 'основную категорию',
    'status_id': 'статус',
    'finished_id': 'статус процесса устранения',
    'general_contractor_id': 'подрядную организацию',
    'category_id': 'категорию нарушения',
    'normative_documents_id': 'нормативку',
    'violation_category_id': 'степень опасности ситуации',
    'incident_level_id': 'уровень происшествия',
    'act_required_id': 'требуется ли оформление',
    'elimination_time_id': 'кол-во дней на устранение',
    # 'file_id': '',
    # 'title': '', == comment

}

SPECIAL_COLUMNS_DICT: dict = {
    'act_number': 'номер Акта',
    'is_published': 'опубликование',
    'agreed_id': 'согласование',
    'photo': 'photo-файл',
    'json': 'json-файл',
}

RESULT_DICT: dict = {
    "location_id": 'core_location',
    "main_category_id": 'core_maincategory',
    "category_id": 'core_category',
    "violation_category_id": 'core_violationcategory',
    "incident_level_id": 'core_incidentlevel',
    "act_required_id": 'core_actrequired',
    "status_id": 'core_status',
    "main_location_id": 'core_mainlocation',
    "elimination_time_id": 'core_eliminationtime',
    "finished_id": 'core_finished',

    "normative_documents_id": 'core_normativedocuments',
    "sub_location_id": 'core_sublocation',
    "general_contractor_id": 'core_generalcontractor',

    'description': 'core_violations',
    'comment': 'core_violations',

    'act_number': 'core_violations',
    'is_published': 'core_violations',
    "agreed_id": 'core_agreed',
    'photo': 'core_violations',
    'json': 'core_violations',
}


# 'day': '',
# 'month': '',
# 'year': '',
# 'week_id': '',
# 'quarter': '',
# 'day_of_year': '',
# 'json_folder_id': '',
# 'parent_id': '',
# 'photo_folder_id': '',
# 'report_folder_id': '',
# 'coordinates': '',
# 'latitude': '',
# 'longitude': '',
# 'json_file_path': '',
# 'json_full_name': '',
# 'photo_file_path': '',
# 'photo_full_name': '',
# 'user_fullname': '',


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['correct_non_act_item_item_correct']))
async def call_correct_non_act_item_item_correct(call: types.CallbackQuery = None, callback_data: dict[str, str] = None,
                                                 user_id: int | str = None):
    """Обработка ответов содержащихся в callback_data "Финализировать и записать"
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {callback_data = }')

    await bot_delete_markup(message=call.message)

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    item_number_text = await get_item_number_from_call(call, hse_user_id)
    if not item_number_text: return

    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "id": item_number_text,
        },
    }
    query: str = await QueryConstructor(None, 'core_violations', **query_kwargs).prepare_data()

    violations_dataframe: DataFrame = await create_lite_dataframe_from_query(query=query, table_name='core_violations')
    if not await check_dataframe(violations_dataframe, hse_user_id):
        return False

    user_violations_df: DataFrame = await create_user_dataframe(hse_user_id, violations_dataframe)
    if not await check_dataframe(user_violations_df, hse_user_id):
        return False

    text_violations: str = await text_processor_user_violations(user_violations_df, hse_user_id)

    markup = types.InlineKeyboardMarkup()
    reply_markup: types.InlineKeyboardMarkup = await add_correct_inline_keyboard_with_action(
        markup=markup, item_number_text=item_number_text, value_dict=COLUMNS_DICT
    )

    hse_dataframe = await get_hse_dataframe()
    hse_role_is_admins_list: list = await get_hse_role_is_admins_list(hse_dataframe=hse_dataframe)

    if get_sett(cat='enable_features', param='correct_special_value').get_set():
        if hse_user_id in hse_role_is_admins_list:
            reply_markup: types.InlineKeyboardMarkup = await add_correct_inline_keyboard_with_action(
                markup=markup, item_number_text=item_number_text, value_dict=SPECIAL_COLUMNS_DICT
            )

    await bot_send_message(chat_id=hse_user_id, text=text_violations, reply_markup=reply_markup)

    msg_id = call.message.message_id
    await bot_delete_message(chat_id=hse_user_id, message_id=msg_id, sleep_sec=15)

    return True


async def text_processor_user_violations(user_violations_df: DataFrame, hse_user_id: str | int) -> str:
    """Формирование текста для отправки пользователю

    """
    unique_items_ids: list = user_violations_df.id.unique().tolist()

    items_description: list = []

    for item_id in unique_items_ids:

        item_violations_dataframe = user_violations_df.copy(deep=True)
        item_df = item_violations_dataframe.loc[item_violations_dataframe['id'] == item_id]

        if not await check_dataframe(item_violations_dataframe, hse_user_id):
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

    header_text: str = 'Выбранный пункт:'
    footer_text: str = 'Выберите характеристику для изменения'

    final_text: str = f'{header_text} \n\n{items_text}  \n\n{footer_text}'
    return final_text


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


async def add_correct_inline_keyboard_with_action(
        markup: types.InlineKeyboardMarkup(), item_number_text: str | int, value_dict: dict
):
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """

    for k, v in value_dict.items():
        markup.add(types.InlineKeyboardButton(text=v, callback_data=f'characteristic_{k}_{item_number_text}'))

    return markup


async def test():
    await call_correct_non_act_item_item_correct(user_id='373084462')


if __name__ == '__main__':
    asyncio.run(test())
