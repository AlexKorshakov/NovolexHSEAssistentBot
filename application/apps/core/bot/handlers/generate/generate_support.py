from __future__ import annotations

import datetime
from datetime import datetime

from apps.MyBot import bot_send_message
from apps.core.bot.handlers.generate.generate_support_paths import (create_file_path,
                                                                    get_report_full_filepath,
                                                                    get_report_full_name,
                                                                    )
from apps.core.bot.messages.messages import Messages

from config.config import WRITE_DATA_ON_GOOGLE_DRIVE
from loader import logger


async def get_and_create_full_act_prescription_name(chat_id: int, param: dict) -> str:
    """Формирование и получение полного имение пути к акту

    :param param:
    :param chat_id:
    :return:
    """
    if not param:
        return ''

    act_number = param.get('act_number', None)
    if not act_number:
        act_number = (datetime.datetime.now()).strftime("%d.%m.%Y")

    act_date = param.get('act_date', None)
    if not act_date:
        act_date = (datetime.datetime.now()).strftime("%d.%m.%Y")

    short_title = param.get('short_title', None)
    if not short_title:
        short_title = ''

    main_location = param.get('main_location', None)
    if not main_location:
        main_location = ''

    try:
        report_full_name = f'Акт-предписание № {act_number} от {act_date} {short_title} {main_location}.xlsx'
        report_path = await get_report_full_filepath(str(chat_id), actual_date=act_date)

        await create_file_path(report_path)
        full_report_path: str = await get_report_full_name(report_path, report_full_name)

        return full_report_path

    except Exception as err:
        logger.error(f"get_report_path {repr(err)}")
        return ''


async def set_report_data(chat_id: int, full_report_path: str):
    """Загрузка файла отчета на google drive

    :param chat_id: id чата
    :param full_report_path: полный путь до файла с данными
    """

    await set_user_report_data(chat_id=chat_id, full_report_path=full_report_path)
    await bot_send_message(chat_id=chat_id, text=Messages.Successfully.registration_completed)


async def set_user_report_data(chat_id: int, full_report_path: str):
    """Сoхранение данных отчета различными методами

    :param chat_id: id чата
    :param full_report_path: полный путь до файла с данными
    """
    if not full_report_path:
        await bot_send_message(chat_id=chat_id, text=Messages.Error.fill_report_path_not_found)
        logger.info(Messages.Error.fill_report_path_not_found)
        return

    if not WRITE_DATA_ON_GOOGLE_DRIVE:
        logger.info(f'{WRITE_DATA_ON_GOOGLE_DRIVE = } abort upload / download from Google Drive')
        return False

    # if await set_user_report_data_on_google_drive(chat_id=chat_id, full_report_path=full_report_path):
    #     logger.info(Messages.Successfully.save_data_on_g_drive)


async def set_act_data_on_google_drive(chat_id: int, full_report_path: str):
    """Сoхранение данных отчета различными методами

    :param chat_id: id чата
    :param full_report_path: полный путь до файла с данными
    """

    if not WRITE_DATA_ON_GOOGLE_DRIVE:
        logger.info(f'{WRITE_DATA_ON_GOOGLE_DRIVE = } abort upload / download from Google Drive')
        return False

    if not full_report_path:
        await bot_send_message(chat_id=chat_id, text=Messages.Error.fill_report_path_not_found)
        logger.info(Messages.Error.fill_report_path_not_found)
        return

    # if await set_user_report_data_on_google_drive(chat_id=chat_id, full_report_path=full_report_path):
    #     logger.info(Messages.Successfully.save_data_on_g_drive)
    return


async def set_json_act_prescription_in_registry(full_patch: str, json_name: str, json_data) -> bool:
    """

    :param json_data:
    :param json_name:
    :param full_patch:
    :return:
    """
    with open(f'{full_patch}\\{json_name}', 'w') as json_file:
        json_file.write(json_data)

    return True

# async def test():
#     chat_id = '373084462'
#     constractor_id = 2
#
#     now = datetime.datetime.now()
#     previous = now - datetime.timedelta(days=1)
#     query_act_date_period: list = [previous.strftime("%d.%m.%Y"), now.strftime("%d.%m.%Y"), ]
#
#     clean_headers: list = await db_get_clean_headers(table_name='core_violations')
#
#     act_dataframe: DataFrame = await get_act_dataframe(
#         chat_id=chat_id, act_period=query_act_date_period, constractor_id=constractor_id, headers=clean_headers
#     )
#     if act_dataframe.empty:
#         return
#
#     hse_chat_id = '373084462'
#     act_number = '1151'
#     path_in_registry = '/media/registry/ООО Удоканская Медь/2023/04/Акт-предписание № 1151 от 30.04.2023 ООО РХИ'
#     act_date = '24.04.2023'
#
#     await set_act_prescription_json(
#         hse_chat_id, act_dataframe, act_number, path_in_registry, constractor_id, act_date
#     )
#
#     if __name__ == '__main__':
#         asyncio.run(test())
