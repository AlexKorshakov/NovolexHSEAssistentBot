import asyncio
import datetime
import traceback

from apps.core.bot.reports.report_data import headlines_data
from apps.core.database.db_utils import (db_get_data_dict_from_table_with_id,
                                         db_get_data_list,
                                         db_get_clean_headers)
from apps.core.database.query_constructor import QueryConstructor
from loader import logger


async def get_act_headlines_data_values(chat_id, dataframe=None, act_date=None, act_number=None) -> dict:
    """ Формирование данных для формирования шапки акта - предписания

    :return: dict headlines_data
    """

    table_name: str = 'core_violations'
    clean_headers: list = await db_get_clean_headers(table_name=table_name)
    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "hse_telegram_id": chat_id,
        },
    }
    query: str = await QueryConstructor(None, 'core_hseuser', **query_kwargs).prepare_data()
    datas_query_list: list = await db_get_data_list(query=query)
    clean_datas_query_list = datas_query_list[0]

    item_dict: dict = dict(
        (header, item_value) for header, item_value in zip(clean_headers, clean_datas_query_list))

    hse_id = item_dict.get('id', None)

    if not hse_id:
        logger.error(f'hse_id is {hse_id}')
        return {}

    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "hse_telegram_id": chat_id,
        },
    }
    query: str = await QueryConstructor(None, 'core_hseuser', **query_kwargs).prepare_data()
    # print(f'{__name__} {fanc_name()} {query}')

    hse_user: dict = await db_get_data_dict_from_table_with_id(
        table_name='core_hseuser',
        post_id=hse_id,
        query=query
    )

    # ФИО выдавшего
    # headlines_data['HSE'] = list(set(list(dataframe.name)))[0]
    headlines_data['HSE'] = hse_user.get('hse_full_name', None)

    # ФИО сокращенно выдавшего
    # headlines_data['HSE_name_short'] = 'Коршаков А.С.'
    headlines_data['HSE_name_short'] = hse_user.get('hse_short_name', None)

    # ФИО и должность выдавшего в родительном
    # headlines_data['HSE_full_name_dative'] = list(set(list(dataframe.name)))[0]
    headlines_data['HSE_full_name_dative'] = hse_user.get('hse_full_name_dative', None)

    # Email выдавшего
    # headlines_data['HSE_email'] = 'as.korshakov@udokancopper.com'
    headlines_data['HSE_email'] = hse_user.get('hse_contact_main_email', None)

    # Должность выдавшего
    # headlines_data['HSE_function'] = list(set(list(dataframe.function)))[0]
    headlines_data['HSE_function'] = hse_user.get('hse_function', None)
    headlines_data['HSE_function_dative'] = hse_user.get('hse_function_dative', None)

    # Отдел выдавшего
    # headlines_data['hse_department'] = list(set(list(dataframe.function)))[0]
    headlines_data['hse_department'] = hse_user.get('hse_department', None)
    headlines_data['hse_department_dative'] = hse_user.get('hse_department_dative', None)

    headlines_data['act_number'] = act_number if act_number else 00000

    # Максимальная дата ответа
    elimination_time_id = max(dataframe['elimination_time_id'])
    elimination_time: dict = await db_get_data_dict_from_table_with_id(
        table_name='core_eliminationtime',
        post_id=elimination_time_id
    )

    max_date = max(dataframe['created_at'])
    days_max = elimination_time['days']
    headlines_data['act_date'] = datetime.datetime.strptime(max_date, '%Y-%m-%d').strftime('%d.%m.%Y')
    headlines_data['act_max_date'] = (datetime.datetime.strptime(act_date, '%d.%m.%Y') + datetime.timedelta(
        days=days_max)).strftime('%d.%m.%Y')

    # Подрядчик
    general_contractor_id = list(set(list(dataframe.general_contractor_id)))[0]
    general_contractor_dict: dict = await db_get_data_dict_from_table_with_id(
        table_name='core_generalcontractor',
        post_id=general_contractor_id)

    headlines_data['general_contractor_full_name'] = general_contractor_dict.get('title', None)
    headlines_data['general_contractor_legal_address'] = general_contractor_dict.get('legal_address', None)

    hse_organization: dict = await db_get_data_dict_from_table_with_id(
        table_name='core_generalcontractor',
        post_id=hse_user.get('hse_organization', None))

    headlines_data['hse_organization_full_name'] = hse_organization.get('title', None)
    headlines_data['hse_organization_legal_address'] = hse_organization.get('legal_address', None)

    # TODO  update general_contractor table in DB
    # Ответственное лицо подрядчика
    headlines_data['contractor_representative'] = ' '

    # Проект
    main_location_id_list: list = list(set(list(dataframe.main_location_id)))
    item_dict: dict = {}
    for main_location_id in main_location_id_list:
        main_location_name: dict = await db_get_data_dict_from_table_with_id(
            table_name='core_mainlocation',
            post_id=main_location_id)
        item_dict[main_location_id] = main_location_name

    headlines_data['main_location'] = item_dict

    headlines_data["day"] = (datetime.datetime.now()).strftime("%d")
    headlines_data["year"] = (datetime.datetime.now()).strftime("%Y")

    return headlines_data


