import datetime
from math import ceil

from apps.core.bot.reports.report_data import headlines_data
from apps.core.database.db_utils import (db_get_categories,
                                         db_get_data_dict_from_table_with_id,
                                         db_get_data_list,
                                         db_get_dict_userdata,
                                         db_get_elimination_time)
from apps.core.database.query_constructor import QueryConstructor
from apps.core.bot.handlers.generate.generate_report.generate_daily_report.set_daily_report_alignment import \
    set_report_alignment
from apps.core.bot.handlers.generate.generate_report.set_value import (check_mark_true,
                                                                       not_found)
from apps.core.bot.handlers.generate.generate_report.sheet_formatting.set_font import \
    sets_report_font
from loader import logger
from pandas import DataFrame
from xlsxwriter.workbook import Workbook
from xlsxwriter.worksheet import Worksheet


async def set_report_violation_values(
        worksheet: Worksheet, dataframe: DataFrame, num: int = None, body_val_list: list = None,
        workbook: Workbook = None, full_daily_report_report_path: str = None) -> bool:
    """Заполнение акта значениями из dataframe

    :param workbook:
    :param full_daily_report_report_path:
    :param body_val_list:
    :param num:
    :param worksheet: страница для заполнения
    :param dataframe: dataframe с данными нарушений
    :return: bool
    """
    serial_number: int = 0
    violation_value: list = []

    clean_categories = await db_get_categories()

    for category in clean_categories:

        violation_value = await get_violation_value(dataframe, category)

        if not violation_value:
            continue

        serial_number += 1
        for body_val_item in body_val_list:

            if category != body_val_item.get('value'):
                continue

            await set_worksheet_cell_value(worksheet, body_val_item, serial_number, violation_value)
            workbook.save(full_daily_report_report_path)
            violation_value = []
            break

    return True


async def get_violation_value(dataframe, category) -> list:
    violation_value: list = []

    for enum, item in enumerate(range(0, dataframe.category_id.size)):
        category_data_dict: dict = await db_get_data_dict_from_table_with_id(
            table_name='core_category',
            post_id=dataframe.loc[item]["category_id"])
        category_title = category_data_dict.get('title')

        if category_title != category:
            continue

        try:
            elimination_time = await get_elimination_time(dataframe, item)
            violation_value.append(
                {"description": dataframe.loc[enum]["description"] + ' \\',
                 "elimination_time": elimination_time + ' \\'}
            )
        except Exception as err:
            logger.error(f"{repr(err)}")
            continue

    return violation_value


