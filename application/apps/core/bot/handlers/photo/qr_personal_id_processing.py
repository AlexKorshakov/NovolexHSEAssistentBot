from __future__ import annotations

import asyncio
import io
import json
import os
import sqlite3
from datetime import datetime, timedelta
from itertools import chain

from aiogram import types
from aiogram.dispatcher import FSMContext

from apps.MyBot import bot_send_message, MyBot
from config.config import Novolex_Bagration_subcontractor_employee_DB, Novolex_media_path
from loader import logger
from apps.core.bot.bot_utils.check_access import get_hse_user_data
from apps.core.bot.data.board_config import BoardConfig as board_config
from apps.core.bot.filters.custom_filters import filter_is_private
from apps.core.bot.handlers.photo.qr_support_paths import qr_check_path, qr_get_file_path, qr_check_or_create_dir
from apps.core.bot.states import PersonalIdHuntingState
from apps.core.database.query_constructor import QueryConstructor


class DataBaseSubconEmployeeID:

    def __init__(self):

        if not qr_check_path(Novolex_Bagration_subcontractor_employee_DB):
            logger.error(f'Path {Novolex_Bagration_subcontractor_employee_DB} is not exists!')

        self.db_file = Novolex_Bagration_subcontractor_employee_DB
        self.connection = sqlite3.connect(self.db_file)
        self.cursor = self.connection.cursor()

        self.name: str = self.db_file.stem

    async def create_backup(self) -> str | None:
        """

        :return:
        """
        backup_file_path: str = f"C:\\backup\\{datetime.now().strftime('%d.%m.%Y')}\\"
        if not os.path.isdir(backup_file_path):
            os.makedirs(backup_file_path)

        query: str = f"vacuum into '{backup_file_path}backup_{datetime.now().strftime('%d.%m.%Y, %H.%M.%S')}_{self.name}.db'"

        try:
            with self.connection:
                result = self.cursor.execute(query)
                return self.name

        except (ValueError, sqlite3.OperationalError) as err:
            logger.error(f'Invalid query. {repr(err)}')
            return None

        finally:
            self.cursor.close()

    async def get_table_headers(self, table_name: str = None) -> list[str]:
        """Получение всех заголовков таблицы core_violations

        :return: list[ ... ]
        """
        if not table_name:
            return []

        with self.connection:
            result: list = self.cursor.execute(f"PRAGMA table_info('{table_name}')").fetchall()
            clean_headers: list = [item[1] for item in result]
            return clean_headers

    async def get_all_tables_names(self) -> list:
        """Получение всех имен таблиц в БД

        :return:
        """
        with self.connection:
            result: list = self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
            return result

    async def get_data_list(self, query: str = None) -> list:
        """Получение данных из таблицы по запросу 'query'"""
        if not query:
            return []

        with self.connection:
            return self.cursor.execute(query).fetchall()

    async def db_get_data_list(self, table_name: str = None, query: str = '') -> list:
        """Получение данных из таблицы table_name"""

        if not query:
            query_kwargs: dict = {
                "action": 'SELECT', "subject": '*',
            }
            query: str = await QueryConstructor(None, table_name, **query_kwargs).prepare_data()

        try:
            with self.connection:
                result: list = self.cursor.execute(query).fetchall()

            if not result:
                # logger.error(f"no matches found {table_name} in DB "
                #              f"because .cursor.execute is none `table_name`: {table_name}")
                return []
            return result
        except (ValueError, sqlite3.OperationalError) as err:
            logger.error(f'Invalid query. {repr(err)}')
            return []
        finally:
            self.cursor.close()


async def qr_personal_id_processing(hse_user_id: str | int, data: list, message, state: FSMContext = None):
    """

    :param state:
    :param message:
    :param hse_user_id: str
    :param data: list
    :return:
    """
    # board_config.id_data_list = data
    await board_config(state, "id_data_list", data).set_data()

    await PersonalIdHuntingState.location.set()

    item_text: str = '_'.join([item.replace('personal_id_code_', '') for item in data])
    file_path: str = await get_directory_path()

    destination_file: str = await qr_get_file_path(file_path, f'{get_today()}_{item_text}.jpg')
    await message.photo[-1].download(make_dirs=False, destination_file=destination_file)

    item_txt: str = 'введите литер позиции'
    await bot_send_message(chat_id=hse_user_id, text=item_txt)


