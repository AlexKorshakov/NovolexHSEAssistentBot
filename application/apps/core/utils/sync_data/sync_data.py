import asyncio
import os
from pprint import pprint

# from apps.core.bot.reports.report_data_preparation import \
#     preparing_violation_data_for_loading_to_google_drive
from apps.core.database.ViolationsDataBase import create_file_path
from apps.core.utils.goolgedrive_processor.googledrive_worker import (
    ROOT_REPORT_FOLDER_NAME, get_root_folder_id)
from apps.core.utils.goolgedrive_processor.GoogleDriveUtils.download_file_for_google_drive import \
    upload_file
from apps.core.utils.goolgedrive_processor.GoogleDriveUtils.find_folder import (
    find_file_by_name, find_files_or_folders_list_by_parent_id)
from apps.core.utils.goolgedrive_processor.GoogleDriveUtils.get_folder_id import \
    get_folders_ids_from_google_drive
from apps.core.utils.goolgedrive_processor.GoogleDriveUtils.GoogleDriveWorker import (
    drive_account_auth_with_oauth2client, move_file)
from apps.core.utils.goolgedrive_processor.GoogleDriveUtils.set_permissions import \
    get_user_permissions
from apps.core.utils.goolgedrive_processor.GoogleDriveUtils.upload_data_on_gdrive import \
    upload_file_on_gdrave
from apps.core.utils.secondary_functions.get_json_files import (get_dirs_files,
                                                                get_files)
from config.config import WRITE_DATA_ON_GOOGLE_DRIVE, Udocan_media_path
from loader import logger
from tqdm.asyncio import tqdm




DEBUG: bool = False

MAX_FILE: int = 10000

DICT_TYPES: dict = {
    "reports": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "photo": "image/jpeg",
    "json": "application/json",
    "violation_photo": "image/jpeg",
    "violation_json": "application/json",
}


async def get_id_item(item_name: str) -> str:
    """Получение id из имени файла для обработки и получения user_id

    Example:

    .. code-block:: python3

        report_data___04.08.2022___373084462___22485 --> 373084462
        373084462.json --> 373084462

    :type item_name: str
    :param item_name: имя файла вида report_data___{data}___{user_id}___{violation_id}
    """

    if 'report_data' in item_name:
        id_item = item_name.split('___')[-2]
    else:
        id_item = item_name.split('.')[-2]

    if DEBUG: print(f'{item_name} {id_item = }')
    return id_item


async def get_normalize_file_list(file_list: list) -> list:
    """Распаковка list[list] и получение имён файлов без полного пути

    Example:

    .. code-block:: python3

        .path\\to\\file\\report_data___04.08.2022___373084462___22485.json -->
        report_data___04.08.2022___373084462___22485.json

    :type file_list: list
    :param file_list: список файлов с полным путем файлов
    """
    return [f.split('\\')[-1] for f in file_list]


async def get_file_list(directory: str, endswith: str = ".json") -> list:
    """Получение списка файлов с нарушениям / регистрационными данными

    Example:

    .. code-block:: python3

        [...,
        f'{directory}\\{file.endswith},
        ]

    :type directory: str
    :param directory: директория для поиска файлов
    :type endswith: str
    :param endswith: расширение файлов для обработки и формирования списка
    """

    if DEBUG: print(f'{directory = }')

    if not os.path.isdir(directory):
        return []

    dirs: list = await get_dirs_files(directory=directory)

    file_list: list = []
    for f_dir in dirs:
        file_path: str = f'{directory}\\{f_dir}'

        if os.path.isdir(file_path):
            json_file_list: list = await get_files(directory=file_path, endswith=endswith)
            file_list.extend(json_file_list)

    if DEBUG:
        for n, i in enumerate(file_list): print(f'{n} {i}')

    return file_list


async def upload_file_on_google_disc(drive_service: object, preparing_data: dict, file_path: str, parent: str,
                                     id_item: str) -> None:
    """Загрузка файла на google_disc, получение разрешений на перемещение и перемещение файла в целевую папку

    :param drive_service: объект авторизации
    :param preparing_data:
    :param file_path:
    :param parent:
    :param id_item:
    """

    if not drive_service: drive_service = await drive_account_auth_with_oauth2client()

    violation_file_id: str = await upload_file_on_gdrave(
        chat_id=id_item,
        drive_service=drive_service,
        parent=parent,
        file_path=file_path,
        notify_user=False
    )

    await get_user_permissions(drive_service=drive_service, file_id=violation_file_id)

    await move_file(
        service=drive_service,
        file_id=violation_file_id,
        add_parents=parent,
        remove_parents=preparing_data["report_folder_id"]
    )