async def set_report_header_values(worksheet: Worksheet, dataframe: DataFrame) -> bool:
    """Заполнение заголовка отчета

    :param dataframe:
    :param worksheet: страница для заполнения
    :return:
    """

    # TODO: check dataframe general_contractor_id
    contractors = dataframe.general_contractor_id.tolist()
    contractors = list(set(list(contractors)))
    contractors_str = ''
    for item in contractors:
        if isinstance(item, float):
            continue

        general_contractor_full_name: dict = await db_get_data_dict_from_table_with_id(
            table_name='core_generalcontractor',
            post_id=item)
        general_contractor_name = general_contractor_full_name.get('title', '')

        headlines_data['general_contractor_full_name'] = general_contractor_name
        gc_full_name: str = general_contractor_full_name['title']

        if gc_full_name and gc_full_name != 'Подрядная организация':
            contractors_str = contractors_str + gc_full_name + ', '
            headlines_data['contractors'] = contractors_str

    values = [
        {"coordinate": "C2", "value": f"{headlines_data.get('organization')}",
         "row": "2", "column": "3"},
        {"coordinate": "D2", "value": f"Отчет {headlines_data.get('work_shift')} {headlines_data.get('custom_date')}",
         "row": "2", "column": "4"},
        {"coordinate": "C3", "value": f"ЛО-ОТПБиООС-{headlines_data.get('year')}-{headlines_data.get('day')}",
         "row": "3", "column": "3"},
        {"coordinate": "D5", "value": f"{headlines_data.get('linear_bypass')}", "row": "5", "column": "4"},
        {"coordinate": "D6", "value": f"{headlines_data.get('custom_date')}", "row": "6", "column": "4"},

        {"coordinate": "D7", "value": f"{headlines_data.get('contractors')}", "row": "7", "column": "4"},

        {"coordinate": "D8", "value": "", "row": "8", "column": "4"},
        {"coordinate": "D9", "value": f"{headlines_data.get('name_location')}", "row": "9", "column": "4"},
        {"coordinate": "F12", "value": f"{headlines_data.get('construction_manager')}", "row": "12", "column": "6"},

        {"coordinate": "E13", "value": f"{headlines_data.get('function')}", "row": "13", "column": "5"},
        {"coordinate": "E13", "value": f"{headlines_data.get('name')} тел. +{headlines_data.get('phone_number')}",
         "row": "13", "column": "6"},

        {"coordinate": "F14", "value": f"{headlines_data.get('building_control_engineer')}", "row": "14",
         "column": "6"},
        {"coordinate": "F15", "value": f"{headlines_data.get('contractor_representative')}", "row": "15",
         "column": "6"},
        {"coordinate": "F16", "value": f"{headlines_data.get('subcontractor_representative')}", "row": "16",
         "column": "6"},
    ]

    for val in values:
        try:
            worksheet.cell(row=int(val['row']), column=int(val['column']), value=str(val['value']))
        except Exception as err:
            logger.error(f"set_user_values {repr(err)}")
            return False
    return True


async def set_report_values_header(worksheet: Worksheet) -> bool:
    """Заполнение первоначальных данных отчета

    :param worksheet: страница для заполнения
    :return:
    """
    values = [
        {"coordinate": "C2", "value": "НАЗВАНИЕ ОРГАНИЗАЦИИ", "row": "2", "column": "3"},
        # {"coordinate": "D2", "value": "Отчет о ночной смены", "row": "2", "column": "4"},
        {"coordinate": "C3", "value": "ЛО-ОТПБиПТ--", "row": "3", "column": "3"},
        {"coordinate": "D3", "value": "Значение", "row": "3", "column": "4"},
        {"coordinate": "F3", "value": "Примечание", "row": "3", "column": "6"},
        {"coordinate": "C4", "value": "Общая информация", "row": "4", "column": "3"},
        {"coordinate": "C5", "value": "Обход", "row": "5", "column": "3"},
        # {"coordinate": "D5", "value": "Первичный", "row": "5", "column": "4"},
        {"coordinate": "C6", "value": "Дата", "row": "6", "column": "3"},
        {"coordinate": "C7", "value": "Подрядчик", "row": "7", "column": "3"},
        # {"coordinate": "D7", "value": "стм.", "row": "7", "column": "4"},
        {"coordinate": "C8", "value": "Субподрядчик", "row": "8", "column": "3"},
        {"coordinate": "C9", "value": "Проект", "row": "9", "column": "3"},
        # {"coordinate": "D9", "value": "", "row": "9", "column": "4"},
        {"coordinate": "C10", "value": "Комиссия", "row": "10", "column": "3"},
        {"coordinate": "D10", "value": "Функция", "row": "10", "column": "4"},
        {"coordinate": "F10", "value": "ФИО", "row": "10", "column": "6"},
        {"coordinate": "D11", "value": "□", "row": "11", "column": "4"},
        {"coordinate": "E11", "value": "Инспектирующие", "row": "11", "column": "5"},
        {"coordinate": "D12", "value": f"{check_mark_true}", "row": "12", "column": "4"},
        {"coordinate": "E12", "value": "Руководитель строительства", "row": "12", "column": "5"},
        # {"coordinate": "F12", "value": f"{be_away}", "row": "12", "column": "6"},
        {"coordinate": "D13", "value": f"{check_mark_true}", "row": "13", "column": "4"},
        {"coordinate": "E13", "value": "Специалист отдела ПБ", "row": "13", "column": "5"},
        {"coordinate": "D14", "value": f"{check_mark_true}", "row": "14", "column": "4"},
        {"coordinate": "E14", "value": "Инженер СК", "row": "14", "column": "5"},
        # {"coordinate": "F14", "value": f"{be_away}", "row": "14", "column": "6"},
        {"coordinate": "D15", "value": f"{check_mark_true}", "row": "15", "column": "4"},
        {"coordinate": "E15", "value": "Подрядчик", "row": "15", "column": "5"},
        # {"coordinate": "F15", "value": f"{be_away}", "row": "15", "column": "6"},
        {"coordinate": "D16", "value": f"{check_mark_true}", "row": "16", "column": "4"},
        {"coordinate": "E16", "value": "Субподрядчик", "row": "16", "column": "5"},
        {"coordinate": "C17", "value": "Охрана труда, промышленная безопасность и охрана окружающей среды", "row": "17",
         "column": "3"},
        {"coordinate": "C18", "value": "Наблюдения", "row": "18", "column": "3"},
        {"coordinate": "D18", "value": "Категория несоответствия", "row": "18", "column": "4"},
        {"coordinate": "F18", "value": "№", "row": "18", "column": "6"},
        {"coordinate": "G18", "value": "Несоответствие", "row": "18", "column": "7"},
        {"coordinate": "H18", "value": "Срок", "row": "18", "column": "8"},
    ]

    for val in values:
        try:
            worksheet.cell(row=int(val['row']), column=int(val['column'])).value = str(val['value'])

            if val["value"] == not_found:
                cell_range = [f"D{val['row']}:H{val['row']}",
                              {"color": "008000", "font_size": "14", "name": "Arial"}]
                await sets_report_font(worksheet, cell_range[0], params=cell_range[1])

        except Exception as err:
            logger.error(f"set_values {repr(err)}")
            return False
    return True


