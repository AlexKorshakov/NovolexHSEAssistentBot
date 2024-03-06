from loader import logger
from xlsxwriter.worksheet import Worksheet


async def set_merge_cells(worksheet: Worksheet, merged_cell: str) -> bool:
    """Форматирование: обьединение ячеек

    :param worksheet:
    :param merged_cell:
    :return:
    """
    try:
        worksheet.merge_cells(merged_cell)
        return True
    except Exception as err:
        logger.error(f"set_merge_cells {repr(err)}")
        return False