async def get_file_location_map(drive_service: object, type_files_name: str) -> list:
    """Получение всех папок и файлов из корневой директории ROOT_REPORT_FOLDER_NAME на Google Drive

    :param type_files_name: тип получаемых данных
    :param drive_service: объект авторизации
    :return: list со списком всех файлов и папок в директории ROOT_REPORT_FOLDER_NAME
    """

    mime_type = DICT_TYPES[type_files_name]

    if not drive_service: drive_service = await drive_account_auth_with_oauth2client()

    root_folder_id = await get_root_folder_id(
        drive_service=drive_service,
        root_folder_name=ROOT_REPORT_FOLDER_NAME
    )

    folders_list = await find_files_or_folders_list_by_parent_id(
        drive_service=drive_service, folder_id=root_folder_id, is_folder=True
    )

    data_list = []
    for item in tqdm(folders_list):
        folder_id = item['id']
        folder_list = await find_files_or_folders_list_by_parent_id(
            drive_service, folder_id=folder_id, is_folder=True, mime_type='application/vnd.google-apps.folder'
        )

        file_list = await find_files_or_folders_list_by_parent_id(
            drive_service, folder_id=folder_id, is_folder=False, mime_type=mime_type
        )

        data_list.append(
            {
                'user': item,
                'reg_file': file_list[0] if len(file_list) > 0 else [],
                'folder_list': folder_list
            }
        )
    return data_list


async def get_global_file_list(drive_service: object, file_location_map: list) -> list:
    """Поиск файлов на google_drive и формирование списка найденных файлов по типу из списка file_location_map

    :param file_location_map: полный список папок и файлов из корневой папки ROOT_REPORT_FOLDER_NAME,
    :param drive_service: объект авторизации
    :return: список
    """

    if not drive_service: drive_service = await drive_account_auth_with_oauth2client()

    global_file_list = []

    for item in tqdm(file_location_map):
        user_file_list = []
        for type_files in item['folder_list']:

            file_list = []
            if type_files['name'] in [k for k, v in DICT_TYPES.items()]:
                file_list = await find_files_or_folders_list_by_parent_id(
                    drive_service=drive_service, folder_id=type_files['id'],
                    is_folder=False, mime_type=DICT_TYPES[type_files['name']]
                )
            user_file_list.append(file_list)

        global_file_list.append(user_file_list)

    return global_file_list


async def normalize_global_file_list(file_list: list) -> tuple[list, list, list]:
    """Сортировка списка файлов file_list на reports, photos, json_files

    :param file_list: список файлов,
    :return: file_list - список файлов reports, список файлов photos, список файлов json_files,
    """
    reports, photos, json_files = [], [], []

    for item in tqdm(file_list):
        if not item: continue

        reports.extend(item[0])
        photos.extend(item[1])
        json_files.extend(item[2])

    return reports, photos, json_files


async def get_local_files_for_sync(endswith: str) -> tuple[list, list]:
    """Получение списка файлов на сервере (локальной машине) для синхронизации с Google Drive

    :param endswith: расширение / тип файлов для синхронизации,
    :return: file_list - список файлов с полным именем,
    normalize_file_list - список файлов без полного пути

    """
    file_list: list = await get_file_list(directory=str(f'{Udocan_media_path}\\HSE'), endswith=endswith)
    normalize_file_list: list = await get_normalize_file_list(file_list)

    return file_list, normalize_file_list


async def get_list_files_to_download(google_files: list, local_files: list, folder_name: str) -> list:
    """Сравнение списков файлов из Google Drive и с сервера.
    Определение какие локальные файлы были ранее загружены / присутствуют на Google Drive
    Формирование полного пути к файлу и добавление в item_file
    Формирование списка файлов для загрузки на Google Drive

    :param google_files: список файлов с Google Drive / облачного репозитория,
    :param local_files: список файлов с сервера / локального репозитория,
    :param folder_name: имя директории / под директории (report, photo, json) в локальном репозитории,
    :return: сформированный список файлов для загрузки
    """
    files_to_download = []
    synced, download = 0, 0

    for number_file, item_file in (enumerate(google_files, start=1)):

        if item_file['name'] in local_files:
            synced += 1
            if DEBUG: print(f'{number_file} file: {item_file} is synced')
        else:
            download += 1
            if DEBUG: print(f'{number_file} file: {item_file} need download')

            file_path = f'{str(Udocan_media_path)}\\HSE\\{item_file["name"].split("___")[2]}\\' \
                        f'data_file\\{item_file["name"].split("___")[1]}\\{folder_name}\\'
            item_file['file_path'] = file_path
            item_file["full_name"] = file_path + item_file["name"]

            files_to_download.append(item_file)

    print(f'Total google -> local: {len(google_files)} synced: {synced} need download: {download}')

    return files_to_download