async def set_report_values_body(worksheet: Worksheet) -> tuple[bool, int, list]:
    """Заполнение первоначальных данных отчета

    :param worksheet: страница для заполнения
    :return:
    """
    values: list = []
    num: int = 0

    query_kwargs: dict = {
        "action": 'SELECT', "subject": 'title',
    }
    query: str = await QueryConstructor(None, 'core_category', **query_kwargs).prepare_data()

    categories: list = await db_get_data_list(query=query)
    clean_title_categories = [item[0] for item in categories]

    for num, category in enumerate(clean_title_categories, start=19):
        values.append({"coordinate": f"D{num}", "value": f"{check_mark_true}", "row": f"{num}", "column": "4"})
        values.append({"coordinate": f"E{num}", "value": f"{category}", "row": f"{num}", "column": "5"})
        values.append({"coordinate": f"G{num}", "value": f"{not_found}", "row": f"{num}", "column": "7"})

    for val in values:
        try:
            worksheet.cell(row=int(val['row']), column=int(val['column'])).value = str(val['value'])

            if val["value"] == not_found:
                cell_range = [f"D{val['row']}:H{val['row']}",
                              {"color": "008000", "font_size": "14", "name": "Arial"}]
                await sets_report_font(worksheet, cell_range[0], params=cell_range[1])

        except Exception as err:
            logger.error(f"set_values {repr(err)}")
            return False, num, values
    return True, num, values


async def set_report_values_footer(worksheet: Worksheet, workbook,
                                   full_daily_report_report_path, num) -> tuple[bool, int]:
    """Заполнение первоначальных данных отчета

    :param num:
    :param full_daily_report_report_path:
    :param workbook:
    :param worksheet: страница для заполнения
    :return:
    """

    values = [
        {"coordinate": f"C{num + 1}", "value": "Дополнительная информация", "row": f"{num + 1}", "column": "3"},
        {"coordinate": f"C{num + 2}",
         "value": 'Данное сообщение рассылается Дирекцией по охране труда, промышленной безопасности и охране '
                  'окружающей среды  с целью информирования о состоянии площадки, производства и '
                  'документирования строительно-монтажных работ',
         "row": f"{num + 2}", "column": "3"}
    ]

    for val in values:
        try:
            worksheet.cell(row=int(val['row']), column=int(val['column'])).value = str(val['value'])

            if val["value"] == not_found:
                cell_range = [f"D{val['row']}:H{val['row']}",
                              {"color": "008000", "font_size": "14", "name": "Arial"}]
                await sets_report_font(worksheet, cell_range[0], params=cell_range[1])

        except Exception as err:
            logger.error(f"set_values {repr(err)}")
            return False, num

    workbook.save(full_daily_report_report_path)
    return True, num


