from apps.core.bot.messages.messages import Messages
from apps.core.bot.handlers.generate.generate_report.create_xlsx.create_xlsx import create_xlsx
from apps.core.bot.handlers.generate.generate_report.generate_stat.set_stat_format import (
    format_stat_sheet_basic, format_stat_sheet_body, format_stat_sheet_footer,
    format_stat_sheet_header)
from apps.core.bot.handlers.generate.generate_report.generate_stat.set_stat_values import (
    set_stat_header_values, set_stat_headlines_data_values,
    set_stat_values_body, set_stat_values_footer, set_stat_values_header,
    set_stat_violation_values)
from apps.core.bot.handlers.generate.generate_report.sheet_formatting.set_page_setup import \
    set_row_breaks
from apps.core.utils.img_processor.insert_img import \
    insert_signalline_to_report_body
from apps.MyBot import bot_send_message
from loader import logger
from pandas import DataFrame


async def create_stat(chat_id: int, dataframe: DataFrame = None, full_stat_path: str = None, query_period = None):
    """Создание отчета xls из данных dataframe

    """

    if not full_stat_path:
        logger.error(Messages.Error.fill_report_path_not_found)
        return

    workbook, worksheet = await create_xlsx(chat_id, full_stat_path)
    if not worksheet:
        return False

    await format_stat_sheet_basic(worksheet)
    workbook.save(full_stat_path)

    await set_stat_values_header(worksheet)
    await format_stat_sheet_header(worksheet)
    workbook.save(full_stat_path)

    _, num, body_val_list = await set_stat_values_body(worksheet)
    await format_stat_sheet_body(worksheet, workbook, full_stat_path, num)
    workbook.save(full_stat_path)

    _, num = await set_stat_values_footer(worksheet, workbook, full_stat_path, num)
    _, num = await format_stat_sheet_footer(worksheet, workbook, full_stat_path, num)
    workbook.save(full_stat_path)

    # await insert_service_image(worksheet)
    await set_row_breaks(worksheet, row=num)
    workbook.save(full_stat_path)

    await set_stat_headlines_data_values(chat_id=chat_id, dataframe=dataframe, query_period=query_period)
    workbook.save(full_stat_path)

    await set_stat_header_values(worksheet, dataframe)
    workbook.save(full_stat_path)

    try:
        await set_stat_violation_values(
            worksheet, dataframe, body_val_list, workbook, full_stat_path
        )
    except Exception as err:
        await bot_send_message(chat_id=chat_id, text=f'{Messages.Error.file_not_found} {repr(err)}')
        logger.error(f'create_act_prescription: set_stat_violation_values error: {repr(err)}')
        return False

    await insert_signalline_to_report_body(worksheet)
    workbook.save(full_stat_path)

    return True
