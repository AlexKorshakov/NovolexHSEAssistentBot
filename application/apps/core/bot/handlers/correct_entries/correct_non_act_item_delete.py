from __future__ import annotations

import asyncio
from datetime import datetime

from aiogram import types
from pandas import DataFrame

from apps.MyBot import MyBot, bot_send_message, bot_delete_markup
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.handlers.correct_entries.correct_entries_handler import correct_entries_handler, del_file
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages import Messages, LogMessage
from apps.core.bot.messages.messages_test import msg
from apps.core.database.db_utils import (db_get_data_list,
                                         db_get_clean_headers,
                                         db_del_item_from_table)
from apps.core.database.query_constructor import QueryConstructor
from apps.core.utils.secondary_functions.get_filepath import Novolex_media_path
from loader import logger


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['correct_non_act_item_delete']))
async def call_correct_non_act_item_delete(call: types.CallbackQuery = None, callback_data: dict[str, str] = None,
                                           user_id: int | str = None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST
    """

    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {callback_data = }')

    await bot_delete_markup(message=call.message)

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return


    if not call:
        await bot_send_message(chat_id=hse_user_id, text=Messages.Error.error_call)
        return

    if not call.message.values['text']:
        await bot_send_message(chat_id=hse_user_id, text=Messages.Error.error_call_text)
        return

    item_number_text = call.message.values['text'].split('_')[-1].split(' ')[-1]
    logger.debug(f'{hse_user_id = } {item_number_text = }')
    try:
        item_number_text = int(item_number_text)
    except Exception as err:
        logger.error(f'{hse_user_id = } {repr(err)} {item_number_text = }')
        await bot_send_message(chat_id=hse_user_id, text=Messages.Error.error_command)
        # TODO Delete
        logger.error(f'{hse_user_id = } Messages.Error.error_action')
        msg_text = await msg(hse_user_id, cat='error', msge='error_action', default=Messages.Error.error_action).g_mas()
        await bot_send_message(chat_id=hse_user_id, text=msg_text)
        return

    reply_markup = await add_correct_act_delete_inline_keyboard_with_action()
    act_delete_text: str = 'Вы уверены что хотите удалить запись полностью и окончательно? ' \
                           'Все файлы записи также будут удалены с сервера и не подлежат восстановлению \n' \
                           f'Выбрано act_number_{item_number_text}'
    await bot_send_message(chat_id=hse_user_id, text=act_delete_text, reply_markup=reply_markup)


async def add_correct_act_delete_inline_keyboard_with_action():
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """

    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton('Да. Удалить Запись полностью',
                                          callback_data=posts_cb.new(id='-', action='correct_non_act_item_delete_yes')))
    markup.add(types.InlineKeyboardButton('Нет. Вернуться',
                                          callback_data=posts_cb.new(id='-', action='correct_non_act_item_delete_not')))
    return markup


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['correct_non_act_item_delete_not']))
async def call_correct_act_delete_not(call: types.CallbackQuery = None, callback_data: dict[str, str] = None,
                                      user_id: int | str = None):
    """Обработка ответов
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {callback_data = }')

    await bot_delete_markup(message=call.message)

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    await correct_entries_handler(hse_user_id=hse_user_id)


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['correct_non_act_item_delete_yes']))
async def call_correct_act_delete_yes(call: types.CallbackQuery = None, callback_data: dict[str, str] = None,
                                      user_id: [int, str] = None):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST
    """

    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {callback_data = }')

    await bot_delete_markup(message=call.message)

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    if not call:
        await bot_send_message(chat_id=hse_user_id, text=Messages.Error.error_call)
        return

    if not call.message.values['text']:
        await bot_send_message(chat_id=hse_user_id, text=Messages.Error.error_call_text)
        return

    item_number_text = call.message.values['text'].split('_')[-1].split(' ')[-1]
    logger.debug(f'{hse_user_id = } {item_number_text = }')

    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "id": item_number_text,
        },
    }
    query: str = await QueryConstructor(None, 'core_violations', **query_kwargs).prepare_data()

    violations_dataframe: DataFrame = await create_lite_dataframe_from_query(query=query, table_name='core_violations')
    if violations_dataframe.empty:
        logger.error(f'{hse_user_id = } {Messages.Error.dataframe_is_empty}  \n{query = }')
        return
    errors_count: int = 0

    del_act_json_result: bool = await del_act_json(
        hse_user_id=hse_user_id, id_numbers=item_number_text, item_dataframe=violations_dataframe
    )
    if del_act_json_result:
        logger.info(f'{hse_user_id = } Записи записи {item_number_text} в форматах .json удалены с сервера ')

    del_act_photo_result: bool = await del_act_photo(
        hse_user_id=hse_user_id, id_numbers=item_number_text, item_dataframe=violations_dataframe
    )
    if del_act_photo_result:
        logger.info(f'{hse_user_id = } Фотоматериалы записи {item_number_text} в форматах .jpeg удалены с сервера ')

    del_act_result_execute: bool = await db_del_item_from_table(
        table_name='core_violations', table_column_name='id', file_id=item_number_text
    )

    if del_act_result_execute:
        logger.info(
            f'{hse_user_id = } Данные записи {item_number_text} успешно обновлены в database!')
    else:
        logger.error(
            f'{hse_user_id = } Ошибка обновления данных {item_number_text} в database!')
        errors_count += 1

    if errors_count:
        text: str = f'Акт-предписание не удалён. Количество ошибок: {errors_count}.'
        await bot_send_message(chat_id=hse_user_id, text=text)
        return

    text: str = f'Данные записи {item_number_text} успешно обновлены в database! Пункт удален.'
    await bot_send_message(chat_id=hse_user_id, text=text)


