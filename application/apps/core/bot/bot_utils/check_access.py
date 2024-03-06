from __future__ import print_function, annotations

import re
import traceback

from aiogram import types
from pandas import DataFrame

from apps.MyBot import bot_send_message
from apps.core.bot.bot_utils.bot_admin_notify import admin_notify
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages import Messages
from apps.core.bot.messages.messages_test import msg
from apps.core.database.db_utils import (db_get_data_list,
                                         db_get_clean_headers)
from apps.core.database.query_constructor import QueryConstructor
from loader import logger


async def check_user_access(*, chat_id, message: types.Message = None, notify_admin: bool = None,
                            role_df: DataFrame = None) -> bool:
    """Проверка наличия регистрационных данных пользователя

    :return: bool
    """

    chat_id = chat_id if chat_id else message.chat.id

    if not await base_check_user_access(chat_id, role_df=role_df):
        logger.error(f'access fail {chat_id = }')
        await user_access_fail(chat_id, hse_id=chat_id)
        return False

    table_data: list = await get_list_table_values(chat_id)
    if not table_data:
        logger.error(f'access fail {chat_id = } {table_data =}')
        await user_access_fail(chat_id, hse_id=chat_id)
        return False

    clean_headers: list = await db_get_clean_headers(table_name='core_hseuser')
    hse_user_data_dict: dict = await get_data_dict(clean_headers, table_data)

    if not hse_user_data_dict:
        logger.error(f'access fail {chat_id = } {hse_user_data_dict =}')
        await user_access_fail(chat_id, hse_id=chat_id)
        return False

    if not hse_user_data_dict.get('hse_is_work', None):
        logger.error(
                f"access fail {chat_id = } {hse_user_data_dict =} hse_is_work {hse_user_data_dict.get('hse_is_work', None)}")
        await user_access_fail(chat_id, hse_id=chat_id)
        return False

    if not hse_user_data_dict.get('hse_status', None):
        logger.error(
                f"access fail {chat_id = } {hse_user_data_dict =} hse_status {hse_user_data_dict.get('hse_status', None)}")
        await user_access_fail(chat_id, hse_id=chat_id)
        return False

    hse_user_role_dict: dict = await get_dict_hse_user_role(hse_user_data_dict)
    logger.debug(f'{chat_id = } ::: {hse_user_role_dict = }')

    if not hse_user_role_dict.get('hse_role_is_user', None):
        logger.info(f"{chat_id = } ::: {hse_user_role_dict.get('hse_role_is_user', None) = }")
        logger.error(
                f"access fail {chat_id = } {hse_user_role_dict =} hse_status {hse_user_role_dict.get('hse_role_is_user', None)}")
        await user_access_fail(chat_id, hse_id=chat_id)
        return False

    if notify_admin:
        logger.info(f"{notify_admin = }")
        await user_access_granted(chat_id)

    return True


async def base_check_user_access(chat_id: int | str, role_df: DataFrame = None):
    """

    :param role_df:
    :param chat_id:
    :return:
    """
    user_id_list: list = await get_id_list(
            hse_user_id=chat_id, user_role='hse_role_is_user', hse_role_df=role_df
    )
    if not user_id_list:
        logger.error(f'{await fanc_name()} access fail {chat_id = }')
        await user_access_fail(chat_id, hse_id=chat_id)
        return False

    if chat_id not in user_id_list:
        logger.error(f'{await fanc_name()} access fail {chat_id = }')
        return False

    logger.debug(f"user_access_granted for {chat_id = }")
    await user_access_granted(chat_id, role=await fanc_name())
    return True


async def check_admin_access(chat_id: int | str, role_df: DataFrame = None):
    """

    :param role_df:
    :param chat_id:
    :return:
    """
    admin_id_list: list = await get_id_list(
            hse_user_id=chat_id, user_role='hse_role_is_admin', hse_role_df=role_df
    )
    if not admin_id_list:
        logger.warning(f'{await fanc_name()} access fail {chat_id = }')
        await user_access_fail(chat_id, hse_id=chat_id)
        return False

    if chat_id not in admin_id_list:
        logger.warning(f'{await fanc_name()} access fail {chat_id = }')
        return False

    logger.info(f"user_access_granted for {chat_id = }")
    await user_access_granted(chat_id, role=await fanc_name(), notify=True)
    return True


