from __future__ import annotations

from loader import logger

logger.debug(f"{__name__} start import")

import asyncio
import traceback
from aiogram import types
from pandas import DataFrame
from aiogram.dispatcher.filters import ChatTypeFilter

from apps.MyBot import MyBot
from apps.core.bot.bot_utils.check_access import (user_access_fail,
                                                  get_id_list,
                                                  user_access_granted)
from apps.core.database.query_constructor import QueryConstructor
from apps.core.database.db_utils import (db_get_id,
                                         db_get_data_list,
                                         db_get_clean_headers)

logger.debug(f"{__name__} finish import")

_PREFIX_ND: str = 'nrm_doc_'
_PREFIX_POZ: str = 'nrm_poz_'


async def is_admin_user_actions(call: types.CallbackQuery):
    return True if 'admin_user_actions_' in call.data else False


async def is_admin_add_user(call: types.CallbackQuery):
    return True if 'admin_add_user_' in call.data else False


async def is_admin_add_user_progress(call: types.CallbackQuery):
    return True if 'admin_add_add_user_progress_' in call.data else False


async def admin_add_user_default(call: types.CallbackQuery):
    return True if 'admin_add_add_user_default_' in call.data else False


async def admin_add_user_role_item(call: types.CallbackQuery):
    return True if 'admin_add_add_user_role_item_' in call.data else False


async def admin_add_user_stop(call: types.CallbackQuery):
    return True if 'admin_add_add_user_stop' in call.data else False


async def admin_add_user_role_update_role(call: types.CallbackQuery):
    return True if 'hse_role_item_' in call.data else False


async def is_lna_text_answer(call: types.CallbackQuery):
    return True if '_lna_file_' in call.data else False


async def filter_message_not_media_group(message: types.Message):
    return True if not message.media_group_id else False


async def filter_is_group(message: types.Message):
    return message.chat.type in ['group', 'supergroup']

    # if message.from_user.id not in [member.user.id for member in await message.chat.get_administrators()]:
    #     return


async def filter_is_private(message: types.Message):
    return message.chat.type in ['private']


# async def filter_is_channel(message: types.Message):
#     return ChatTypeFilter(types.ChatType.CHANNEL)


async def filter_is_super_user(message: types.Message) -> bool:
    user = message.from_user.id

    result = await check_super_user_access(chat_id=user)
    logger.info(f'check_super_user_access {user = } {result = }')
    return result


async def check_super_user_access(chat_id: int | str, role_df: DataFrame = None) -> bool:
    """Проверка допуска super_user
    """
    super_user_id_list: list = await get_id_list(
        hse_user_id=chat_id,
        user_role='hse_role_is_super_user',
        hse_role_df=role_df
    )
    if not super_user_id_list:
        logger.error(f'{await fanc_name()} access fail {chat_id = }')
        await user_access_fail(chat_id, hse_id=chat_id)
        return False

    if chat_id not in super_user_id_list:
        logger.error(f'{await fanc_name()} access fail {chat_id = }')
        return False

    logger.info(f"user_access_granted for {chat_id = }")
    await user_access_granted(chat_id, role=await fanc_name())
    return True


async def filter_is_hashtag(call: types.CallbackQuery) -> bool:
    return bool(call.data[0] == '#')


async def filter_act_required(call: types.CallbackQuery) -> bool:
    # lambda call: call.data in get_filter_data_list("ACT_REQUIRED")
    if 'fabnum' in call.data: return False
    result = call.data in await get_filter_data_list(category_in_db='core_actrequired',
                                                     coll_func=await fanc_name()
                                                     )
    return result


async def filter_category(call: types.CallbackQuery) -> bool:
    # lambda call: call.data in get_filter_data_list("CATEGORY")
    if 'fabnum' in call.data: return False
    result = call.data in await get_filter_data_list(category_in_db='core_category',
                                                     coll_func=await fanc_name()
                                                     )
    return result


