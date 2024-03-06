from loader import logger


async def set_column_dimensions(worksheet, column, width):
    """Форматирование: ширина столбцов

    :param worksheet:
    :param column:
    :param width:
    :return:
    """
    try:
        worksheet.column_dimensions[column].width = width
    except Exception as err:
        logger.error(f"set_column_widths {repr(err)}")