async def set_report_headlines_data_values(chat_id: int, dataframe=None) -> bool:
    """Формирование заголовков отчета

    :param dataframe:
    :param chat_id: id пользователя для которого заполняется отчет
    :return:
    """

    be_away: str = 'отсутствовал'

    if not headlines_data:
        # Руководитель строительства
        headlines_data['construction_manager'] = be_away
        # Инженер СК
        headlines_data['building_control_engineer'] = be_away
        # Подрядчик
        headlines_data['general_contractor'] = ''
        # Подрядчики
        headlines_data['contractors'] = ''
        # Субподрядчик
        headlines_data['subcontractor'] = ''
        # Проект
        headlines_data['name_location'] = ''
        # Вид обхода
        headlines_data['linear_bypass'] = 'Первичный'
        # Дата
        headlines_data['date_linear_bypass'] = ''
        # Представитель подрядчика
        headlines_data['contractor_representative'] = be_away
        # Представитель субподрядчика
        headlines_data['subcontractor_representative'] = be_away

    headlines_data["day"] = (datetime.datetime.now()).strftime("%d")
    headlines_data["year"] = (datetime.datetime.now()).strftime("%Y")

    registration_data: dict = await db_get_dict_userdata(chat_id)

    organization_full_name: dict = await db_get_data_dict_from_table_with_id(
        table_name='core_generalcontractor',
        post_id=registration_data.get("hse_organization", ''))
    organization_name = organization_full_name.get('title', '')

    headlines_data['organization'] = organization_name

    headlines_data['function'] = registration_data.get("hse_function", '')
    headlines_data['name'] = registration_data.get("hse_short_name", '')

    location_list = []
    if not dataframe.empty:

        location = dataframe.location_id.tolist()
        location = list(set(list(location)))

        for item in location:
            if isinstance(item, float):
                continue

            location_full_name: dict = await db_get_data_dict_from_table_with_id(
                table_name='core_location',
                post_id=item)
            location_list.append(location_full_name.get('title', ''))

        headlines_data['name_location'] = ''.join(location_list)

    if not location_list:
        location_dict: dict = await db_get_data_dict_from_table_with_id(
            table_name='core_location',
            post_id=registration_data.get("hse_location", '')
        )
        location = location_dict.get('title', '')
        headlines_data['name_location'] = location

    headlines_data['phone_number'] = registration_data.get("hse_contact_main_phone_number", '')

    headlines_data['HSE_email'] = registration_data.get("hse_contact_main_email", '')

    work_shift_dict: dict = await db_get_data_dict_from_table_with_id(
        table_name='core_workshift',
        post_id=registration_data.get("hse_work_shift", '')
    )
    work_shift = work_shift_dict.get('title', '')

    headlines_data['work_shift'] = work_shift

    date_now = datetime.datetime.now().strftime("%d.%m.%Y")
    date_then = datetime.datetime.now() - datetime.timedelta(days=1)
    date_then = date_then.strftime("%d.%m.%Y")

    if headlines_data.get("work_shift", '').lower() == "дневная смена":
        headlines_data['work_shift'] = 'дневной смены'
        headlines_data['custom_date'] = f"{date_now}"
    else:
        headlines_data['work_shift'] = 'о ночной смене'
        headlines_data['custom_date'] = f"{date_then} - {date_now}"

    return True


