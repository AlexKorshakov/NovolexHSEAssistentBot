from __future__ import annotations

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup
from pandas import DataFrame

import apps.xxx
from apps.MyBot import bot_send_message, MyBot
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.filters.custom_filters import filter_is_private
from apps.core.bot.handlers.correct_entries.correct_non_act_item_item_correct import RESULT_DICT, COLUMNS_DICT
from apps.core.bot.handlers.correct_entries.correct_support import check_dataframe, create_lite_dataframe_from_query, \
    spotter_data, check_spotter_data, get_violations_df
from apps.core.bot.handlers.correct_entries.correct_support_updater import update_column_value
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages import Messages
from apps.core.bot.states import CorrectViolationsState
from apps.core.database.query_constructor import QueryConstructor
from loader import logger


async def text_meaning_handler(hse_user_id: int | str, character: str, item_number: int | str,
                               violations_dataframe: DataFrame, state: FSMContext = None) -> bool:
    """Обработка текстовых характеристик

    :param hse_user_id: int | str id пользователя.
    :param violations_dataframe: DataFrame - DataFrame с данными записи
    :param item_number:  int | str номер записи в база данных
    :param character: str - название изменяемой характеристики записи.
    :return: bool - True если успешно or False
    """
    character_table_name: str = RESULT_DICT.get(character, None)

    if not character_table_name:
        logger.error(f'{hse_user_id = } {item_number = } {character = } not character in character_table_name')
        await bot_send_message(chat_id=hse_user_id, text=f'Ошибка при изменении показателя {character = }')
        return False

    text = await text_processor_character_text(violations_dataframe, character, item_number, hse_user_id)

    reply_markup = InlineKeyboardMarkup()
    reply_markup.add(types.InlineKeyboardButton(
        text='Продолжить без изменений', callback_data=posts_cb.new(id='-', action='correct_text_meaning_act_cancel'))
    )

    await bot_send_message(chat_id=hse_user_id, text=text, reply_markup=reply_markup)

    if character == 'description':
        await CorrectViolationsState.description.set()
    if character == 'comment':
        await CorrectViolationsState.comment.set()

    spotter_data['calld_prefix'] = f"corr_{character_table_name}_"
    spotter_data['character_table_name'] = f"{character_table_name}"
    spotter_data['hse_user_id'] = f"{hse_user_id}"
    spotter_data['item_number_text'] = f"{item_number}"
    spotter_data['character'] = f"{character}"

    return True


async def text_processor_character_text(violations_dataframe: DataFrame, character: str, item_number_text: str | int,
                                        hse_user_id: str | int) -> str:
    """Формирование текста для отправки пользователю

    """

    if not await check_dataframe(violations_dataframe, hse_user_id):
        character_table_name = RESULT_DICT.get(character, None)
        query_kwargs: dict = {
            "action": 'SELECT', "subject": '*',
            "conditions": {
                "id": item_number_text,
            },
        }
        query: str = await QueryConstructor(None, character_table_name, **query_kwargs).prepare_data()
        violations_dataframe: DataFrame = await create_lite_dataframe_from_query(
            query=query, table_name='core_violations'
        )
        if not await check_dataframe(violations_dataframe, hse_user_id):
            return ''

    sub_character_text: str = violations_dataframe[character].values[0]

    character_title: str = COLUMNS_DICT.get(character, None)

    header_text: str = f'Выберите значение для показателя Изменить "{character_title}" для ' \
                       f'записи item_number_{item_number_text}'

    old_text: str = f'Значение в базе:\n\n{sub_character_text}'
    footer_text: str = 'Введите новое значение нажмите кнопку "Продолжить без изменений" '

    final_text: str = f'{header_text} \n\n{old_text}\n\n{footer_text}'
    return final_text


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['correct_text_meaning_act_cancel']))
@MyBot.dp.message_handler(filter_is_private, Text(equals=Messages.correct_cancel), state=CorrectViolationsState.all_states)
async def cancel(message: types.Message, state: FSMContext, user_id: int | str = None):
    """Отмена изменений

    :param message:
    :param state:
    :param user_id:
    :return:
    """
    hse_user_id = message.message.chat.id if message else user_id

    await state.finish()
    await bot_send_message(chat_id=hse_user_id, text=Messages.Violations.canceled)