async def sync_local_to_google_drive(drive_service: object = None, file_list: list = None,
                                     normalize_file_list: list = None, endswith: str = None) -> bool:
    """Синхронизация local storage -> google_drive  с расширением endswith

    :param endswith:
    :param drive_service: объект авторизации
    :param file_list: список файлов локального репозитория,
    :param normalize_file_list: список файлов локального репозитория без указания полного пути
    :return: bool
    """

    if not WRITE_DATA_ON_GOOGLE_DRIVE:
        logger.info(f'{WRITE_DATA_ON_GOOGLE_DRIVE = } abort upload / download from Google Drive')
        return False

    if not normalize_file_list:
        _, local_files = await get_local_files_for_sync(endswith=endswith)

    if not file_list:
        file_list, _ = await get_local_files_for_sync(endswith=endswith)

    last_id: str = ''
    last_id_item: str = ''
    preparing_data: dict = {}

    if not drive_service:
        drive_service = await drive_account_auth_with_oauth2client()

    synced, upload, number = 0, 0, 0
    parent: str = ''
    for nom, item in tqdm(enumerate(normalize_file_list, start=1), total=len(normalize_file_list)):

        id_item = await get_id_item(item_name=item)
        if not id_item: continue

        if last_id_item != id_item:
            preparing_data: dict = await get_folders_ids_from_google_drive(
                user=id_item,
                drive_service=drive_service
            )

            # await preparing_violation_data_for_loading_to_google_drive(
            #     data=preparing_data
            # )
            last_id_item = id_item

        if endswith == '.json':
            if last_id != id_item:
                last_id = id_item
                parent = preparing_data['user_folder_id']
            else:
                parent = preparing_data['json_folder_id']

        if endswith == '.jpg':
            parent = preparing_data['photo_folder_id']
        if endswith == '.xlsx':
            parent = preparing_data['reports_folder_id']

        result: list = await find_file_by_name(service=drive_service, name=item, parent=parent)

        if DEBUG: pprint(f'{item = } {result = }')

        if not result:
            file_path = [i for i in file_list if item in i][0]

            await upload_file_on_google_disc(drive_service=drive_service, preparing_data=preparing_data,
                                             file_path=file_path, parent=parent, id_item=id_item)
            number += 1
            upload += 1
            print(f'{nom} file upload {number} in {len(normalize_file_list)} {item}')
            synced += 1
            if number == MAX_FILE: break
        else:
            synced += 1

    print(f'Total local -> google: {len(normalize_file_list)} synced: {synced} need upload: {upload}')
    return True


async def sync_google_drive_to_local(drive_service: object, files_to_download: list) -> bool:
    """Синхронизация google_drive -> local storage

    :param files_to_download:
    :param drive_service: объект авторизации,
    :return: bool
    """

    if not WRITE_DATA_ON_GOOGLE_DRIVE:
        logger.info(f'{WRITE_DATA_ON_GOOGLE_DRIVE = } abort upload / download from Google Drive')
        return False

    if not drive_service:
        drive_service: object = await drive_account_auth_with_oauth2client()

    number = 0
    for number, item_file in enumerate(files_to_download, start=1):
        if number == MAX_FILE: break
        await create_file_path(path=item_file["file_path"])
        await upload_file(
            drive_service=drive_service,
            file_id=item_file["id"],
            file_full_name=item_file["full_name"]
        )
    print(f'download {number} files for {len(files_to_download)}')
    return True


