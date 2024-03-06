from __future__ import annotations

import os
from itertools import chain

from aiogram import types
from aiogram.dispatcher import FSMContext

from apps.MyBot import bot_send_message, MyBot
from apps.core.bot.handlers.photo.qr_act_nom_processing import qr_act_nom_processing
# from apps.core.bot.handlers.photo.qr_matrix_nom_processing import qr_matrix_nom_processing
# from apps.core.bot.handlers.photo.qr_personal_id_processing import qr_personal_id_processing
from apps.core.bot.handlers.photo.qr_support_paths import qr_get_file_path, qr_check_or_create_dir
from apps.core.bot.handlers.photo.qr_worker import qr_code_reader, read_qr_code_image
from apps.core.bot.messages.messages import Messages
from apps.core.bot.messages.messages_test import msg
from apps.core.bot.reports.report_data import QRData
from apps.core.settyngs import get_sett
from config.config import Novolex_media_path


@MyBot.dp.callback_query_handler(lambda call: call.data[0] == '#', state=QRData.all_states)
async def qr_code_processing(message: types.Message, state: FSMContext, context: dict = None) -> bool:
    """Функция распознавания qr-кодов

    """

    hse_user_id: str = str(message.chat.id)

    if not get_sett(cat='enable_features', param='use_qr_code_processing').get_set():
        msg_text: str = await msg(hse_user_id, cat='error', msge='features_disabled',
                                  default=Messages.Error.features_disabled).g_mas()
        await bot_send_message(chat_id=hse_user_id, text=msg_text, disable_web_page_preview=True)
        return False

    photo_file_path: str = await qr_get_file_path(Novolex_media_path, 'temp_qr_code', hse_user_id, 'photos')
    await qr_check_or_create_dir(file_path=photo_file_path)

    destination_file_path: str = await qr_get_file_path(photo_file_path, f'{hse_user_id}.jpg')

    await message.bot.send_chat_action(message.chat.id, 'upload_photo')
    result = await message.photo[-1].download(make_dirs=False, destination_file=destination_file_path)

    img = read_qr_code_image(destination_file_path)
    data: list = await qr_code_reader(hse_user_id, img)

    if not data:
        answer_text: str = await msg(
                hse_user_id, cat='warning', msge='qr_not_found', default="QR-код, не распознан или отсутствует").g_mas()

        await bot_send_message(chat_id=hse_user_id, text=answer_text)
        return False

    if not isinstance(data, list):
        return False

    # qr_dat = [item for item in list(chain(*data)) if 'qr_matrix_nom_' in item]
    # if qr_dat:
    #     await qr_matrix_nom_processing(hse_user_id, qr_data=data, state=state)
    #     return True

    qr_dat = [item for item in list(chain(*data)) if 'qr_act_nom_' in item]
    if qr_dat:
        await qr_act_nom_processing(hse_user_id, data=data)
        return True

    # qr_dat = [item for item in list(chain(*data)) if 'personal_id_code_' in item]
    # if qr_dat:
    #     await qr_personal_id_processing(hse_user_id, data=data, message=message)
    #     return True

    # qr_dat = [item for item in list(chain(*data)) if 'personal_id_code_' in item]
    # if qr_dat:
    #     await qr_personal_id_processing(hse_user_id, data=data, message=message)
    #     return True

    try:
        os.remove(destination_file_path)
    except PermissionError:
        pass

    return False