@MyBot.dp.message_handler(filter_is_private, state=CorrectViolationsState.all_states)
async def correct_violations_data_all_states_answer(message: types.Message, state: FSMContext):
    """Обработка изменений

    :param message:
    :param state:
    :return:
    """
    chat_id = message.chat.id
    state_name = await get_state_storage_name(state, chat_id)
    await state.finish()
    await all_states(hse_user_id=chat_id, correct_data=message.text, state_name=state_name)


async def get_state_storage_name(state, chat_id):
    """Получение имени состояния state[state]
    """
    state_storage = dict(apps.xxx.storage.data)
    state_name: str = state_storage.get(f'{chat_id}').get(f'{chat_id}').get('state').split(':')[-1]

    return state_name


async def all_states(*, hse_user_id: str, correct_data: str, state_name: str):
    """Обработка состояний из get_state_storage_name и данных correct_data

    :param hse_user_id: id пользователя / чата
    :param correct_data: данне для коррекции параметра state_name
    :param state_name: имя параметра для коррекции
    :return:
    """

    logger.debug(f'{hse_user_id = } {correct_data = }')

    # await bot_delete_markup(message=call.message)

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    if not await check_spotter_data():
        return

    item_number: str = spotter_data.get('item_number_text', None)
    character: str = spotter_data.get('character', None)
    # character_id: str = call.data.split('_')[-1]
    character_id = correct_data

    violations_dataframe = await get_violations_df(item_number, hse_user_id)
    if not await check_dataframe(violations_dataframe, hse_user_id):
        return

    await update_column_value(
        hse_user_id, character, character_id, item_number, violations_dataframe
    )

    # violations_file_path: str = ''
    #
    # violations_files_list: list = await get_json_file_list(chat_id)
    # if not violations_files_list:
    #     logger.warning(Messages.Error.file_list_not_found)
    #     await bot_send_message(chat_id=chat_id, text=Messages.Error.file_list_not_found)
    #     return
    #
    # violations_id = board_config.current_file.split(' ')[0]
    #
    # for file in violations_files_list:
    #     if file.split('\\')[-1].split(SEPARATOR)[-1].replace('.json', '') == violations_id:
    #         violations_file_path = file
    #         break
    #
    # if not violations_file_path:
    #     logger.warning(f'{Messages.Error.file_not_found} violations_id: {violations_id}')
    #     await bot_send_message(chat_id=chat_id, text=f'{Messages.Error.file_not_found} violations_id: {violations_id}')
    #     return
    #
    # violation_data: dict = await read_json_file(file=violations_file_path)
    #
    # violation_data[state_name] = correct_data
    #
    # await write_json_file(data=violation_data, name=violation_data["json_full_name"])
    #
    # await update_user_violation_data_on_google_drive(chat_id=chat_id, violation_data=violation_data, notify_user=True)
    #
    # if violation_data:
    #     violation_text = await get_violations_text(violation_data)
    #     await bot_send_message(chat_id=chat_id, text=violation_text)
    #
    # await bot_send_message(chat_id=chat_id, text=Messages.Successfully.correct_violations_completed,
    #                        reply_markup=ReplyKeyboardRemove())


# async def test():
#     """Test text_meaning_handler"""
#
#     hse_user_id = 373084462
#     character = 'description'
#     item_number = '10593'
#     violations_dataframe = None
#
#     await text_meaning_handler(hse_user_id, character, item_number, violations_dataframe)
#
#
# if __name__ == '__main__':
#     asyncio.run(test())
