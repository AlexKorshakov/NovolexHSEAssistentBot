from loader import logger
from openpyxl.styles import Alignment


async def set_alignment(worksheet):
    """Форматирование ячейки: положение текста в ячейке (лево верх)
    """
    wrap_alignment = Alignment(wrap_text=True, horizontal='left', vertical='center')

    for row in worksheet.iter_rows():
        for cell in row:
            try:
                cell.alignment = wrap_alignment
            except Exception as err:
                logger.error(f"set_alignment {repr(err)}")