async def set_act_header_values(worksheet, headlines_data: dict = None) -> bool:
    """Заполнение заголовка отчета
    
    :param headlines_data:
    :param worksheet:
    :return:
    """
    values: list = [
        {"coordinate": "B6",
         "value": f"Акт предписание № {headlines_data.get('act_number', 'act_number')} от "
                  f"{headlines_data.get('act_date', 'act_date')} г.",
         "row": "6",
         "column": "2"},

        {"coordinate": "B9",
         "value": f"{headlines_data.get('general_contractor_full_name', 'general_contractor_full_name')}",
         "row": "9",
         "column": "2"},

        {"coordinate": "B12",
         "value": f"{headlines_data.get('HSE_function_dative', 'HSE_function_dative')} "
                  f"{headlines_data.get('hse_department_dative', 'hse_department_dative')} "
                  f"{headlines_data.get('HSE_full_name_dative', 'HSE_full_name_dative')}",
         "row": "12",
         "column": "2"},

        {"coordinate": "B16",
         "value": f"{headlines_data.get('general_contractor_full_name', 'general_contractor_full_name')}",
         "row": "16",
         "column": "2"},

        {"coordinate": "B20",
         "value": f"{headlines_data.get('contractor_representative', 'contractor_representative')}",
         "row": "20",
         "column": "2"},
    ]

    for val in values:
        try:
            worksheet.cell(row=int(val['row']), column=int(val['column']), value=str(val['value']))
        except Exception as err:
            logger.error(f"set_user_values {repr(err)}")
            continue

    return True


async def set_act_footer_footer_values(worksheet, row_number):
    """Установка значений футера акта

    :param worksheet:
    :param row_number:
    :return:
    """
    row_value = 28 + row_number

    values: list = [
        {"coordinate": "G31",
         "value": f"{headlines_data.get('HSE_email')}",
         "row": f"{31 - 28 + row_value}",
         "column": "7"},

        {"coordinate": "G32",
         "value": f"{(headlines_data.get('act_max_date'))}",
         "row": f"{32 - 28 + row_value}",
         "column": "7"},

        {"coordinate": "B43",
         "value": f"{headlines_data.get('HSE_function')} {headlines_data.get('hse_department_dative')}",
         "row": f"{43 - 28 + row_value}",
         "column": "2"},

        {"coordinate": "B43",
         "value": f"{headlines_data.get('HSE_name_short')}",
         "row": f"{43 - 28 + row_value}",
         "column": "11"},

        {"coordinate": "B46",
         "value": f"{headlines_data.get('act_date')}",
         "row": f"{46 - 28 + row_value}",
         "column": "11"},
    ]

    for val in values:
        try:
            worksheet.cell(row=int(val['row']), column=int(val['column']), value=str(val['value']))
        except Exception as err:
            logger.error(f"set_user_values {repr(err)}")
            continue


def say_fanc_name():
    stack = traceback.extract_stack()
    return str(stack[-2][2])