async def check_super_user_access(chat_id: int | str, role_df: DataFrame = None):
    """

    :param role_df:
    :param chat_id:
    :return:
    """
    super_user_id_list: list = await get_id_list(
            hse_user_id=chat_id, user_role='hse_role_is_super_user', hse_role_df=role_df
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


async def check_developer_access(chat_id: int | str, role_df: DataFrame = None):
    """

    :param role_df:
    :param chat_id:
    :return:
    """
    developer_id_list: list = await get_id_list(
            hse_user_id=chat_id, user_role='hse_role_is_developer', hse_role_df=role_df
    )
    if not developer_id_list:
        logger.error(f'{await fanc_name()} access fail {chat_id = }')
        await user_access_fail(chat_id, hse_id=chat_id)
        return False

    if chat_id not in developer_id_list:
        logger.error(f'{await fanc_name()} access fail {chat_id = }')
        return False

    logger.info(f"user_access_granted for {chat_id = }")
    await user_access_granted(chat_id, role=await fanc_name())
    return True


async def check_autor_access(chat_id: int | str, role_df: DataFrame = None):
    """

    :param role_df:
    :param chat_id:
    :return:
    """
    autor_id_list: list = await get_id_list(
            hse_user_id=chat_id, user_role='hse_role_is_author', hse_role_df=role_df
    )
    if not autor_id_list:
        logger.error(f'{await fanc_name()} access fail {chat_id = }')
        await user_access_fail(chat_id, hse_id=chat_id)
        return False

    if chat_id not in autor_id_list:
        logger.error(f'{await fanc_name()} access fail {chat_id = }')
        return False

    logger.info(f"user_access_granted for {chat_id = }")
    await user_access_granted(chat_id, role=await fanc_name())
    return True


async def check_coordinating_person_access(chat_id: int | str, role_df: DataFrame = None):
    """

    :param role_df:
    :param chat_id:
    :return:
    """
    coordinating_person_id_list: list = await get_id_list(
            hse_user_id=chat_id, user_role='hse_role_is_coordinating_person', hse_role_df=role_df
    )
    if not coordinating_person_id_list:
        logger.error(f'{await fanc_name()} access fail {chat_id = }')
        await user_access_fail(chat_id, hse_id=chat_id)
        return False

    if chat_id not in coordinating_person_id_list:
        logger.error(f'{await fanc_name()} access fail {chat_id = }')
        return False

    logger.info(f"user_access_granted for {chat_id = }")
    await user_access_granted(chat_id, role=await fanc_name(), notify=True)
    return True


async def check_subcontractor_access(chat_id: int | str, role_df: DataFrame = None):
    """

    :param role_df:
    :param chat_id:
    :return:
    """
    subcontractor_id_list: list = await get_id_list(
            hse_user_id=chat_id, user_role='hse_role_is_coordinating_person', hse_role_df=role_df
    )
    if not subcontractor_id_list:
        logger.error(f'{await fanc_name()} access fail {chat_id = }')
        await user_access_fail(chat_id, hse_id=chat_id)
        return False

    if chat_id not in subcontractor_id_list:
        logger.error(f'{await fanc_name()} access fail {chat_id = }')
        return False

    logger.info(f"user_access_granted for {chat_id = }")
    await user_access_granted(chat_id, role=await fanc_name(), notify=True)
    return True


async def user_access_fail(chat_id: int, notify_text: str = None, hse_id: str = None) -> object:
    """Отправка сообщения о недостатке прав
    """
    hse_id = hse_id if hse_id else chat_id

    try:
        part_1 = f"{await msg(hse_id, cat='error', msge='access_fail', default=Messages.default_answer_text).g_mas()}"
        part_2 = f"{await msg(hse_id, cat='help', msge='help_message', default=Messages.help_message).g_mas()}"
        answer_text = f'{part_1}\n\n{part_2}'
        print(f'{answer_text = }')

        await bot_send_message(chat_id=chat_id, text=answer_text, disable_web_page_preview=True)
        return

    except Exception as err:
        logger.error(f'User {chat_id} ошибка уведомления пользователя {repr(err)}')
        await admin_notify(user_id=chat_id, notify_text=notify_text)

    finally:
        if not notify_text:
            notify_text: str = f'User {chat_id} попытка доступа к функциям без регистрации'

        logger.error(notify_text)
        button = types.InlineKeyboardButton('user_actions',
                                            callback_data=posts_cb.new(id='-', action=f'admin_user_actions_{chat_id}'))
        await admin_notify(
                user_id=chat_id,
                notify_text=notify_text,
                button=button
        )


async def user_access_granted(chat_id: int, role: str = None, notify=False):
    """Отправка сообщения - доступ разрешен"""

    # reply_markup = types.InlineKeyboardMarkup()
    # reply_markup.add(types.InlineKeyboardButton(text=f'{chat_id}', url=f"tg://user?id={chat_id}"))

    notify_text: str = f'доступ разрешен {chat_id} {role = }'
    logger.debug(notify_text)
    if notify:
        await admin_notify(user_id=chat_id, notify_text=notify_text)


async def get_id_list(hse_user_id: str | int, user_role: str = None, hse_role_df: DataFrame = None) -> list:
    """Получение id"""

    if not await check_dataframe_role(hse_role_df, hse_user_id):
        hse_role_df: DataFrame = await get_hse_role_receive_df()
        if not await check_dataframe_role(hse_role_df, hse_user_id):
            return []

    try:
        current_act_violations_df: DataFrame = hse_role_df.loc[
            hse_role_df[user_role] == 1]

    except Exception as err:
        logger.error(f"loc dataframe {repr(err)}")
        return []

    unique_hse_telegram_id: list = current_act_violations_df.hse_telegram_id.unique().tolist()
    if not unique_hse_telegram_id:
        return []

    return unique_hse_telegram_id


async def get_hse_role_receive_df() -> DataFrame | None:
    """Получение df с ролями пользователя

    :return:
    """

    db_table_name: str = 'core_hseuser'
    kwargs: dict = {
        "action": 'SELECT',
        "subject": '*',
    }
    query: str = await QueryConstructor(table_name=db_table_name, **kwargs).prepare_data()
    datas_query: list = await db_get_data_list(query=query)
    if not datas_query:
        return None

    if not isinstance(datas_query, list):
        return None

    clean_headers: list = await db_get_clean_headers(table_name=db_table_name)
    if not clean_headers:
        return None

    try:
        hse_role_receive_df: DataFrame = DataFrame(datas_query, columns=clean_headers)
    except Exception as err:
        logger.error(f"create_dataframe {repr(err)}")
        return None

    return hse_role_receive_df


async def check_dataframe_role(dataframe: DataFrame, hse_user_id: str | int) -> bool:
    """Проверка dataframe на наличие данных

    :param dataframe:
    :param hse_user_id: id пользователя
    :return:
    """
    if dataframe is None:
        # text_violations: str = 'не удалось получить данные!'
        # logger.error(f'{hse_user_id = } {text_violations}')
        # await bot_send_message(chat_id=hse_user_id, text=text_violations)
        return False

    if dataframe.empty:
        logger.error(f'{hse_user_id = } {Messages.Error.dataframe_is_empty}')
        return False

    return True


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])