async def filter_elimination_time(call: types.CallbackQuery) -> bool:
    # lambda call: call.data in get_filter_data_list("ELIMINATION_TIME")
    if 'fabnum' in call.data: return False
    result = call.data in await get_filter_data_list(category_in_db='core_eliminationtime',
                                                     coll_func=await fanc_name()
                                                     )
    return result


async def filter_general_contractors(call: types.CallbackQuery) -> bool:
    # lambda call: call.data in get_filter_data_list("GENERAL_CONTRACTORS")
    if 'fabnum' in call.data: return False
    result = call.data in await get_filter_data_list(category_in_db='core_generalcontractor',
                                                     coll_func=await fanc_name()
                                                     )
    return result


async def filter_incident_level(call: types.CallbackQuery) -> bool:
    # lambda call: call.data in get_filter_data_list("INCIDENT_LEVEL")
    if 'fabnum' in call.data: return False
    result = call.data in await get_filter_data_list(category_in_db='core_incidentlevel',
                                                     coll_func=await fanc_name()
                                                     )
    return result


async def filter_start_location(call: types.CallbackQuery) -> bool:
    # lambda call: call.data in get_filter_data_list("LOCATIONS")
    if 'fabnum' in call.data: return False
    result = call.data in await get_filter_data_list(category_in_db='core_location',
                                                     coll_func=await fanc_name()
                                                     )
    return result


async def filter_main_location(call: types.CallbackQuery) -> bool:
    # lambda call: call.data in get_filter_data_list("MAIN_LOCATIONS", condition='short_title')
    if 'fabnum' in call.data: return False
    state = MyBot.dp.current_state(user=call.from_user.id)
    v_data: dict = asyncio.run(state.get_data())
    result = call.data in await get_filter_data_list(category_in_db='core_mainlocation',
                                                     # category=v_data.get("main_location", None),
                                                     condition='short_title',
                                                     coll_func=await fanc_name()
                                                     )
    return result


async def filter_main_category(call: types.CallbackQuery) -> bool:
    if 'fabnum' in call.data: return False
    state = MyBot.dp.current_state(user=call.from_user.id)
    v_data: dict = asyncio.run(state.get_data())
    result = call.data in await get_filter_data_list(category_in_db='core_maincategory',
                                                     coll_func=await fanc_name()
                                                     )
    return result


async def filter_violation_category(call: types.CallbackQuery) -> bool:
    # lambda call: call.data in get_filter_data_list("INCIDENT_LEVEL")
    if 'fabnum' in call.data: return False
    result = call.data in await get_filter_data_list(category_in_db='core_violationcategory',
                                                     coll_func=await fanc_name()
                                                     )
    return result


async def filter_sub_location(call: types.CallbackQuery) -> bool:
    if 'fabnum' in call.data: return False
    call_data = call.data
    state = MyBot.dp.current_state(user=call.from_user.id)

    v_data: dict = asyncio.run(state.get_data())
    result = call_data in await get_filter_data_list(category_in_db='core_sublocation',
                                                     category=v_data.get("main_location", None),
                                                     condition='short_title',
                                                     coll_func=await fanc_name())
    return result


async def filter_normativedocuments(call: types.CallbackQuery) -> bool:
    if 'fabnum' in call.data: return False
    if call.data == 'nrm_doc_0': return True

    call_data = call.data
    state = MyBot.dp.current_state(user=call.from_user.id)

    v_data: dict = asyncio.run(state.get_data())
    result = call_data in await get_filter_data_list(category_in_db='core_normativedocuments',
                                                     category=v_data.get("category", None),
                                                     condition='short_title',
                                                     coll_func=await fanc_name()
                                                     )

    return result


