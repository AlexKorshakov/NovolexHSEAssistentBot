from __future__ import annotations
import asyncio

from datetime import datetime

from aiogram import types
from pandas import DataFrame

from apps.MyBot import MyBot, bot_send_message, bot_delete_markup
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.handlers.correct_entries.correct_entries_handler import correct_entries_handler
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages import Messages, LogMessage
from apps.core.database.db_utils import (db_get_data_list,
                                         db_get_clean_headers,
                                         db_update_column_value,
                                         db_update_table_column_value)
from apps.core.database.query_constructor import QueryConstructor
from loader import logger


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['correct_act_finalize']))
async def call_correct_act_finalize(call: types.CallbackQuery = None, callback_data: dict[str, str] = None,
                                    user_id: int | str = None):
    """Обработка ответов содержащихся в callback_data "Финализировать и записать"
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
    act_delete_text: str = 'Вы уверены что хотите финализировать и записать акт как завершенный? ' \
                           'Все записи акта также будут финализированы в системе \n' \
                           f'Выбрано act_number_{act_number_text}'
    await bot_send_message(chat_id=hse_user_id, text=act_delete_text, reply_markup=reply_markup)


async def add_correct_act_delete_inline_keyboard_with_action():
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """

    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton('Да. Финализировать и записать',
                                          callback_data=posts_cb.new(id='-', action='correct_act_finalize_yes')))
    markup.add(types.InlineKeyboardButton('Нет. Вернуться',
                                          callback_data=posts_cb.new(id='-', action='correct_act_finalize_not')))
    return markup


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['correct_act_finalize_not']))
async def call_correct_act_finalize_not(call: types.CallbackQuery = None, callback_data: dict[str, str] = None,
                                        user_id: int | str = None):
    """Обработка ответов содержащихся в callback_data "Финализировать и записать"
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {callback_data = }')

    await bot_delete_markup(message=call.message)

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    await correct_entries_handler(hse_user_id=hse_user_id)


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['correct_act_finalize_yes']))
async def call_correct_act_finalize_yes(call: types.CallbackQuery = None, callback_data: dict[str, str] = None,
                                        user_id: int | str = None):
    """Обработка ответов содержащихся в callback_data "Финализировать и записать"
    """

    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = }')
    logger.debug(f'{callback_data = }')

    # await bot_delete_markup(message=call.message)

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

    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "act_number": act_number_text,
        },
    }
    query: str = await QueryConstructor(None, 'core_violations', **query_kwargs).prepare_data()

    violations_dataframe: DataFrame = await create_lite_dataframe_from_query(query=query, table_name='core_violations')
    if violations_dataframe.empty:
        logger.error(f'{hse_user_id = } {Messages.Error.dataframe_is_empty}  \n{query = }')
        return

    unique_id_numbers: list = violations_dataframe.id.unique().tolist()
    logger.debug(f'{hse_user_id = } {unique_id_numbers = }')

    if not unique_id_numbers:
        return

    errors_count: int = 0
    for id_numbers in unique_id_numbers:

        finished_result_execute: bool = await db_update_column_value(
            column_name='finished_id',
            value=1,
            violation_id=str(id_numbers)
        )
        status_result_execute: bool = await db_update_column_value(
            column_name='status_id',
            value=1,
            violation_id=str(id_numbers)
        )

        if finished_result_execute and status_result_execute:
            logger.info(
                f'{hse_user_id = } Данные записи {id_numbers} акта {act_number_text = } успешно обновлены в database!')
        else:
            logger.error(
                f'{hse_user_id = } Ошибка обновления данных {id_numbers} акта {act_number_text = } в database!')
            errors_count += 1

    if errors_count:
        text: str = f'Акт-предписание не закрыт. Количество ошибок: {errors_count}.'
        # await bot_send_message(chat_id=hse_user_id, text=text)
        await bot_send_message(chat_id=hse_user_id, text=text)
        return

    finished_result_execute: bool = await db_update_table_column_value(
        table_name='core_actsprescriptions',
        table_column_name_for_update='act_status_id',
        table_column_name='act_number',
        item_value=str(1),
        item_name=str(act_number_text)
    )

    if finished_result_execute:
        text: str = f'Все пункты акта {act_number_text} финализированы и записаны без ошибок. Акт-предписание закрыт'
        await bot_send_message(chat_id=hse_user_id, text=text)


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


async def test():
    await call_correct_act_finalize(user_id='373084462')


if __name__ == '__main__':
    asyncio.run(test())
