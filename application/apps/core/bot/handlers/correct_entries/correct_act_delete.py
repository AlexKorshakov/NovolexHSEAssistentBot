from __future__ import annotations

import asyncio

from aiogram import types
from pandas import DataFrame

from apps.MyBot import MyBot, bot_send_message, bot_delete_markup
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.handlers.correct_entries.correct_entries_handler import correct_entries_handler, del_file
from apps.core.bot.handlers.correct_entries.correct_support import create_lite_dataframe_from_query
from apps.core.bot.handlers.correct_entries.correct_support_path import get_full_act_prescription_path
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages import Messages
from apps.core.database.db_utils import db_del_item_from_table
from apps.core.database.query_constructor import QueryConstructor
from apps.core.utils.secondary_functions.get_filepath import Novolex_media_path
from loader import logger


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['correct_act_delete']))
async def call_correct_act_delete(call: types.CallbackQuery = None, callback_data: dict[str, str] = None,
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

    act_number_text = call.message.values['text'].split('_')[-1].split(' ')[-1]
    logger.debug(f'{hse_user_id = } {act_number_text = }')
    try:
        act_number_text = int(act_number_text)
    except Exception as err:
        logger.error(f'{hse_user_id = } {repr(err)} {act_number_text = }')
        await bot_send_message(chat_id=hse_user_id, text=Messages.Error.error_command)
        return

    reply_markup = await add_correct_act_delete_inline_keyboard_with_action()
    act_delete_text: str = 'Вы уверены что хотите удалить акт полностью и окончательно? ' \
                           'Все записи акта также будут удалены из системы \n' \
                           'Все файлы акта также будут удалены с сервера и не подлежат восстановлению \n' \
                           f'Выбрано act_number_{act_number_text}'
    await bot_send_message(chat_id=hse_user_id, text=act_delete_text, reply_markup=reply_markup)


async def add_correct_act_delete_inline_keyboard_with_action():
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """

    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton('Да. Удалить Акт полностью',
                                          callback_data=posts_cb.new(id='-', action='correct_act_delete_yes')))
    markup.add(types.InlineKeyboardButton('Нет. Вернуться',
                                          callback_data=posts_cb.new(id='-', action='correct_act_delete_not')))
    return markup


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['correct_act_delete_not']))
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


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['correct_act_delete_yes']))
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

    act_number_text = call.message.values['text'].split('_')[-1].split(' ')[-1]
    logger.debug(f'{hse_user_id = } {act_number_text = }')

    table_name = 'core_violations'
    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "act_number": act_number_text,
        },
    }
    query: str = await QueryConstructor(None, table_name, **query_kwargs).prepare_data()

    violations_dataframe: DataFrame = await create_lite_dataframe_from_query(query=query, table_name=table_name)
    if violations_dataframe.empty:
        logger.error(f'{hse_user_id = } {Messages.Error.dataframe_is_empty}  \n{query = }')
        return

    unique_id_numbers: list = violations_dataframe.id.unique().tolist()
    logger.debug(f'{hse_user_id = } {unique_id_numbers = }')

    if not unique_id_numbers:
        return

    errors_count: int = 0
    for id_number in unique_id_numbers:

        del_act_json_result: bool = await del_act_json(
            hse_user_id=hse_user_id, id_numbers=id_number, item_dataframe=violations_dataframe
        )
        if del_act_json_result:
            logger.info(f'{hse_user_id = } Записи акта {act_number_text} в форматах .json удалены с сервера ')

        del_act_photo_result: bool = await del_act_photo(
            hse_user_id=hse_user_id, id_numbers=id_number, item_dataframe=violations_dataframe
        )
        if del_act_photo_result:
            logger.info(f'{hse_user_id = } Фотоматериалы акта {act_number_text} в форматах .jpeg удалены с сервера ')

        del_act_result_execute: bool = await db_del_item_from_table(
            table_name='core_violations', table_column_name='id', file_id=id_number
        )

        if del_act_result_execute:
            logger.info(
                f'{hse_user_id = } Данные записи {id_number} акта {act_number_text = } успешно обновлены в database!')
        else:
            logger.error(
                f'{hse_user_id = } Ошибка обновления данных {id_number} акта {act_number_text = } в database!')
            errors_count += 1

    if errors_count:
        text: str = f'Акт-предписание не удалён. Количество ошибок: {errors_count}.'
        await bot_send_message(chat_id=hse_user_id, text=text)
        return

    act_dataframe: DataFrame = await get_act_data(
        hse_user_id=hse_user_id, act_number_text=act_number_text, table_name='core_actsprescriptions'
    )
    if act_dataframe.empty:
        logger.error(f'{hse_user_id = } {Messages.Error.dataframe_is_empty}  \n{act_number_text = }')
        return

    del_act_doc_pdf_local_result: bool = await del_act_doc_pdf_from_local(
        hse_user_id=hse_user_id, act_datas_query=act_dataframe
    )
    if del_act_doc_pdf_local_result:
        logger.info(f'{hse_user_id = } Сформированный акт {act_number_text} в форматах .doc и .pdf удалены с сервера ')

    del_act_doc_pdf_from_gdrive_result: bool = await del_act_doc_pdf_from_gdrive(
        hse_user_id=hse_user_id, act_datas_query=act_dataframe
    )
    if del_act_doc_pdf_from_gdrive_result:
        logger.info(f'{hse_user_id = } Сформированный акт {act_number_text} в форматах .doc и .pdf удалены с gdrive ')

    del_act_result_execute: bool = await db_del_item_from_table(
        table_name='core_actsprescriptions', table_column_name='act_number', file_id=act_number_text
    )

    if del_act_result_execute:
        text: str = f'Все упоминания акта {act_number_text} удалены без ошибок.  \n' \
                    f'Акт-предписание удален из базы. \n' \
                    f'Данные не доступные для редактирования'
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


async def del_act_doc_pdf_from_local(*, hse_user_id: int | str, act_datas_query: DataFrame) -> bool:
    """Удаление сформированного акта в форматах .doc и .pdf с сервера

    :return:
    """

    if act_datas_query.empty:
        logger.error(f'{hse_user_id = } {Messages.Error.dataframe_is_empty}')
        return False

    act_number = act_datas_query['act_number'].values[0]
    act_date = act_datas_query['act_date'].values[0]
    constractor_id = act_datas_query['act_general_contractor_id'].values[0]

    full_act_prescription_path_xlsx: str = await get_full_act_prescription_path(
        chat_id=hse_user_id, act_number=act_number, act_date=act_date, constractor_id=constractor_id
    )
    del_file_xlsx = await del_file(path=full_act_prescription_path_xlsx)
    if not del_file_xlsx:
        logger.error(f'{hse_user_id = } Не удалось удалить акт {act_number} в формате .xlsx с сервера ')

    full_act_prescription_path_pdf = full_act_prescription_path_xlsx.replace(".xlsx", ".pdf")

    del_file_pdf = await del_file(path=full_act_prescription_path_pdf)
    if not del_file_pdf:
        logger.error(f'{hse_user_id = } Не удалось удалить акт {act_number} в формате .pdf с сервера ')

    if not all([del_file_xlsx, del_file_pdf, ]):
        logger.error(
            f'{hse_user_id = } акт {act_number} не удалось удалить с сервера {del_file_xlsx = } {del_file_pdf = }')
        return False

    logger.info(f'{hse_user_id = } Сформированный акт {act_number} в форматах .doc и .pdf удалены с сервера ')
    return True


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


async def test():
    await call_correct_act_delete(user_id='373084462')


if __name__ == '__main__':
    asyncio.run(test())