@MyBot.dp.message_handler(filter_is_private, state=PersonalIdHuntingState.all_states)
async def persona_id_hunting_all_states_answer(message: types.Message = None, user_id: int | str = None,
                                               data: list = None, state: FSMContext = None):
    """Обработка изменений

    :param data:
    :param user_id:
    :param message:
    :param state:
    :return:
    """
    hse_user_id = message.chat.id if message else user_id

    v_data: dict = await state.get_data()

    logger.info(f'{hse_user_id = } {message.text = }')

    location: str = message.text
    data = data if data else v_data['id_data_list']

    data_to_base, data_to_notice = await check_data(data)

    if data_to_notice:
        await notice_hse_user(hse_user_id, data_to_notice)

        file_path: str = await get_directory_path()
        recorded_cases_file_path: str = await qr_get_file_path(file_path, f'{get_today()} recorded_cases.json')
        recorded_cases: list = await read_json_file(file=recorded_cases_file_path)
        if not recorded_cases: recorded_cases = []

        write_result: bool = await write_json(
            file=recorded_cases_file_path,
            data=[f'{item} ::: {get_today()} ::: {get_time()} ::: {location}' for item in
                  data_to_notice] + recorded_cases
        )
        if write_result:
            await bot_send_message(chat_id=hse_user_id, text=f'Повторные данные внесены в реестр {data}')

    if data_to_base:
        personal_id_data_list: list = await prepare_data(hse_user_id, data_to_base, location)

        file_path: str = await get_directory_path()
        personal_id_data_file_path: str = await qr_get_file_path(file_path, f'{get_today()} personal_id_data.json')
        data_list: list = await read_json_file(file=personal_id_data_file_path)
        if not data_list: data_list = []

        write_result = await write_json(
            file=personal_id_data_file_path,
            data=data_list + personal_id_data_list
        )
        if write_result:
            await bot_send_message(chat_id=hse_user_id, text=f'Новые данные внесены {data}')

            await state.finish()
            # board_config.id_data_list = []
            await board_config(state, "id_data_list", []).set_data()

    await state.finish()
    # board_config.id_data_list = []
    await board_config(state, "id_data_list", []).set_data()
    return False


async def get_directory_path():
    file_path: str = await qr_get_file_path(Novolex_media_path, 'BAGRATION', 'personal_id_hunting', get_today())
    await qr_check_or_create_dir(file_path)
    return file_path


def get_today() -> str:
    return (datetime.today() + timedelta(hours=6)).strftime("%d.%m.%Y")


def get_time() -> str:
    return (datetime.now() + timedelta(hours=6)).strftime("%H:%M:%S")


async def notice_hse_user(hse_user_id: str | int, result_list: list) -> list:
    """

    :param hse_user_id:
    :param result_list:
    :return:
    """
    if not result_list:
        return []

    file_path: str = await get_directory_path()
    full_file_path: str = await qr_get_file_path(file_path, f'{get_today()} personal_id_data.json')

    data_list: list = await read_json_file(full_file_path)
    if not data_list: data_list = []

    for item in result_list:
        for data_item_dict in data_list:
            if item.replace('personal_id_code_', '') not in data_item_dict:
                continue

            item_dict: dict = data_item_dict[item.replace('personal_id_code_', '')]
            hse_user_data: dict = await get_hse_user_data(chat_id=item_dict.get('hse_user_id'))

            notice_text: str = f"Номер работника {item_dict.get('personal_id')} уже был внесен в базу " \
                               f"в {item_dict.get('time')} " \
                               f"на площадке {item_dict.get('location')} " \
                               f"cотрудником УМ {hse_user_data.get('hse_function_dative')} " \
                               f" {hse_user_data.get('hse_full_name_dative')}"

            await bot_send_message(chat_id=hse_user_id, text=notice_text)

            file_path: str = await get_directory_path()
            file_full_recorded_cases_path: str = await qr_get_file_path(file_path,
                                                                        f'{get_today()} full_recorded_cases.json')
            recorded_cases: list = await read_json_file(file=file_full_recorded_cases_path)
            if not recorded_cases: recorded_cases = []

            await write_json(
                file=file_full_recorded_cases_path,
                data=[notice_text] + recorded_cases
            )

    return []


