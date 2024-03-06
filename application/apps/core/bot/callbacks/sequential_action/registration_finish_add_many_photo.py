from __future__ import annotations

import asyncio
import datetime
import os
from pathlib import Path

from aiogram import types
from aiogram.dispatcher import FSMContext

from apps.MyBot import MyBot, bot_send_message
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.bot_utils.progress_bar import ProgressBar
from apps.core.bot.callbacks.sequential_action.data_answer import notify_user_for_choice
from apps.core.bot.callbacks.sequential_action.registration_finist_keybord import registration_finish_keyboard_inline
from apps.core.bot.filters.custom_filters import filter_is_private
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages import Messages
from apps.core.bot.messages.messages_test import msg
from apps.core.bot.reports.report_data import ViolationData
from apps.core.bot.reports.report_data_preparation import set_violation_atr_data
from apps.core.settyngs import get_sett
from config.config import Novolex_media_path, REPORT_NAME, SEPARATOR
from loader import logger


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['registration_finish_add_many_photo']),
                                 state='*')
async def call_registration_finish_add_many_photo(call: types.CallbackQuery = None, callback_data: dict = None,
                                                  user_id: int | str = None, state: FSMContext = None):
    """Обработка ответов содержащихся в call_registration_finish_add_coordinate
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {call.data = }')

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    if not get_sett(cat='enable_features', param='use_registration_finish_add_many_photo').get_set():
        msg_text: str = f"{await msg(hse_user_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=hse_user_id, text=msg_text, disable_web_page_preview=True)
        return

    await notify_user_for_choice(call, data_answer=call.data)

    await ViolationData.add_many_photo.set()
    await bot_send_message(
        chat_id=hse_user_id, text="Загрузите фотографии из галереи",
        disable_web_page_preview=True
    )

    v_data: dict = await state.get_data()
    if v_data.get("comment"):
        reply_markup = await registration_finish_keyboard_inline()
        await bot_send_message(chat_id=hse_user_id, text=Messages.Registration.confirm, reply_markup=reply_markup)


@MyBot.dp.message_handler(filter_is_private, content_types=types.ContentType.ANY, state=ViolationData.add_many_photo)
async def handler_albums(message: types.Message, album: list[types.Message] = None, callback_data: dict = None,
                         user_id: int | str = None, state: FSMContext = None):
    """This handler will receive a complete album of any type
    """

    hse_user_id = message.chat.id if message else user_id
    v_data: dict = await state.get_data()
    media_group: list = []
    num: int = 0

    if not album:
        await state.update_data(media_group=media_group)
        v_data.get('media_group', [])

        file_name = await get_filename_msg_with_photo(message=message, main_message_id=v_data.get('violation_id', ''))
        photo_full_name = await get_photo_full_filename(user_id=hse_user_id, file_name=file_name)

        try:
            await message.photo[-1].download(destination_file=photo_full_name)
            num = +1
            media_group.append({'media': file_name})

        except asyncio.exceptions.TimeoutError as err:
            logger.debug(f'download_photo: {hse_user_id = } {photo_full_name = } {repr(err)}')
            return False

        await state.update_data(media_group=media_group)
        await state.finish()

        reply_markup = await registration_finish_keyboard_inline()
        await bot_send_message(
            chat_id=hse_user_id, text=f'{Messages.Registration.successful} {num}', reply_markup=reply_markup
        )
        return

    p_bar = ProgressBar(chat=hse_user_id)
    await p_bar.start(chat=hse_user_id)

    for num, mess in enumerate(album, start=1):
        await p_bar.update_msg(num)

        if not mess.photo:
            continue

        file_name = await get_filename_msg_with_photo(message=mess, main_message_id=v_data.get('violation_id', ''))
        photo_full_name = await get_photo_full_filename(user_id=hse_user_id, file_name=file_name)

        try:
            await mess.photo[-1].download(destination_file=photo_full_name)
            media_group.append({'media': file_name})

        except asyncio.exceptions.TimeoutError as err:
            logger.debug(f'download_photo: {hse_user_id = } {photo_full_name = } {repr(err)}')
            continue

    await state.update_data(media_group=media_group)
    await set_violation_atr_data("media_group", media_group, state=state)

    await p_bar.finish()
    # await state.finish()

    reply_markup = await registration_finish_keyboard_inline()
    await bot_send_message(
        chat_id=hse_user_id, text=f'{Messages.Registration.successful} {num}', reply_markup=reply_markup
    )


async def registration_finish_keyboard_inline_test():
    """Формирование индентфикатора записи
    """
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            text='Добавить фотографии к нарушению',
            callback_data=posts_cb.new(id='-', action='registration_finish_add_many_photo')
        )
    )
    return markup


async def get_filename_msg_with_photo(message, main_message_id):
    """Формирование индентфикатора записи
    """
    day: str = await get_day_message()
    month: str = await get_month_message()
    year: str = await get_year_message()
    from_id: str = str(message.values['from'].id)
    message_id: str = str(message.message_id)

    filename = f'{day}.{month}.{year}{SEPARATOR}{from_id}{SEPARATOR}{main_message_id}{SEPARATOR}{message_id}'

    logger.info(f"filename {filename}")
    return filename


async def get_photo_full_filename(user_id: str = None, file_name: str=None, date: str = None):
    """Обработчик сообщений с photo. Получение полного пути файла
    """
    if not date:
        date: str = await date_now()

    photo_full_name: Path = Path(Novolex_media_path, "HSE", str(user_id), 'data_file', date, 'photo')

    try:
        os.makedirs(photo_full_name)

    except FileExistsError as err:
        logger.debug(f'get_photo_full_filename: {user_id = } {photo_full_name = } {repr(err)}')

    return str(Path(photo_full_name, f"dop_{REPORT_NAME}{file_name}.jpg"))


async def date_now() -> str:
    """Возвращает текущую дату в формате дд.мм.гггг
    """
    return str((datetime.datetime.now()).strftime("%d.%m.%Y"))


async def get_day_message(current_date: datetime | str = None) -> str:
    """Обработчик сообщений с фото
    Получение номер str дня из сообщения в формате dd
    """
    current_date: datetime.date = await str_to_datetime(current_date)

    if not current_date:
        current_date: datetime = datetime.datetime.now()
    return str("0" + str(current_date.day) if current_date.day < 10 else str(current_date.day))


async def get_month_message(current_date: datetime | str = None) -> str:
    """Получение номер str месяца из сообщения в формате mm
    """
    current_date: datetime.date = await str_to_datetime(current_date)

    if not current_date:
        current_date: datetime = datetime.datetime.now()
    return str("0" + str(current_date.month) if int(current_date.month) < 10 else str(current_date.month))


async def get_year_message(current_date: datetime | str = None) -> str:
    """Обработчик сообщений с фото. Получение полного пути файла
    """
    current_date: datetime.date = await str_to_datetime(current_date)

    if not current_date:
        current_date: datetime = datetime.datetime.now()

    return str(current_date.year)


async def str_to_datetime(date_str: str) -> datetime.date:
    """Преобразование str даты в datetime
    :param
    """
    current_date = datetime.datetime.now()

    if not date_str:
        return current_date

    if isinstance(date_str, str):
        current_date: datetime.date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
        return current_date

    return current_date


async def test():
    hse_user_id = '373084462'

    reply_markup = await registration_finish_keyboard_inline_test()
    await bot_send_message(chat_id=hse_user_id, text=Messages.Registration.confirm, reply_markup=reply_markup)


if __name__ == '__main__':
    asyncio.run(test())
