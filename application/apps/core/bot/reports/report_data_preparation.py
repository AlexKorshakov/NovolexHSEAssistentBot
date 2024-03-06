from __future__ import annotations

import asyncio

from apps.core.utils.json_worker.read_json_file import read_json_file
from loader import logger

logger.debug(f"{__name__} start import")

from aiogram import types
from aiogram.dispatcher import FSMContext
from apps.core.bot.reports.report_data import ViolationData
from apps.core.utils.json_worker.writer_json_file import (write_json_file,
                                                          write_json_violation_user_file)
from apps.core.utils.secondary_functions.get_filename import get_filename_msg_with_photo
from apps.core.utils.secondary_functions.get_filepath import (create_file_path,
                                                              get_json_full_filename,
                                                              get_json_full_filepath,
                                                              get_photo_full_filename,
                                                              get_photo_full_filepath)

logger.debug(f"{__name__} finish import")


async def download_photo(message: types.Message, user_id: str = None):
    """Подготовка данных предписания. первичное заполнение violation_data

    :return:
    """

    hse_user_id = message.chat.id if message else user_id

    photo_file_path = await get_photo_full_filepath(user_id=hse_user_id)
    await create_file_path(photo_file_path)

    file_id = await get_filename_msg_with_photo(message=message)
    photo_full_name = await get_photo_full_filename(user_id=hse_user_id, name=file_id)

    try:
        await message.photo[-1].download(destination_file=photo_full_name)
        return True

    except asyncio.exceptions.TimeoutError as err:
        logger.debug(f'download_photo: {hse_user_id = } {photo_full_name = } {repr(err)}')
        return False


async def preparing_violation_data(message: types.Message, state: FSMContext, chat_id: str = None, user_id: str = None):
    """Подготовка данных предписания. первичное заполнение violation_data

    :return:
    """
    violation: dict = {}
    await state.set_state(ViolationData.starting)

    hse_user_id = message.chat.id if message else user_id

    file_id = await get_filename_msg_with_photo(message=message)
    await state.update_data(file_id=file_id)

    photo_file_path = await get_photo_full_filepath(user_id=hse_user_id)
    await create_file_path(photo_file_path)
    await state.update_data(photo_file_path=photo_file_path)

    photo_full_name = await get_photo_full_filename(user_id=hse_user_id, name=file_id)
    await state.update_data(photo_full_name=photo_full_name)

    json_file_path = await get_json_full_filepath(user_id=hse_user_id)
    await create_file_path(json_file_path)
    await state.update_data(json_file_path=json_file_path)

    json_full_name = await get_json_full_filename(user_id=hse_user_id, file_name=file_id)
    await state.update_data(json_full_name=json_full_name)

    violation[hse_user_id] = await state.get_data()
    # await write_json_violation_user_file(data=violation_data, json_full_name=json_full_name)
    await write_json_violation_user_file(data=await state.get_data(), json_full_name=json_full_name)

    await set_violation_atr_data("file_id", file_id, state=state)

    await state.update_data(user_id=chat_id)
    await set_violation_atr_data("user_id", user_id, state=state)

    await state.update_data(violation_id=message.message_id)
    await set_violation_atr_data("violation_id", message.message_id, state=state)


async def preparing_violations_paths_on_pc(message: types.Message, state: FSMContext, user_id: str = None):
    """Создание путей сохранения файлов и запись в json
    :param state:
    :param user_id:
    :param message:
    :return:
    """

    hse_user_id = message.chat.id if message else user_id

    photo_file_path = await get_photo_full_filepath(user_id=hse_user_id)
    await create_file_path(photo_file_path)

    file_id = await get_filename_msg_with_photo(message=message)
    photo_full_name = await get_photo_full_filename(user_id=hse_user_id, name=file_id)
    await message.photo[-1].download(destination_file=photo_full_name)

    photo_file_path = await get_photo_full_filepath(user_id=hse_user_id)

    await state.update_data(photo_file_path=photo_file_path)

    photo_full_name = await get_photo_full_filename(user_id=hse_user_id, name=file_id)

    await state.update_data(photo_full_name=photo_full_name)

    json_file_path = await get_json_full_filepath(user_id=hse_user_id)

    await state.update_data(json_file_path=json_file_path)

    json_full_name = await get_json_full_filename(user_id=hse_user_id, file_name=file_id)

    await state.update_data(json_full_name=json_full_name)

    await create_file_path(json_file_path)

    v_data: dict = await state.get_data()
    await write_json_violation_user_file(data=v_data)


async def preparing_violation_data_for_loading_to_google_drive(data: dict, state: FSMContext = None) -> bool:
    """Подготовка данных (id папок) на google_drive

    :rtype: dict
    """
    if not data:
        return False

    await state.update_data(json_folder_id=data.get("json_folder_id", None))

    await state.update_data(photo_folder_id=data.get("photo_folder_id", None))

    await state.update_data(report_folder_id=data.get("report_folder_id", None))

    await state.update_data(parent_id=data.get("user_folder_id", None))

    # await write_json_violation_user_file(data=violation_data)

    v_data: dict = await state.get_data()
    user_id = v_data.get('user_id')
    json_file_path = await get_json_full_filepath(user_id=user_id)
    await create_file_path(json_file_path)

    await write_json_violation_user_file(data=v_data)

    return True


async def set_violation_atr_data(atr_name: str, art_val: str | int | list, state: FSMContext = None, **kvargs) -> bool:
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

    file_id = user_dict.get("file_id", None)
    hse_user_id = state.user

    json_full_name = await get_json_full_filename(user_id=hse_user_id, file_name=file_id)

    if json_full_name is None: return False
    if not json_full_name: return False

    # violation_data[atr_name] = art_val
    # await write_json_file(data=violation_data, json_full_name=violation_data["json_full_name"])
    if atr_name not in ['media_group', ]:
        await state.update_data({atr_name: art_val})

        await write_json_file(data=user_dict, name=json_full_name)
        return True

    read_dict: dict = await read_json_file(file=json_full_name)

    if not read_dict.get('media_group'):
        read_dict.update({'media_group': art_val})
        await state.update_data({atr_name: art_val})

    else:
        media_group: list = read_dict['media_group'] + art_val
        read_dict['media_group'] = media_group
        await state.update_data({atr_name: media_group})

    await write_json_file(data=read_dict, name=json_full_name)
    return True