async def get_global_files_for_sync(drive_service: object, type_files: str) -> dict:
    """Получение списка файлов типа type_files из Google Drive

    :param type_files: тип файлов
    :param drive_service: объект авторизации,
    :return: dict_files: dict = {
        "report": reports,
        "photo": photos,
        "json": json_files,
    }
    """

    if not drive_service:
        drive_service: object = await drive_account_auth_with_oauth2client()

    file_location_map: list = await get_file_location_map(drive_service=drive_service, type_files_name=type_files)

    if not file_location_map:
        return {}

    global_file_list: list = await get_global_file_list(
        drive_service=drive_service,
        file_location_map=file_location_map
    )
    if not global_file_list:
        return {}

    reports, photos, json_files = await normalize_global_file_list(global_file_list)

    dict_files: dict = {
        "report": reports,
        "photo": photos,
        "json": json_files,
    }
    return dict_files


async def get_list_files_to_download_on_google_drive(drive_service: object, local_files: list, global_files: dict,
                                                     type_files: str, endswith: str) -> list:
    """Формирование списка файлов для загрузки на Google Drive
    Получение списка локальных файлов
    Получение списка файлов на Google Drive
    Поиск локальных файлов в global_files и определение файлов которых нет в global_files
    Формирование списка файлов list_files_to_download

    :param endswith: расширение файлов для поиска в локальном репозитории
    :param type_files: тип файлов для поиска на Google Drive
    :param global_files: список файлов в Google Drive
    :param local_files: список файлов в локальном репозитории
    :param drive_service: объект авторизации,
    :return: list_files_to_download
    """
    if not local_files:
        _, local_files = await get_local_files_for_sync(endswith=endswith)

    if not global_files:
        global_files = await get_global_files_for_sync(drive_service=drive_service, type_files=type_files)

    list_files_to_download: list = await get_list_files_to_download(
        google_files=global_files[type_files],
        local_files=local_files,
        folder_name=type_files
    )
    return list_files_to_download


async def get_files_to_sync(drive_service: object, endswith: str, type_files: str) -> list:
    """Формирование списка файлов для загрузки из Google Drive

    :param type_files: тип файлов для поиска на Google Drive
    :param endswith: расширение файлов для поиска в локальном репозитории
    :param drive_service: объект авторизации,
    """

    file_list, local_files = await get_local_files_for_sync(
        endswith=endswith
    )

    dict_files: dict = await get_global_files_for_sync(
        drive_service=drive_service,
        type_files=type_files
    )

    files_to_download: list = await get_list_files_to_download_on_google_drive(
        drive_service=drive_service, local_files=local_files,
        global_files=dict_files, type_files=type_files,
        endswith=endswith
    )

    return files_to_download


async def run_sync(type_files='photo'):
    """Запуск синхронизации файлов local storage <-> google_drive
    """
    if not WRITE_DATA_ON_GOOGLE_DRIVE:
        logger.info(f'{WRITE_DATA_ON_GOOGLE_DRIVE = } abort upload / download from Google Drive')
        return

    files_types = {
        'photo': {
            'endswith': '.jpg',
            'type_files': 'photo',
            'description': 'фото материалы нарушений'
        },
        'json': {
            'endswith': '.json',
            'type_files': 'json',
            'description': 'файлы с информацией о нарушении'
        },
        'reports': {
            'endswith': '.xlsx',
            'type_files': 'reports',
            'description': 'отчеты'
        },
    }

    type_files = files_types[type_files]['type_files']
    endswith = files_types[type_files]['endswith']

    drive_service = await drive_account_auth_with_oauth2client()
    if not drive_service:
        print(f"авторизация успешно провалена!")
        return

    file_list, local_files = await get_local_files_for_sync(
        endswith=endswith
    )
    if await sync_local_to_google_drive(
            drive_service=drive_service,
            file_list=file_list,
            normalize_file_list=local_files,
            endswith=endswith
    ):
        print(f"Синхронизация local storage -> google_drive завершилась успешно")
    else:
        print(f"Ошибка синхронизации local storage -> google_drive")

    files_to_download = await get_files_to_sync(
        drive_service=drive_service,
        endswith=endswith,
        type_files=type_files
    )
    if await sync_google_drive_to_local(
            drive_service=drive_service,
            files_to_download=files_to_download
    ):
        print(f"Синхронизация google_drive -> local storage завершилась успешно")
    else:
        print(f"Ошибка синхронизации google_drive -> local storage")

    print(f"Синхронизация завершена успешно")


if __name__ == '__main__':
    dict_types = [
        'photo',
        'json',
        'reports',
    ]

    asyncio.run(run_sync(type_files='json'))
