from __future__ import annotations

import io
import json
import asyncio
import traceback
from aiogram import types
from datetime import datetime
from aiogram.dispatcher import FSMContext

from apps.core.bot.handlers.group.group_write_data import write_data_in_database
from loader import logger
from apps.MyBot import MyBot
from apps.core.bot.handlers.group.group_support_path import (create_file_path,
                                                             text_get_file_path)
from config.config import Novolex_media_path, SEPARATOR


async def data_text_reader(message: types.Message, user_id: str | int = None, chat_id: str | int = None,
                           text_message: str | None = None) -> list:
    user_id = user_id if user_id else message.from_user.id
    chat_id = chat_id if chat_id else message.chat.id

    if not text_message:
        return []
    if not isinstance(text_message, str):
        return []

    text_message = text_message.replace('\n', ' ')
    message_list: list = text_message.split(' ')
    message_list: list = [item for item in message_list if item]

    logger.info(f"{__name__} {await fanc_name()} start_text_mes_id {chat_id=} {user_id=} {message_list}")
    return [item.lower() for item in message_list if (item and isinstance(item, str))]


async def processing_text_violation(message: types.Message, *, album: list[types.Message] = None,
                                    user_id: str | int = None, chat_id: str | int = None,
                                    state: FSMContext = None, ):
    """

    :return:
    """
    user_id = user_id if user_id else message.from_user.id
    chat_id = chat_id if chat_id else message.chat.id

    violation_data_dict: dict = await preparing_violation_data(
        message=message, album=album, state=state, user_id=user_id, chat_id=chat_id
    )
    logger.info(f"{__name__} {await fanc_name()} {chat_id=} {user_id=} {violation_data_dict= }")
    result: bool = await write_data_in_database(violation_data_to_db=violation_data_dict)
    logger.info(f"{__name__} {await fanc_name()} {chat_id=} {user_id=} {result= }")
    return result


async def processing_data_text_work(message: types.Message, *, album: list[types.Message] = None,
                                    user_id: str | int = None, chat_id: str | int = None,
                                    state: FSMContext = None, ):
    """

    :return:
    """
    user_id = user_id if user_id else message.from_user.id
    chat_id = chat_id if chat_id else message.chat.id

    violation_data_dict: dict = await preparing_violation_data(
        message=message, album=album, state=state, user_id=user_id, chat_id=chat_id
    )
    result: bool = await write_data_in_database(violation_data_to_db=violation_data_dict)
    logger.info(f"{__name__} {await fanc_name()} {chat_id=} {user_id=} {result= }")
    return result


async def preparing_violation_data(message: types.Message, album: list[types.Message] = None, state: FSMContext = None,
                                   chat_id: str = None, user_id: str = None) -> dict:
    """Подготовка данных предписания. первичное заполнение violation_data
    :return:dict
    """
    state = state if state else MyBot.dp.current_state(user=user_id)

    chat_id = chat_id if chat_id else message.chat.id
    user_id = message.from_user.id

    user_name = message.from_user.username if message.from_user.username else ''
    first_name = message.from_user.first_name if message.from_user.first_name else ''

    file_id = message.message_id
    await state.update_data(file_id=file_id)

    chat_name: str = message.chat.title
    await state.update_data(chat_name=chat_name)

    date: str = f'{str(message.date.day).zfill(2)}.{str(message.date.month).zfill(2)}.{message.date.year}'
    await state.update_data(date=date)

    media_group_id: str = message.media_group_id if message.media_group_id else ''

    group_report_name: str = f'group_report_data___{chat_id}___{date}___{user_id}__{media_group_id}__{file_id}'
    await state.update_data(report_name=group_report_name)

    json_file_path = await get_json_full_filepath(
        chat_name=chat_name, date=date
    )
    await create_file_path(json_file_path)
    await state.update_data(json_file_path=json_file_path)

    json_full_name: str = await get_json_full_filename(
        chat_name=chat_name, file_id=file_id, report_name=group_report_name, date=date
    )
    await state.update_data(json_full_name=json_full_name)

    photo: list = message.photo[-1] if len(message.photo) > 0 else []
    text: str = message.caption
    description: str = message.caption

    created_at = await date_now()

    time_server: str = f'{str(message.date.hour).zfill(2)}:' \
                       f'{str(message.date.minute).zfill(2)}:' \
                       f'{str(message.date.second).zfill(2)}'
    await state.update_data(time_server=time_server)

    await set_violation_atr_data("date", date, state=state)
    await set_violation_atr_data("file_id", file_id, state=state)
    await set_violation_atr_data("user_id", user_id, state=state)
    await set_violation_atr_data("violation_id", message.message_id, state=state)
    await set_violation_atr_data("chat_id", chat_id, state=state)
    await set_violation_atr_data("chat_name", chat_name, state=state)
    # await set_violation_atr_data("photo", photo, state=state)
    await set_violation_atr_data("media_group_id", media_group_id, state=state)
    await set_violation_atr_data("text", text, state=state)
    await set_violation_atr_data("description", description, state=state)
    await set_violation_atr_data("created_at", created_at, state=state)
    await set_violation_atr_data("user_name", user_name, state=state)
    await set_violation_atr_data("first_name", first_name, state=state)

    media_group: list = []
    if album:
        for _, mess in enumerate(album, start=1):
            if not mess.photo: continue

            filename = await get_filename_msg_with_photo(message=mess, group_report_name=group_report_name)
            photo_full_name = await get_photo_full_filename(
                chat_name=chat_name, filename=filename
            )
            try:
                await mess.photo[-1].download(destination_file=photo_full_name)
                media_group.append({'media': filename})

            except asyncio.exceptions.TimeoutError as err:
                logger.debug(f'download_photo:{chat_id = } {user_id = } {photo_full_name = } {repr(err)}')
                continue

    if not album and message.photo:
        filename = await get_filename_msg_with_photo(message=message, group_report_name=group_report_name)
        photo_full_name = await get_photo_full_filename(
            chat_name=chat_name, filename=filename
        )
        try:
            await message.photo[-1].download(destination_file=photo_full_name)
            media_group.append({'media': filename})

        except asyncio.exceptions.TimeoutError as err:
            logger.debug(f'download_photo: {chat_id = } {user_id = } {photo_full_name = } {repr(err)}')

    await set_violation_atr_data("media_group", media_group, state=state)

    await write_json_violation_user_file(data=await state.get_data(), json_full_name=json_full_name)
    return await state.get_data()


