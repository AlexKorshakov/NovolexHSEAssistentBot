from loader import logger

logger.debug(f"{__name__} start import")
from aiogram import types
from aiogram.types import ReplyKeyboardRemove
from apps.core.bot.messages.messages import Messages
from apps.core.database.entry_in_db import write_data_in_database
# from apps.core.utils.goolgedrive_processor.GoogleDriveUtils.set_user_registration_data_on_google_drave import \
#     write_user_registration_data_on_google_drive
from apps.core.utils.json_worker.writer_json_file import write_user_registration_data_on_json_on_local_storage
from apps.core.utils.secondary_functions.get_filepath import preparation_registration_paths_on_pc
from apps.MyBot import bot_send_message

logger.debug(f"{__name__} finish import")


async def registration_data(message: types.Message, user_data):
    """

    :param message:
    :param user_data:
    :return:
    """
    user_id = message.from_user.id

    user_data = await preparation_registration_paths_on_pc(user_id=user_id, user_data=user_data)

    chat_id = message.chat.id
    await bot_send_message(chat_id=chat_id, text=Messages.Registration.user_registration)

    await set_user_registration_data(chat_id=chat_id, user_data=user_data)

    await bot_send_message(chat_id=chat_id, text=Messages.Successfully.registration_completed)
    await bot_send_message(chat_id=chat_id, text=Messages.help_message, reply_markup=ReplyKeyboardRemove())


async def set_user_registration_data(*, chat_id, user_data):
    """Запись и сохранение данных в local storage, database, Google Drive

     :param: chat_id: id пользователя
     :param: user_data: данные для записи
     """

    user_data = await preparation_registration_paths_on_pc(user_id=chat_id, user_data=user_data)

    if await write_user_registration_data_on_json_on_local_storage(user_data=user_data):
        logger.info(f"Данные сохранены в local storage в файл {user_data['reg_user_file']}")

    if await write_data_in_database(violation_data_to_db=user_data):
        logger.info(f"Данные сохранены в database в файл {user_data['reg_user_file']}")

    # if await write_user_registration_data_on_google_drive(chat_id=chat_id, user_data=user_data):
    #     logger.info(f"Данные сохранены в Google Drive в файл {user_data['reg_user_file']} \n"
    #                 f"https://drive.google.com/drive/folders/{user_data['parent_id']}")
