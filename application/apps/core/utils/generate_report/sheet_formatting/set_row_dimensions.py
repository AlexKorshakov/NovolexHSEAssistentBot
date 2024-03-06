from openpyxl.worksheet.worksheet import Worksheet

from apps.core.database.db_utils import db_get_data_dict_from_table_with_id
from loader import logger


async def set_row_dimensions(worksheet: Worksheet, row_number: int or str, height: int):
    """Установление высоты строки

    :param worksheet:
    :param row_number:
    :param height:
    :return:
    """
    try:
        worksheet.row_dimensions[int(row_number)].height = float(height)
    except Exception as err:
        logger.error(f"set_row_dimensions {repr(err)}")


async def set_automatic_row_dimensions(worksheet: Worksheet, row_number: int, row_value) -> bool:
    """Автоматическое установление высоты строки по тексту

    :param row_value:
    :param worksheet:
    :param row_number:
    :return:
    """

    if not row_value:
        return False

    normative_documents: dict = await db_get_data_dict_from_table_with_id(
        table_name='core_normativedocuments',
        post_id=row_value.normative_documents_id)

    title = normative_documents.get('title', None)
    normative = normative_documents.get('normative', None)
    procedure = normative_documents.get('procedure', None)
    comment = row_value.comment

    if not normative:
        logger.error(f"No normative found if {row_value =  }")
    if not procedure:
        logger.error(f"No procedure found if {row_value =  }")

    if procedure:
        comment = row_value.comment if len(row_value.comment) < len(procedure) else procedure

    item_list: list = []
    try:
        list_val = [row_value.description, title, normative, comment]
        for item in list_val:
            if not isinstance(item, str): continue

            lines = min(len(item.split("\n\n")) - 1, 1)
            height = max(len(item) / 26 + lines, 1.5) * 16
            item_list.append(height)

        max_height = round(max(item_list), 2) + 10

        if max_height <= 60:
            max_height = 60

        dim = worksheet.row_dimensions[row_number]
        dim.height = max_height

        logger.debug(f"row_number {row_number} max_height {max_height}")
        return True

    except Exception as err:
        logger.error(f"Error row {row_number} set_automatic_row_dimensions {repr(err)}")
        return False