async def set_violation_atr_data(atr_name: str, art_val: str | int | list, state: FSMContext = None) -> bool:
    """Запись данных  атрибута 'atr_name': art_val глобального словаря violation_data в файл json

    :param state:
    :param atr_name: str имя ключа
    :param art_val: str|int значение ключа
    :return: bool True если успешно.
    """
    logger.debug(f'set_violation_atr_data: {atr_name = } {art_val = }')
    if not atr_name:
        return False

    user_dict: dict = await state.get_data()
    date = user_dict.get("date", None)
    file_id = user_dict.get("file_id", None)
    chat_name = user_dict.get("chat_name", None)
    report_name = user_dict.get("report_name", None)

    json_full_name: str = await get_json_full_filename(
        chat_name=chat_name, file_id=file_id, report_name=report_name, date=date
    )
    if json_full_name is None: return False
    if not json_full_name: return False

    if atr_name not in ['media_group', ]:
        await state.update_data({atr_name: art_val})
        await write_json_file(data=user_dict, name=json_full_name)
        return True

    read_dict: dict = await read_json_file(file=json_full_name)
    if not read_dict:
        return False

    if not read_dict.get('media_group'):
        read_dict.update({'media_group': art_val})
        await state.update_data({atr_name: art_val})

    else:
        media_group: list = read_dict['media_group'] + art_val
        read_dict['media_group'] = media_group
        await state.update_data({atr_name: media_group})

    await write_json_file(data=read_dict, name=json_full_name)
    return True


async def get_filename_msg_with_photo(message, group_report_name):
    """Формирование индентфикатора записи
    """
    message_id: str = str(message.message_id)
    filename = f'{group_report_name}{SEPARATOR}{message_id}'
    logger.info(f"filename {filename}")
    return filename


async def get_photo_full_filename(chat_name: str = None, filename: str = None, date: str = None):
    """Обработчик сообщений с photo. Получение полного пути файла
    """
    if not date:
        date = await date_now()

    photo_full_filepath = await get_photo_full_filepath(chat_name, date)
    await create_file_path(photo_full_filepath)
    return await text_get_file_path(photo_full_filepath, f"dop___{filename}.jpg")


async def get_json_full_filename(chat_name: str = None, file_id: str = None, report_name=None, date: str = None):
    """Обработчик сообщений с json
    Получение полного пути файла
    """
    if not date:
        date = await date_now()

    json_full_filepath = await get_json_full_filepath(chat_name, date)
    await create_file_path(json_full_filepath)
    return await text_get_file_path(json_full_filepath, f"{report_name}___{file_id}.json")


async def get_json_full_filepath(chat_name: str = None, date: str = None):
    """Обработчик сообщений с json
    Получение полного пути файла
    """
    if not date:
        date = await date_now()

    return await text_get_file_path(Novolex_media_path, "BAGRATION", 'group', str(chat_name), date, 'json')


async def get_photo_full_filepath(chat_name: str = None, date: str = None):
    """Обработчик сообщений с json
    Получение полного пути файла
    """
    if not date:
        date = await date_now()

    return await text_get_file_path(Novolex_media_path, "BAGRATION", 'group', str(chat_name), date, 'photo')


async def write_json_violation_user_file(*, data: dict = None, json_full_name: str = None) -> bool:
    """Запись данных о нарушениях в json

    :param json_full_name: полный путь для записи / сохранения файла включая расширение,
    :param data: данные для записи / сохранения
    :return: True or False
    """
    if not json_full_name:
        json_full_name = str(data.get("json_full_name"))

    if not json_full_name:
        logger.error(f'write_json_violation_user_file error write on {json_full_name}')
        return False

    if await write_json_file(name=json_full_name, data=data):
        logger.debug(f'Data write on {json_full_name}')
        return True
    return False


async def write_json_file(name: str, data: any) -> bool:
    """Запись данных в json

    :param name: полный путь для записи / сохранения файла включая расширение,
    :param data: данные для записи / сохранения
    :return: True or False
    """
    try:
        with io.open(name, 'w', encoding='utf8') as outfile:
            str_ = json.dumps(data,
                              indent=4,
                              sort_keys=True,
                              separators=(',', ': '),
                              ensure_ascii=False)
            outfile.write(str_)
            return True
    except TypeError as err:
        logger.error(f"TypeError: {repr(err)}")
        return False


async def read_json_file(file: str):
    """Получение данных из json.

    :param file: полный путь к файлу
    """
    try:
        with open(file, 'r', encoding='utf8') as data_file:
            data_loaded = json.load(data_file)
        return data_loaded
    except FileNotFoundError:
        return None


async def date_now() -> str:
    """Возвращает текущую дату в формате дд.мм.гггг
    :return:
    """
    return str((datetime.now()).strftime("%d.%m.%Y"))


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])
