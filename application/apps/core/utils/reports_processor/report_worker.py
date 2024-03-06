from pprint import pprint

from apps.core.bot.messages.messages import Messages
from apps.core.database.db_utils import db_get_data_dict_from_table_with_id
from apps.core.utils.data_recording_processor.set_user_report_data import \
    set_report_data
from apps.core.bot.handlers.generate.generate_report import \
    create_report_from_other_method
from apps.core.bot.handlers.generate.generate_report import get_data_report
from apps.core.bot.handlers.generate.generate_report.get_file_list import get_json_file_list
from apps.core.bot.handlers.generate.generate_report.get_report_path import \
    get_full_report_name
from apps.core.bot.handlers.generate.generate_report.send_report_from_user import \
    send_report_from_user
from apps.MyBot import bot_send_message
from loader import logger


async def create_and_send_report(chat_id:int):
    """Формирование и отправка отчета

    :param chat_id:
    :return:
    """

    file_list = await get_json_file_list(chat_id=chat_id)
    if not file_list:
        logger.warning(Messages.Error.file_list_not_found)
        await bot_send_message(chat_id=chat_id, text=Messages.Error.file_list_not_found)

    report_dataframe = await get_data_report(chat_id=chat_id, file_list=file_list)
    if report_dataframe.empty:
        logger.warning(Messages.Error.dataframe_not_found)
        await bot_send_message(chat_id=chat_id, text=Messages.Error.dataframe_not_found)

    full_report_path = await get_full_report_name(chat_id=chat_id)
    await create_report_from_other_method(chat_id=chat_id,
                                          full_report_path=full_report_path,
                                          file_list=file_list)

    await bot_send_message(chat_id=chat_id, text=f'{Messages.Report.done} \n')

    await set_report_data(chat_id=chat_id, full_report_path=full_report_path)

    await send_report_from_user(chat_id=chat_id, full_report_path=full_report_path)

    return True


async def test():
    general_constractor = await db_get_data_dict_from_table_with_id(
        table_name='core_generalcontractor',
        post_id=2)

    pprint(general_constractor)
    return general_constractor


if __name__ == '__main__':
    chat_id = 862629360

    # if '2022-10-30' == datetime.now().strftime("%Y-%m-%d"):
    #     print(f'data is true')
    #
    # asyncio.create_qr_code(generate_and_send_act_prescription(
    #     chat_id=chat_id,
    #     query_act_date_period='2022-12-01'
    # ))
    # asyncio.create_qr_code(test())
