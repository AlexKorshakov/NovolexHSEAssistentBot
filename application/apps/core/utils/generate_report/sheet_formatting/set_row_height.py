from loader import logger

MAXIMUM_ROW_HEIGHT: int = 120


async def set_row_height(worksheet):
    """Форматирование ячейки: высота шрифта
    """
    for ind in range(worksheet.max_row):
        if ind == 0:
            continue
        try:
            worksheet.row_dimensions[ind + 1].height = MAXIMUM_ROW_HEIGHT
        except Exception as err:
            logger.error(F"set_row_height {repr(err)}")