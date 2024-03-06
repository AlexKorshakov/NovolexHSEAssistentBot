import os.path
from openpyxl.drawing.image import Image
from xlsxwriter.worksheet import Worksheet

from apps.core.utils.json_worker.read_json_file import read_json_file
from apps.core.utils.secondary_functions.get_filepath import get_directory_name, get_image_name
from apps.core.utils.secondary_functions.get_json_files import get_files
from config.config import Novolex_media_path
from loader import logger

COLUMN_STR_INDEX: str = 'O'
SIGNALLINE_COLUMN_STR_INDEX: str = "B"

IMG_ANCHOR = True
IMG_SCALE = True


async def insert_images_to_sheet(json_data: list, worksheet: Worksheet, height: int = 160):
    """Вставка изображения в лист worksheet
    """
    for ind, j_data in enumerate(json_data, start=2):
        try:
            img_data = await read_json_file(j_data)

            img: Image = Image(img_data['photo_full_name'])

            if img is None:
                logger.error(f"Изображение для вставки в строку {ind} не найдено!")
                continue

            img_params: dict = {
                "height": height,
                "scale": IMG_SCALE,
                "anchor": IMG_ANCHOR,
                "column": COLUMN_STR_INDEX,
                "row": ind
            }

            img = await image_preparation(img, img_params)

            await insert_images(worksheet, img=img)

        except Exception as err:
            logger.error(f"insert_img {repr(err)}")
            return None


async def insert_signalline_to_report_body(worksheet: Worksheet) -> bool:
    """
    :param worksheet:
    :return:
    """
    photo_full_name: str = "signalline.jpeg"

    files: list = await get_files(
        directory=await get_directory_name(Novolex_media_path, 'HSE', "!service_img"),
        endswith=".jpg"
    )

    for file in files:
        photo_full_name: str = file if file.split(os.sep)[-1].split('.')[0] == "signalline" else ''

    if not os.path.isfile(photo_full_name):
        logger.error("signalline not found")
        return False

    img: Image = Image(photo_full_name)

    img_params: dict = {
        "anchor": IMG_ANCHOR,
        "column": SIGNALLINE_COLUMN_STR_INDEX,
        "row": 4
    }

    img: Image = await image_preparation(img, img_params)

    await insert_images(worksheet, img=img)

    return True


async def insert_service_image(worksheet: Worksheet, *, chat_id: int = None, service_image_name: str = 'Logo',
                               img_params: dict = None) -> bool:
    """Вставка изображений в файл

    :param service_image_name: str - имя файла для обработки
    :param chat_id: int - id пользователя (папки) где находится logo
    :param img_params: dict параметры вставки
    :param worksheet:
    :return: bool
    """

    photo_full_name: str = await get_image_name(Novolex_media_path, "HSE", str(chat_id), f"{service_image_name}.jpg")

    # if chat_id:
    #     photo_full_name: str = await get_image_name(Novolex_media_path, "HSE",
    #     str(chat_id), f"{service_image_name}.jpg")

    if not os.path.isfile(photo_full_name):
        logger.error("service image not found")
        photo_full_name: str = await get_image_name(Novolex_media_path, "HSE", str(chat_id), "Logo.jpg")

    if not img_params:
        img_params: dict = {
            'photo_full_name': photo_full_name,
            "height": 90,
            "width": 230,
            "anchor": True,
            "column": 'B',
            "column_img": 2,
            "row": 2,
        }

    if not os.path.isfile(photo_full_name):
        logger.error("service image not found")
        return False

    img: Image = Image(photo_full_name)

    img = await image_preparation(img, img_params)

    result = await insert_images(worksheet, img=img)
    if result:
        return True
    return False


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