async def check_data(personal_id_data_list: list) -> tuple:
    """

    :param personal_id_data_list:
    :return:
    """
    file_path: str = await get_directory_path()
    full_file_path: str = await qr_get_file_path(file_path, f'{get_today()} personal_id_data.json')

    if not qr_check_path(full_file_path):
        return personal_id_data_list, []

    result_list: list = await read_json_file(full_file_path)

    if not result_list:
        return personal_id_data_list, []

    data_to_notice: list = []
    data_to_base: list = []
    id_data_list = list(chain(*[list(item.keys()) for item in result_list]))
    for item in personal_id_data_list:
        i_item: str = item.replace('personal_id_code_', '')
        data_to_notice.append(item) if i_item in id_data_list else data_to_base.append(item)

    return data_to_base, data_to_notice


async def prepare_data(hse_user_id: str | int, data: list, location: str) -> list:
    """

    :return:
    """
    data_list: list = []
    prepare_dict: dict = {}

    for item in data:
        prepare_dict['id_data'] = item
        prepare_dict['personal_id'] = item.split('_')[-1]
        prepare_dict['hse_user_id'] = hse_user_id
        prepare_dict['date'] = get_today()
        prepare_dict['time'] = get_time()
        prepare_dict['location'] = location

        id_data_dict: dict = await check_ids(item.split('_')[-1])

        prepare_dict['subcontractor'] = id_data_dict.get('subcontractor')
        prepare_dict['function'] = id_data_dict.get('function')

        data_list.append({f"{item.split('_')[-1]}": prepare_dict})
        prepare_dict: dict = {}
    return data_list


async def check_employee_id(item_id) -> list:
    """"""
    table_name = 'bagration_subcontractor_emploee_id'

    if not item_id:
        return []

    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "lazy_query": f"`emploee_id` LIKE '%{item_id}%'",
        },
    }
    query: str = await QueryConstructor(None, table_name, **query_kwargs).prepare_data()

    try:
        datas_list: list = await DataBaseSubconEmployeeID().db_get_data_list(table_name=table_name, query=query)

    except sqlite3.OperationalError as err:
        logger.error(f'{table_name = } is missing from the database! err: {repr(err)}')
        return []

    if not datas_list:
        # logger.error('Missing datas_list from the database.')
        return []

    clean_headers: list = await DataBaseSubconEmployeeID().get_table_headers(table_name)
    list_dicts: list = [dict(zip(clean_headers, data_list)) for data_list in datas_list]

    if list_dicts:
        return list_dicts

    return []


async def check_employee_id_from_db(item_id) -> list:
    """"""
    table_name = 'bagration_subcontractor_emploee_id'

    if not item_id:
        return []

    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "id": item_id,
        },
    }
    query: str = await QueryConstructor(None, table_name, **query_kwargs).prepare_data()

    try:
        datas_list: list = await DataBaseSubconEmployeeID().db_get_data_list(table_name=table_name, query=query)

    except sqlite3.OperationalError as err:
        logger.error(f'{table_name = } is missing from the database! err: {repr(err)}')
        return []

    if not datas_list:
        # logger.error('Missing datas_list from the database.')
        return []

    clean_headers: list = await DataBaseSubconEmployeeID().get_table_headers(table_name)
    list_dicts: list = [dict(zip(clean_headers, data_list)) for data_list in datas_list]

    if list_dicts:
        return list_dicts

    return []


async def read_json_file(file: str):
    """Получение данных из json.

    :param file: полный путь к файлу
    """
    try:
        with open(file, 'r', encoding='utf8') as data_file:
            data_loaded = json.load(data_file)
        return data_loaded
    except FileNotFoundError:
        return None


