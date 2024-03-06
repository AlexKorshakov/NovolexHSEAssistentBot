
from openpyxl.worksheet.worksheet import Worksheet

from apps.core.utils.generate_report.sheet_formatting.set_alignment import set_alignment
from apps.core.utils.generate_report.sheet_formatting.set_column_widths import set_column_widths
from apps.core.utils.generate_report.sheet_formatting.set_font import set_font
from apps.core.utils.generate_report.sheet_formatting.set_frame_border import set_border
from apps.core.utils.generate_report.sheet_formatting.set_row_height import set_row_height


async def format_sheets(worksheet: Worksheet):
    """Пошаговое форматирование страницы
    """

    await set_border(worksheet)
    await set_alignment(worksheet)
    await set_font(worksheet)
    await set_column_widths(worksheet)
    await set_row_height(worksheet)


