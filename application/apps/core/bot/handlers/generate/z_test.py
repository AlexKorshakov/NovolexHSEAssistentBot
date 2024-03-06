import datetime
import os

import asyncio
from pathlib import Path
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.worksheet.pagebreak import Break
from openpyxl.drawing.image import Image

from pandas import DataFrame

from apps.core.bot.handlers.generate.generate_act_prescription_support import create_xlsx
from apps.core.bot.handlers.generate.generate_support_paths import get_full_act_prescription_path
from apps.core.database.db_utils import db_get_clean_headers, db_get_data_list
from apps.core.database.query_constructor import QueryConstructor
from apps.core.utils.generate_report.generate_act_prescription.set_act_format_ import set_row_dimensions

from config.config import Novolex_media_path
from loader import logger


async def anchor_dop_photo(chat_id, dataframe: DataFrame, start_row_number: int, workbook: Workbook,
                           worksheet: Worksheet, full_act_path: str):
    """Добавление дополнительных фотоматериалов"""

    img_params: list = await get_img_params(
        user_id=chat_id, dataframe=dataframe, start_row_num=start_row_number
    )

    photo_row: int = start_row_number
    for photo_num, img_param in enumerate(img_params, start=1):
        try:
            await set_act_photographic_materials(worksheet, img_param)
            await set_row_dimensions(worksheet, row_number=img_param['row'], height=242)

            await set_act_photographic_materials_description(worksheet, img_param)
            photo_row: int = img_param.get('row')
            workbook.save(full_act_path)

        except Exception as err:
            logger.error(f"set_act_photographic_materials {photo_num= } {repr(err)} ")
            continue

    print_area = f'$A$1:M{photo_row + 1}'

    return print_area, photo_row + 1


async def get_img_params(user_id: str, dataframe: DataFrame, start_row_num: int) -> list:
    """

    :return:
    """
    group_photo_list: list = await get_group_photo_list(user_id=user_id, dataframe=dataframe)
    photo_row: int = start_row_num

    img_params_list: list = []
    for num_data, media_file_dict in enumerate(group_photo_list, start=1):
        img_params: dict = {"height": 320, "anchor": True, "scale": True, "row_header": photo_row - 1,
                            "row_description": photo_row,
                            'photo_full_name': media_file_dict.get('photo_full_name', None),
                            "description": media_file_dict.get('description', None)}

        if num_data % 2 != 0:
            img_params["column"] = 'B'
            img_params["column_img"] = 2
            # img_params["column_description"] = 6
            img_params["row"] = photo_row

            if num_data != 1:
                # img_params["row_header"] = photo_row - 1
                img_params["row_description"] = img_params["row_description"] + 2
        else:
            img_params["column"] = 'H'
            img_params["column_img"] = 8
            # img_params["column_description"] = 12
            # img_params["row_header"] = photo_row - 1
            img_params["row"] = photo_row
            photo_row += 2

        img_params_list.append(img_params)

    return img_params_list


async def get_group_photo_list(user_id: str, dataframe: DataFrame) -> list:
    """

    :return:
    """
    clean_headers: list = await db_get_clean_headers(table_name='core_violations')

    group_list: list = []
    for violation_num, violation_data in enumerate(dataframe.itertuples(index=False), start=1):
        violation_dict: dict = dict(zip(clean_headers, violation_data))
        if not violation_dict.get('media_group', None): continue
        media_group_list: list = violation_dict.get('media_group', None).split(':::')

        for num_in_group, item in enumerate(media_group_list, start=1):
            photo_full_name: str = await get_dop_photo_full_filename(user_id=user_id, name=item)

            if not os.path.isfile(photo_full_name):
                continue

            group_list.append(
                {
                    'description': f'Доп.фото №{num_in_group} к нарушению №{violation_num}',
                    'photo_full_name': photo_full_name,
                }
            )
    return group_list


async def set_act_photographic_materials(worksheet: Worksheet, img_params: dict) -> bool:
    """Вставка фото нарушения на страницу акта

    :param img_params:
    :param worksheet:
    :return:
    """

    if not img_params:
        logger.error(f'set_act_photographic_materials not found dict img_params {img_params = }')
        return False

    photo_full_name = img_params.get("photo_full_name", None)
    if not photo_full_name:
        logger.error(
            f'set_act_photographic_materials not found param img_params["photo_full_name"] {photo_full_name = }')
        return False

    if not os.path.isfile(photo_full_name):
        logger.error(f'set_act_photographic_materials photo not found {photo_full_name}')
        return False

    img: Image = Image(photo_full_name)
    img = await image_preparation(img, img_params)
    await insert_images(worksheet, img=img)

    return True