async def get_list_table_values(chat_id: int) -> list:
    """Получение данных таблицы по chat_id

    :param chat_id:
    :return:
    """

    query_kwargs: dict = {
        "action": 'SELECT', "subject": '*',
        "conditions": {
            "hse_telegram_id": chat_id,
        },
    }
    query: str = await QueryConstructor(None, 'core_hseuser', **query_kwargs).prepare_data()
    datas_query: list = await db_get_data_list(query=query)

    if not datas_query:
        return []

    if not isinstance(datas_query, list):
        return []

    return list(datas_query[0])


async def get_data_dict(table_headers: list, table_data: list) -> dict:
    """Формирование dict с данными

    :param table_headers:
    :param table_data:
    :return:
    """
    table_dict: dict = {}
    for header, data in zip(table_headers, table_data):
        table_dict[header] = data

    return table_dict


async def get_hse_role(hse_user_data_dict: dict) -> list:
    """Получение ролей пользователя из БД на основе chat_id

    :param hse_user_data_dict:
    :return: list
    """

    hse_role_name: list = [name for name, value in hse_user_data_dict.items() if re.search(r'_role_', name)]
    return hse_role_name


async def get_dict_hse_user_role(hse_user_data_dict: dict) -> dict:
    """Получение ролей пользователя из БД на основе chat_id

    :return: dict
    """

    hse_roles: list = await get_hse_role(hse_user_data_dict)
    hse_roles_dict = {name: value for name, value in hse_user_data_dict.items() if name in hse_roles}
    return dict(hse_roles_dict)


async def get_hse_user_data(*, message: types.Message = None, chat_id: int | str = None) -> dict:
    """Получение данных пользователя из БД на основе chat_id

    :return: dict
    """
    try:
        chat_id = chat_id if chat_id else message.chat.id
    except AttributeError as err:
        logger.debug(f'{__file__} {repr(err)}')
        chat_id = chat_id if chat_id else message.from_user.id

    table_data: list = await get_list_table_values(chat_id)
    if not table_data:
        return {}

    clean_headers: list = await db_get_clean_headers(table_name='core_hseuser')
    hse_user_data_dict: dict = await get_data_dict(clean_headers, table_data)

    if not hse_user_data_dict:
        return {}

    return hse_user_data_dict


async def get_user_data_dict(chat_id: int) -> tuple[dict, dict]:
    """Получение данных пользователя и ролей пользователя отдельно

    :param chat_id:
    :return: tuple[dict, dict]
    """

    table_data: list = await get_list_table_values(chat_id)
    clean_headers: list = await db_get_clean_headers(table_name='core_hseuser')
    hse_user_data_dict: dict = await get_data_dict(clean_headers, table_data)
    hse_user_role_dict: dict = await get_dict_hse_user_role(hse_user_data_dict)

    return hse_user_data_dict, hse_user_role_dict
