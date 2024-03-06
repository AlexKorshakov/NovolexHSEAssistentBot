from loader import logger

logger.debug(f"{__name__} start import")
import asyncio

from aiogram import types
from aiogram.dispatcher import FSMContext
from apps.core.bot.messages.messages import Messages
from apps.core.database.db_utils import db_get_data_dict_from_table_with_id
from apps.core.database.entry_in_db import write_data_in_database
# from apps.core.utils.goolgedrive_processor.GoogleDriveUtils.set_user_violation_data_on_google_drave import \
#     write_violation_data_on_google_drive
from apps.core.utils.json_worker.writer_json_file import write_json_violation_user_file
from apps.MyBot import bot_send_message

logger.debug(f"{__name__} finish import")


async def pre_set_violation_data(message: types.Message, state: FSMContext, user_id: str = None):
    """Интерфейс записи нарушения на Google Drive

    """
    try:
        hse_user_id = message.chat.id if message else user_id

    except AttributeError as err:
        logger.debug(f'{__file__} {repr(err)}')
        hse_user_id = user_id if user_id else message.from_user.id

    v_data: dict = await state.get_data()

    await set_violation_data(chat_id=hse_user_id, v_data=v_data)


async def set_violation_data(*, chat_id: str, v_data: dict):
    """Запись и сохранение данных в local storage, database, Google Drive
    """
    logger.debug(f'{chat_id = } {v_data = }')

    result_write_json = await write_json_violation_user_file(data=v_data)
    if result_write_json:
        logger.info(f"Данные сохранены в local storage {v_data.get('json_full_name')}")

    # result_google: bool = await write_violation_data_on_google_drive(chat_id=chat_id, violation_data=v_data)
    # if result_google:
    #     logger.info(f"Данные сохранены в Google Drive в директорию \n"
    #                 f"https://drive.google.com/drive/folders/{v_data.get('json_folder_id')}")

    result_database: bool = await write_data_in_database(violation_data_to_db=v_data)
    if result_database:
        logger.info(Messages.Report.completed_successfully)
        await bot_send_message(chat_id=chat_id, text=Messages.Report.completed_successfully)
    else:
        await bot_send_message(chat_id=chat_id, text=Messages.Error.entry_in_bd_fail)

    await bot_send_message(chat_id=chat_id, text=Messages.help_message)


async def test():
    """

    :return:
    """
    violation_data: dict = {
        "act_required": "Требуется*",
        "category": "Отходы",
        "comment": "Убрать мусор строительный",
        "data": "30:11:2022",
        "day": "30",
        "day_of_year": "334",
        "description": "Захламление строительным мусором",
        "elimination_time": "3 дня",
        "file_id": "30.11.2022___862629360___29431",
        "function": "специалист",
        "general_contractor": "ООО Ренейссанс Хэви Индастрис",
        "hse_id": 2,
        "incident_level": "Без последствий",
        "json_file_path": "C:\\Users\\KDeusEx\\PycharmProjects\\SWTS\\application\\media\\862629360\\data_file\\30.11.2022\\json\\",
        "json_full_name": "C:\\Users\\KDeusEx\\PycharmProjects\\SWTS\\application\\media\\862629360\\data_file\\30.11.2022\\json\\report_data___30.11.2022___862629360___29431.json",
        "location": "ПО - 1",
        "main_category": "Экология",
        "main_location": "ТК",
        "month": "11",
        "name": "Гарифуллин Ильгиз Рамилевич",
        "normative_documents": "Захламление территории производства работ строительным отходами",
        "normative_documents_normative": "Приказ №883н от 11 декабря 2020 года «Об утверждении Правил по охране труда при строительстве, реконструкции и ремонте» п. 41",
        "normative_documents_procedure": "Привести в соответствие с требованиями НД",
        "now": "2022-11-30 11:17:01.702504",
        "parent_id": None,
        "photo_file_path": "C:\\Users\\KDeusEx\\PycharmProjects\\SWTS\\application\\media\\862629360\\data_file\\30.11.2022\\photo\\",
        "photo_full_name": "C:\\Users\\KDeusEx\\PycharmProjects\\SWTS\\application\\media\\862629360\\data_file\\30.11.2022\\photo\\report_data___30.11.2022___862629360___29431.jpg",
        "quarter": "04",
        "status": "В работе",
        "sub_location": "4.0.6. Корпус обогащения",
        "user_fullname": "Ильгиз Гарифуллин",
        "user_id": 862629360,
        "violation_category": "Опасная ситуация*",
        "violation_id": 29431,
        "week": "48",
        "work_shift": "Дневная смена",
        "year": "2022"
    }

    location = await db_get_data_dict_from_table_with_id(
        table_name='core_location',
        post_id=2
    )
    location = location['title']
    print(f'{location = }')

    if not await write_data_in_database(violation_data_to_db=violation_data):
        print('ERROR violation_data write in db')
        return

    print('violation_data written in db')


if __name__ == "__main__":
    asyncio.run(test())
