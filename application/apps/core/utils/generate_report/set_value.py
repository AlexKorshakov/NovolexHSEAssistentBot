import os

from apps.core.bot.handlers.generate.generate_report.generate_daily_report.set_daily_report_alignment import \
    set_report_alignment
from apps.core.bot.handlers.generate.generate_report.sheet_formatting.set_font import \
    set_report_font
from apps.core.bot.handlers.generate.generate_report.sheet_formatting.set_frame_border import \
    set_range_border
from apps.core.utils.img_processor.insert_img import (image_preparation,
                                                      insert_images)
from loader import logger
from openpyxl.drawing.image import Image
from xlsxwriter.worksheet import Worksheet

not_found: str = 'не выявлено'
not_tested: str = 'не проверялось'

check_mark_true: str = 'V'
check_mark_false: str = '□'

# start_photo_row: int = 52
photo_column: str = 'C'
description_column: int = 7
photo_height: int = 400


async def set_photographic_materials(
        worksheet: Worksheet, violation_data: dict, num_data: int, num: int = None) -> bool:
    """Вставка фото и описания нарушения на страницу отчета

    :param num_data:
    :param worksheet:
    :param violation_data: 
    :return: 
    """

    # img_data = await read_json_file(violation_data)
    start_photo_row = num + 2

    if not violation_data:
        return False

    if not os.path.isfile(violation_data.get('photo_full_name')):
        logger.error("photo not found")
        return False

    merged_cells = [
        f'C{start_photo_row + num_data}:E{start_photo_row + num_data}',
        f'G{start_photo_row + num_data}:H{start_photo_row + num_data}',
    ]

    for merged_cell in merged_cells:
        worksheet.merge_cells(merged_cell)

    photographic_materials_alignment = [
        f'C{start_photo_row + num_data}:H{start_photo_row + num_data}',
    ]

    for item, cell_range in enumerate(photographic_materials_alignment, start=1):
        await set_report_alignment(worksheet, cell_range, horizontal='left', vertical='center')

    photographic_row_dimensions = [
        [f"{start_photo_row + num_data}", 300.0],
    ]

    for item in photographic_row_dimensions:
        worksheet.row_dimensions[int(item[0])].height = float(item[1])

    for item, cell_range in enumerate(photographic_materials_alignment, start=1):
        await set_report_font(worksheet, cell_range=cell_range, font_size=14)

    img: Image = Image(violation_data.get('photo_full_name'))

    img_params: dict = {
        "column": photo_column,
        "row": start_photo_row + num_data,
        "height": photo_height,
        "anchor": True,
        "scale": True,
    }

    img = await image_preparation(img, img_params)

    await insert_images(worksheet, img=img)

    if not violation_data.get('description'):
        return False

    worksheet.cell(row=start_photo_row + num_data,
                   column=description_column,
                   value=str(violation_data.get('description')))

    for item, cell_border_range in enumerate(photographic_materials_alignment, start=1):
        await set_range_border(worksheet, cell_range=cell_border_range)

    worksheet.print_area = f'$A$1:$I${start_photo_row + num_data + 1}'

    return True