async def get_act_data(*, hse_user_id: int | str, act_number_text: int | str,
                       table_name: str = None) -> DataFrame or None:
    """Получение данных акта в формате DataFrame """

    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "act_number": act_number_text,
        },
    }
    query: str = await QueryConstructor(None, table_name, **query_kwargs).prepare_data()

    act_dataframe: DataFrame = await create_lite_dataframe_from_query(query=query, table_name=table_name)
    if act_dataframe is None:
        logger.error(f'{hse_user_id = } {Messages.Error.dataframe_is_empty}  \n{query = }')
        return

    if act_dataframe.empty:
        logger.error(f'{hse_user_id = } {Messages.Error.dataframe_is_empty}  \n{query = }')
        return

    return act_dataframe


async def del_act_doc_pdf_from_gdrive(*, hse_user_id: int | str, act_datas_query: DataFrame = None):
    """Удаление сформированного акта в форматах .doc и .pdf из google drive

    :return
    """
    # TODO: check delete_violation_files_from_gdrive
    violation: dict = act_datas_query.to_dict()
    delete_violation_files_from_gdrive_result: bool = False  # await delete_violation_files_from_gdrive(violation)

    if not delete_violation_files_from_gdrive_result:
        logger.error(f'{hse_user_id = } {Messages.Error.file_not_found}')
        return False
    return True


async def del_act_json(*, hse_user_id: int | str, id_numbers: int | str,
                       item_dataframe: DataFrame = None) -> bool:
    """Удаление сформированного акта в форматах .doc и .pdf с сервера

    :return:
    """
    item_df = item_dataframe.loc[item_dataframe['id'] == int(id_numbers)]

    try:
        json_full_name: str = f"{Novolex_media_path}\\HSE\\{item_df['json'].values[0]}"
    except IndexError as err:
        logger.error(f'{hse_user_id = } Не удалось получить данные записи {id_numbers} {repr(err)}')
        return False

    del_file_json_result: bool = await del_file(path=json_full_name)
    if not del_file_json_result:
        logger.error(f'{hse_user_id = } Не удалось  запись {id_numbers} в формате .json с сервера ')
        return False
    return True


async def del_act_photo(*, hse_user_id: int | str, id_numbers: int | str,
                        item_dataframe: DataFrame = None) -> bool:
    """Удаление сформированного акта в форматах .doc и .pdf с сервера

    :return:
    """
    try:
        item_df = item_dataframe.loc[item_dataframe['id'] == int(id_numbers)]
    except IndexError as err:
        logger.error(f'{hse_user_id = } Не удалось получить данные записи {id_numbers} {repr(err)}')
        return False

    photo_full_name: str = f"{Novolex_media_path}\\HSE\\{item_df['photo'].values[0]}"
    del_file_photo_result: bool = await del_file(path=photo_full_name)
    if not del_file_photo_result:
        logger.error(f'{hse_user_id = } Не удалось удалить запись {id_numbers} в формате .jpeg с сервера ')
        return False
    return True


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


async def get_now() -> str:
    """Возвращает текущую дату и время.
    :return: str
    """
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")