async def get_filter_data_list(category_in_db: str = None, category: str = None, condition: str | dict = None,
                               coll_func: str = None) -> list:
    """Функция получения данных из базы данных. При отсутствии данных поиск в json.
    При наличии condition - формирование данных согласно  condition

    :param coll_func:
    :param category:
    :param category_in_db:
    :param condition:
    :return: data_list or [ ]
    """
    if not category_in_db:
        return []

    if 'fabnum' in category_in_db:
        return []

    coll_func = coll_func if coll_func else ''

    if category and condition:
        clean_datas_query: list = await get_category_data_list_whits_condition(
            db_table_name=category_in_db,
            category=category,
            condition=condition
        )
        logger.debug(f'{__name__} {await fanc_name()}  from db with condition: {clean_datas_query}')
        return clean_datas_query

    data_list: list = await get_data_from_db(db_table_name=category_in_db)

    if not data_list:
        return []

    logger.debug(f'{__name__} {await fanc_name()} {data_list = } {coll_func}')
    return data_list


async def get_category_data_list_whits_condition(db_table_name: str, category: str, condition: str | dict) -> list:
    """Получение данных из таблицы db_table_name с условиями condition

    :param category:
    :param condition:
    :param db_table_name: имя базы данных
    """
    if not db_table_name:
        return []

    if not isinstance(condition, str):
        return []

    main_table_name: str = ''

    if db_table_name == 'core_normativedocuments':
        main_table_name = 'core_category'

    if db_table_name == 'core_sublocation':
        main_table_name = 'core_mainlocation'

    if not main_table_name:
        return []

    category_id: int = await db_get_id(table=main_table_name, entry=category, calling_function_name=await fanc_name())

    if category_id is None:
        return []

    datas_from_db: list = await get_category_data_list_whits_single_condition(
        db_table_name=db_table_name,
        item_id=category_id,
        single_condition=condition
    )
    return datas_from_db


async def get_category_data_list_whits_single_condition(db_table_name: str, item_id: int,
                                                        single_condition: str) -> list:
    """ Получение данных если single_condition

    :param single_condition:
    :param item_id:
    :param db_table_name: имя базы данных
    :return: list
    """
    clean_datas_query: list = []
    query: str = ""

    if db_table_name == 'core_sublocation':
        query_kwargs: dict = {
            "action": 'SELECT', "subject": '*',
            "conditions": {
                "main_location_id": item_id,
            },
        }
        query: str = await QueryConstructor(None, db_table_name, **query_kwargs).prepare_data()
        logger.debug(f'{__name__} {await fanc_name()} {query = }')

    if db_table_name == 'core_normativedocuments':
        query_kwargs: dict = {
            "action": 'SELECT', "subject": '*',
            "conditions": {
                "category_id": item_id,
            },
        }
        query: str = await QueryConstructor(None, db_table_name, **query_kwargs).prepare_data()
        logger.debug(f'{__name__} {await fanc_name()} {query = }')

    datas_query: list = await db_get_data_list(query=query)

    if not datas_query:
        return []

    if not isinstance(datas_query, list):
        return []

    if single_condition == 'short_title':

        if db_table_name == 'core_sublocation':
            clean_datas_query: list = [_PREFIX_POZ + str(item[0]) for item in datas_query]

        if db_table_name == 'core_normativedocuments':
            clean_datas_query: list = [_PREFIX_ND + str(item[0]) for item in datas_query]

        return clean_datas_query

    if single_condition == 'data_list':
        clean_datas_query: list = [item[2] for item in datas_query]
        return clean_datas_query


async def get_data_from_db(db_table_name: str) -> list:
    """Получение данных из таблицы db_table_name базы данных
    """
    if not db_table_name:
        return []

    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
    }
    query: str = await QueryConstructor(None, db_table_name, **query_kwargs).prepare_data()
    datas_query: list = await db_get_data_list(query=query)

    if not isinstance(datas_query, list):
        return []

    clean_headers: list = await db_get_clean_headers(table_name=db_table_name)

    if 'short_title' in clean_headers:
        data_list = [data[2] for data in datas_query]
        return data_list

    if datas_query:
        logger.debug(f'retrieved data from database: {datas_query}')
        data_list = [data[1] for data in datas_query]
        return data_list

    return []


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])