async def write_json(file: str, data: list) -> bool:
    """Запись данных в json

    :param file: полный путь для записи / сохранения файла включая расширение,
    :param data: данные для записи / сохранения
    :return: True or False
    """
    try:
        with io.open(file, 'w', encoding='utf8') as outfile:
            str_ = json.dumps(data,
                              indent=4,
                              sort_keys=True,
                              separators=(',', ': '),
                              ensure_ascii=False)
            outfile.write(str_)
            return True
    except TypeError as err:
        logger.error(f"TypeError: {repr(err)}")
        return False


async def test_fank(item_id):
    # list_1_da = 0
    # list_1_net = 0
    # list_3_da = 0
    # list_3_net = 0
    list_1_da_List = []

    emploee_id = item_id[1:-2]
    item_dict = await check_employee_id(emploee_id)
    # print(f'{len(item_dict)} item_id[1:-2] {emploee_id} {item_dict} ')
    if len(item_dict) == 1:
        # list_1_da += 1
        # print(item_dict)
        list_1_da_List.append(item_dict)

    # if len(item_dict) > 1:
    #     list_1_net += 1

    emploee_id = item_id[1:-1]
    item_dict = await check_employee_id(emploee_id)
    # print(f'{len(item_dict)} item_id[1:-1] {emploee_id}  {item_dict}')
    if len(item_dict) == 1:
        # list_3_da += 1
        # print(item_dict)
        list_1_da_List.append(item_dict)

    # if len(item_dict) > 1:
    #     list_3_net += 1

    # print(f'{list_1_da = }')
    # print(f'{list_1_net = }')
    # print(f'{list_3_da = }')
    # print(f'{list_3_net = }')
    # print(f'{len(list_1_da_List)}')
    return list_1_da_List


async def check_ids(item_id) -> dict:
    """"""
    list_datas = await test_fank(item_id)
    id_data_list: list = list(chain(*[list(item) for item in list_datas]))
    unique_id_list: list = list(set([item.get('id') for item in id_data_list]))
    if not unique_id_list:
        return {}
    id_data: list = await check_employee_id_from_db(unique_id_list[0])
    return id_data[0]


async def test():
    media_patch: str = await qr_get_file_path(Novolex_media_path, 'media', 'BAGRATION', 'personal_id_hunting')

    json_files_list: list = []
    for subdir, dirs, files in os.walk(media_patch):
        for file in files:

            filepath = await qr_get_file_path(subdir, file)
            if filepath.endswith('.py'): continue
            if filepath.endswith('.jpg'): continue
            if filepath.endswith('.tmp'): continue
            if filepath.endswith('.db'): continue
            if "personal_id_data.json" not in filepath: continue
            if not file: continue
            if '~' in file: continue

            period = None
            if not await check_data_period(file, period): continue

            json_files_list.append(
                {
                    "file": file,
                    "subdir": subdir,
                    "full_file_path": await qr_get_file_path(subdir, file),
                }
            )
    all_data_id_list: list = [
        await read_json_file(item.get('full_file_path')) for item in json_files_list if item.get('full_file_path')
    ]

    id_data_list: list = list(chain(*[list(item) for item in all_data_id_list]))

    employee_list: list = []
    for i in id_data_list:
        employee_list.append([k for k, v in i.items()][0])

    uniq_employee_list_fin: list = list(set(employee_list))
    print(f'uniq_employee_list_fin: {len(uniq_employee_list_fin)}')

    all_data = []
    for item_id in uniq_employee_list_fin:
        id_data = await check_ids(item_id)
        if id_data:
            all_data.append(id_data)
    print(f'all_data: {len(all_data)}')


async def check_data_period(file: str, period: list | None = None) -> bool:
    """"""
    if not period: return True
    if len(period) == 1: return False
    if len(period) > 2: return False

    _format: str = '%d.%m.%Y'
    file_date_from_name = file.split(' ')[0]

    try:
        file_date = datetime.strptime(file_date_from_name, _format).date()
    except ValueError:
        logger.warning(f"file: {file} file_date: {file.split(' ')[0]}")
        return False

    start_period = datetime.strptime(period[0], _format).date()
    stop_period = datetime.strptime(period[1], _format).date()

    if start_period <= file_date <= stop_period:
        return True

    return False


if __name__ == '__main__':
    asyncio.run(test())
