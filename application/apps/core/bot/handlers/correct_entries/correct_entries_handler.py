import traceback
import typing

from aiogram.dispatcher import FSMContext

from apps.core.bot.filters.custom_filters import filter_is_private
from apps.core.bot.messages.messages_test import msg
from apps.core.settyngs import get_sett
from loader import logger

logger.debug(f"{__name__} start import")
import os
from mimetypes import guess_type
from pprint import pprint

from aiogram import types
from aiogram.dispatcher.filters import Command

from apps.MyBot import MyBot, bot_send_message
from config.config import WRITE_DATA_ON_GOOGLE_DRIVE

from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages import Messages
# from apps.core.utils.goolgedrive_processor.GoogleDriveUtils.find_folder import (q_request_constructor,
#                                                                                 params_constructor,
#                                                                                 find_files_by_params)
# from apps.core.utils.goolgedrive_processor.GoogleDriveUtils.folders_deleter import delete_folder
from apps.core.utils.misc import rate_limit

logger.debug(f"{__name__} finish import")


# len_description = 25


@rate_limit(limit=10)
@MyBot.dp.message_handler(Command('correct_entries'), filter_is_private, state='*')
async def correct_entries_handler(message: types.Message = None, *, hse_user_id=None, state: FSMContext = None):
    """Корректирование уже введённых значений на локальном pc и на google drive

    :return:
    """
    if message.chat.type in ['group', 'supergroup']:
        return
    # if message.from_user.id not in [member.user.id for member in await message.chat.get_administrators()]:
    #     return
    chat_id = message.chat.id if message else hse_user_id

    if not await check_user_access(chat_id=chat_id):
        logger.error(f'access fail {chat_id = }')
        return

    current_state = await state.get_state()
    await state.finish()
    logger.info(f'{await fanc_name()} state is finish {current_state = }')

    if not get_sett(cat='enable_features', param='use_correct_entries').get_set():
        msg_text: str = f"{await msg(chat_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=chat_id, text=msg_text, disable_web_page_preview=True)
        return

    reply_markup = await add_correct_inline_keyboard_with_action()
    text: str = 'Выберите действие'

    await bot_send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)


async def add_correct_inline_keyboard_with_action():
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """

    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            text='Незакрытые акты',
            callback_data=posts_cb.new(id='-', action='correct_acts'))
    )
    markup.add(
        types.InlineKeyboardButton(
            text='Незакрытые записи не в актах',
            callback_data=posts_cb.new(id='-', action='correct_non_act_item'))
    )
    return markup


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['correct_db_items']))
async def call_correct_db_items(call: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    """Обработка ответов содержащихся в ADMIN_MENU_LIST
    """
    hse_user_id = call.message.chat.id
    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    # TODO Delete
    logger.error(f'{hse_user_id = } Messages.Error.error_action')
    msg_text = await msg(hse_user_id, cat='error', msge='error_action', default=Messages.Error.error_action).g_mas()
    await bot_send_message(chat_id=hse_user_id, text=msg_text)


async def delete_violation_files_from_pc(message: types.Message, file):
    """Удаление файлов из сервера

    :param message:
    :param file:
    :return:
    """


async def del_file(path: str) -> bool:
    """Удаление файла из памяти сервера

    :param path:
    :return:
    """
    if os.path.isfile(path):
        try:
            os.remove(path)
            return True
        except os.error as err:
            logger.error(f'{Messages.Error.file_not_found} {repr(err)}')
            return False
    return False


async def delete_violation_files_from_gdrive(message, file, violation_file):
    """Удаление файлов из google drive

    :param violation_file:
    :param file:
    :param message:
    :return:
    """

    if not WRITE_DATA_ON_GOOGLE_DRIVE:
        logger.info(f'{WRITE_DATA_ON_GOOGLE_DRIVE = } abort upload / download from Google Drive')
        return False

    # drive_service = await drive_account_credentials()


async def del_file_from_gdrive(drive_service, *, name, violation_file, parent_id) -> bool:
    """Удаление файлов из google drive

    :param parent_id:
    :param violation_file:
    :param name:
    :param drive_service:
    :return:
    """

    mime_type: str = str(guess_type(violation_file)[0])
    # q = await q_request_constructor(name=name,
    #                                 parent=parent_id,
    #                                 mime_type=mime_type
    #                                 )
    # params = await params_constructor(q=q, spaces="drive")
    # v_files = await find_files_by_params(drive_service, params=params)
    # pprint(f"find_files {v_files}")
    #
    # for v in v_files:
    #     if v.get("id"):
    #         return bool(await delete_folder(service=drive_service, folder_id=v["id"]))

    return False


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])
