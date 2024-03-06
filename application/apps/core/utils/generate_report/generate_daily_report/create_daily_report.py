from apps.core.bot.messages.messages import Messages
from apps.core.bot.handlers.generate.generate_report.create_xlsx.create_xlsx import create_xlsx
from apps.core.bot.handlers.generate.generate_report.generate_daily_report.set_daily_report_format import (
    format_daily_report_photographic, format_daily_report_sheet_basic,
    format_daily_report_sheet_body, format_daily_report_sheet_footer,
    format_daily_report_sheet_header)
from apps.core.bot.handlers.generate.generate_report.generate_daily_report.set_daily_report_values import (
    set_mip_photographic_materials_values, set_report_header_values,
    set_report_headlines_data_values, set_report_values_body,
    set_report_values_footer, set_report_values_header,
    set_report_violation_values)
from apps.core.bot.handlers.generate.generate_report.set_value import \
    set_photographic_materials
from apps.core.bot.handlers.generate.generate_report.sheet_formatting.set_page_setup import \
    set_row_breaks
from apps.core.utils.img_processor.insert_img import (
    insert_signalline_to_report_body)
from apps.core.utils.reports_processor.report_worker_utils import \
    get_clean_headers
from apps.MyBot import bot_send_message
from loader import logger
from pandas import DataFrame


async def create_daily_report(chat_id: int, dataframe: DataFrame = None, full_daily_report_report_path: str = None,
                              violation_data_list: list = None):
    """Создание отчета xls из данных dataframe

    """

    if not full_daily_report_report_path:
        logger.error(Messages.Error.fill_report_path_not_found)
        return

    workbook, worksheet = await create_xlsx(chat_id, full_daily_report_report_path)
    if not worksheet:
        return False

    await format_daily_report_sheet_basic(worksheet)
    workbook.save(full_daily_report_report_path)

    await set_report_values_header(worksheet)
    await format_daily_report_sheet_header(worksheet)
    workbook.save(full_daily_report_report_path)

    _, num, body_val_list = await set_report_values_body(worksheet)
    await format_daily_report_sheet_body(worksheet, workbook, full_daily_report_report_path, num)
    workbook.save(full_daily_report_report_path)

    _, num = await set_report_values_footer(worksheet, workbook, full_daily_report_report_path, num)
    _, num = await format_daily_report_sheet_footer(worksheet, workbook, full_daily_report_report_path, num)
    workbook.save(full_daily_report_report_path)

    # await insert_service_image(worksheet)
    await set_row_breaks(worksheet, row=num)
    workbook.save(full_daily_report_report_path)

    await set_report_headlines_data_values(chat_id=chat_id, dataframe=dataframe)
    workbook.save(full_daily_report_report_path)

    await set_report_header_values(worksheet, dataframe)
    workbook.save(full_daily_report_report_path)

    try:
        await set_report_violation_values(
            worksheet, dataframe, num, body_val_list, workbook, full_daily_report_report_path
        )
    except Exception as err:
        await bot_send_message(chat_id=chat_id, text=f'Messages.Error.file_not_found {err} ')
        logger.error(f'create_act_prescription: set_report_violation_values error: {repr(err)}')
        return False

    await insert_signalline_to_report_body(worksheet)
    workbook.save(full_daily_report_report_path)

    if violation_data_list is None:
        violation_data_list: list = []

        clean_headers: list = await get_clean_headers(table_name='core_violations')

        for num_data, violation_data in enumerate(dataframe.itertuples(index=False), start=1):
            violation_dict: dict = dict(zip(clean_headers, violation_data))
            violation_data_list.append(violation_dict)

    if violation_data_list:
        _, num = await set_mip_photographic_materials_values(worksheet, num)
        workbook.save(full_daily_report_report_path)
        await format_daily_report_photographic(worksheet, num)
        workbook.save(full_daily_report_report_path)
        num_data: int = 0
        for v_data in violation_data_list:
            is_add = await set_photographic_materials(worksheet, v_data, num_data, num)
            if is_add:
                num_data += 1

    workbook.save(full_daily_report_report_path)

    return True