async def set_act_photographic_materials_description(worksheet, img_params):
    # set header
    worksheet.cell(
        row=img_params["row_header"], column=img_params["column_img"], value=img_params["description"]
    )
    # # set description
    # worksheet.cell(
    #     row=img_params["row_description"], column=img_params["column_description"],
    #     value=img_params["description"]
    # )


async def image_preparation(img: Image, img_params: dict):
    """Подготовка изображения перед вставкой на страницу
    """

    height = img_params.get("height")
    scale = img_params.get("scale")
    width = img_params.get("width")
    anchor = img_params.get("anchor")
    column = img_params.get("column")
    row = img_params.get("row")

    # высота изображения
    if height:
        img.height = height

    # ширина изображения
    if width:
        img.width = width

    # изменение пропорций изображения
    if scale:
        scale = img.height / max(img.height, img.width)
        img.width = img.width * scale

    # прикрепление изображение по адресу str(column) + str(row)
    if anchor:
        img.anchor = str(column) + str(row)

    return img


async def insert_images(worksheet: Worksheet, img: Image) -> bool:
    """Вставка изображения на лист worksheet*,
    :param img: файл изображения
    :param worksheet: Worksheet - страница документа для вставки изображения
    :return:
    """

    try:
        worksheet.add_image(img)
        return True

    except Exception as err:
        logger.error(f"insert_images {repr(err)}")
        return False


async def get_dop_photo_full_filename(user_id: str = None, name=None, date=None):
    """Получение полного пути с расширением дополнительных фото материалов"""
    if not date:
        date = await date_now()
    return str(
        Path(Novolex_media_path, "HSE", str(user_id), 'data_file', date, 'photo', f"dop_report_data___{name}.jpg"))


async def date_now() -> str:
    """Возвращает текущую дату в формате дд.мм.гггг
    :return:
    """
    return str((datetime.datetime.now()).strftime("%d.%m.%Y"))


async def set_act_page_after_footer_setup(worksheet: Worksheet, print_area: str, break_line: int = None) -> bool:
    """Установка параметров страницы

    :param break_line: int
    :param print_area: str
    :param worksheet: Worksheet
    :return: bool
    """

    #  https://xlsxons.horizontalCentered = True
    worksheet.print_area = print_area

    #  масштабный коэффициент для распечатываемой страницы
    # worksheet.set_print_scale(75)

    if break_line:
        worksheet.row_breaks.append(Break(id=break_line))
        # worksheet.col_breaks.append(Break(id=13))

    return True


async def format_data_db(date_item: str):
    """ Форматирование даты в формат даты БВ
    """
    return datetime.datetime.strptime(date_item, "%d.%m.%Y").strftime("%Y-%m-%d")


async def test():
    chat_id = '373084462'
    act_number = '111'
    constractor_id = '2'

    full_act_prescription_path: str = await get_full_act_prescription_path(
        chat_id=chat_id, act_number=act_number, act_date=await date_now(), constractor_id=constractor_id
    )

    workbook, worksheet = await create_xlsx(chat_id=chat_id, full_act_path=full_act_prescription_path)
    if not worksheet:
        return False

    now = datetime.datetime.now()
    act_period: list = [now.strftime("%d.%m.%Y"), now.strftime("%d.%m.%Y"), ]

    clean_headers: list = await db_get_clean_headers(table_name='core_violations')

    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "general_contractor_id": constractor_id,
            'user_id': chat_id,
            'period': [await format_data_db(act_period[0]), await format_data_db(act_period[1])]
        },
    }
    query: str = await QueryConstructor(None, 'core_violations', **query_kwargs).prepare_data()
    item_datas_query: list = await db_get_data_list(query=query)
    dataframe: DataFrame = DataFrame(item_datas_query, columns=clean_headers)

    start_row_number = 10
    await anchor_dop_photo(chat_id, dataframe, start_row_number, workbook, worksheet, full_act_prescription_path)


if __name__ == '__main__':
    asyncio.run(test())