async def set_worksheet_cell_value(worksheet: Worksheet, item: dict, serial_number: int, val: list):
    """

    :param val:
    :param worksheet: страница для заполнения
    :param item:
    :param serial_number:
    :return:
    """
    worksheet.cell(row=int(item['row']), column=6, value=serial_number)
    worksheet.cell(row=int(item['row']), column=7, value="".join([str(i["description"]) + ' \n' for i in val]))
    worksheet.cell(row=int(item['row']), column=8, value="".join([str(i["elimination_time"]) + ' \n' for i in val]))

    cell_ranges = [
        [f"D{item['row']}:F{item['row']}", {"color": "FF0000", "font_size": "14", "name": "Arial"}],
        [f"G{item['row']}:G{item['row']}", {"color": "FF0000", "font_size": "12", "name": "Arial"}],
        [f"H{item['row']}:H{item['row']}", {"color": "FF0000", "font_size": "12", "name": "Arial"}],
    ]
    for cell_range in cell_ranges:
        await sets_report_font(worksheet, cell_range[0], params=cell_range[1])
        await set_report_alignment(worksheet, cell_range[0], horizontal='left', vertical='center')

    worksheet.row_dimensions[int(item['row'])].height = await get_height_for_row(
        worksheet,
        int(item['row']),
        value="".join([str(i["description"]) + ' \n' for i in val]))


async def get_elimination_time(dataframe: DataFrame, item: int) -> str:
    """Получить время устранения

    :return: str
    """
    elimination_time_id = dataframe.loc[item]["elimination_time_id"]
    elimination_time_dict: dict = await db_get_data_dict_from_table_with_id(
        table_name='core_eliminationtime',
        post_id=elimination_time_id
    )
    elimination_time_title = elimination_time_dict.get('title', None)
    elimination_time_days = int(elimination_time_dict.get('days', None))

    elimination_time_title_list = await db_get_elimination_time()

    if elimination_time_title != elimination_time_title_list[0] and \
            elimination_time_title != elimination_time_title_list[1]:
        elimination_time = datetime.datetime.now() + datetime.timedelta(days=elimination_time_days)

        return str(elimination_time.strftime("%d.%m.%Y"))

    return str(elimination_time_days)


async def get_height_for_row(sheet: Worksheet, row_number: int, font_size: int = 12, value=None):
    """Изменение высоты строк в зависимости от содержания

    :param value:
    :param sheet:
    :param row_number:
    :param font_size:
    :return:
    """

    factor_of_font_size_to_width = {
        12: {"factor": 0.9,  # width / count of symbols at row
             "height": 25}
    }

    font_params = factor_of_font_size_to_width[font_size]
    row = list(sheet.rows)[row_number]
    height = font_params["height"]

    for index, cell in enumerate(row):
        if index != 6:
            continue

        if hasattr(cell, 'column_letter'):
            words_count_at_one_row = sheet.column_dimensions[cell.column_letter].width / font_params["factor"]

            lines = ceil(len(str(value)) / words_count_at_one_row)
            height = max(height, lines * font_params["height"])
            return height


async def set_mip_photographic_materials_values(worksheet: Worksheet, num: int = None) -> tuple[bool, int]:
    """Добавление заголовка раздела Фотоматериалы

    :param num:
    :param worksheet:
    """

    values = [
        {"coordinate": f"C{num + 4}", "value": "Фотофиксация", "row": f"{num + 4}", "column": "3"},
        {"coordinate": f"C{num + 5}", "value": "ФОТО", "row": f"{num + 5}", "column": "3"},
        {"coordinate": f"F{num + 5}", "value": "№", "row": f"{num + 5}", "column": "6"},
        {"coordinate": f"C{num + 5}", "value": "Примечание", f"row": f"{num + 5}", "column": "7"},
    ]

    for val in values:
        try:
            worksheet.cell(row=int(val['row']), column=int(val['column']), value=str(val['value']))
        except Exception as err:
            logger.error(f"set_photographic_materials_values {repr(err)}")
            continue

    return True, num + 4