async def set_act_footer_values(worksheet, row_number):
    """

     :param row_number:
     :param worksheet:
     :return:
     """
    row_value = 28 + row_number

    values = [
        {'coordinate': 'B30',
         'value': 'Информацию о выполнении пунктов настоящего предписания необходимо направить '
                  f'в письменной форме в адрес {headlines_data.get("hse_organization_full_name", None)} '
                  f'по адресу: {headlines_data.get("hse_organization_legal_address", None)} или ',
         'row': f'{30 - 28 + row_value}', 'column': '2'},
        {'coordinate': 'B31', 'value': 'на эл. адреса:',
         'row': f'{31 - 28 + row_value}', 'column': '2'},
        {'coordinate': 'G31', 'value': 'тут эл.адрес выдавшего',
         'row': f'{31 - 28 + row_value}', 'column': '7'},
        {'coordinate': 'B32', 'value': 'не позднее:',
         'row': f'{32 - 28 + row_value}', 'column': '2'},
        {'coordinate': 'G32', 'value': 'тут крайняя дата ответа',
         'row': f'{32 - 28 + row_value}', 'column': '7'},
        {'coordinate': 'B33',
         'value': 'Невыполнение предписания в установленный срок является основанием '
                  'для применения дисциплинарных взысканий',
         'row': f'{33 - 28 + row_value}', 'column': '2'},

        {'coordinate': 'B35', 'value': 'С предписанием ознакомлен: ',
         'row': f'{35 - 28 + row_value}', 'column': '2'},
        {'coordinate': 'B36',
         'value': '(Ф.И.О, подпись должность руководителя, иного должностного лица или уполномоченного представителя '
                  'юридического лица, индивидуального предпринимателя, его уполномоченного представителя)',
         'row': f'{36 - 28 + row_value}', 'column': '2'},

        {'coordinate': 'B38', 'value': 'Сведения об отказе в ознакомлении с предписанием и отказе от подписи',
         'row': f'{38 - 28 + row_value}', 'column': '2'},

        {'coordinate': 'B40',
         'value': '(фамилия, имя, отчество (последнее – при наличии), проводившего(их) проверку или '
                  'уполномоченного выдавать предписания)',
         'row': f'{40 - 28 + row_value}', 'column': '2'},

        {'coordinate': 'B42', 'value': 'Предписание выдал: ',
         'row': f'{42 - 28 + row_value}', 'column': '2'},
        {'coordinate': 'B43', 'value': 'тут должность выдавшего',
         'row': f'{43 - 28 + row_value}', 'column': '2'},
        {'coordinate': 'B43', 'value': 'тут ФИО выдавшего',
         'row': f'{43 - 28 + row_value}', 'column': '11'},
        {'coordinate': 'B44', 'value': '(должность)',
         'row': f'{44 - 28 + row_value}', 'column': '2'},
        {'coordinate': 'B44', 'value': '(подпись)',
         'row': f'{44 - 28 + row_value}', 'column': '8'},
        {'coordinate': 'B44', 'value': '(расшифровка подписи)',
         'row': f'{44 - 28 + row_value}', 'column': '11'},

        {'coordinate': 'B46', 'value': 'тут дата',
         'row': f'{46 - 28 + row_value}', 'column': '11'},
        {'coordinate': 'B47', 'value': '(дата выдачи)',
         'row': f'{47 - 28 + row_value}', 'column': '11'},

        {'coordinate': 'B49', 'value': 'Экземпляр предписания для исполнения получил:',
         'row': f'{49 - 28 + row_value}', 'column': '2'},

        {'coordinate': 'B51',
         'value': '(фамилия, имя, отчество (последнее – при наличии), должность руководителя, '
                  'иного должностного лица или уполномоченного представителя юридического лица, '
                  'индивидуального предпринимателя, его уполномоченного представителя)',
         'row': f'{51 - 28 + row_value}', 'column': '2'},

        {'coordinate': 'B53', 'value': '(дата)',
         'row': f'{53 - 28 + row_value}', 'column': '11'},

        {'coordinate': 'B55', 'value': '(подпись)',
         'row': f'{55 - 28 + row_value}', 'column': '11'},
    ]

    for val in values:
        try:
            worksheet.cell(row=int(val['row']), column=int(val['column'])).value = str(val['value'])

        except Exception as err:
            logger.error(f"set_values {repr(err)}")
            return None


async def test():
    chat_id = 862629360
    # await get_act_headlines_data_values(chat_id)

    days_max = 0
    act_date = datetime.datetime.strptime('2023-02-15', '%Y-%m-%d').strftime('%d.%m.%Y')
    t = (datetime.datetime.strptime(act_date, '%d.%m.%Y') + datetime.timedelta(
        days=days_max)).strftime('%d.%m.%Y')

    print(f'{t = }')


if __name__ == "__main__":
    asyncio.run(test())
