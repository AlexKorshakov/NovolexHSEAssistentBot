from loader import logger

logger.debug(f"{__name__} start import")
from pandas import DataFrame
from aiogram.utils.exceptions import NetworkError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import ClientConnectorError

from apps.core.database.db_utils import (db_get_data_list,
                                         db_get_clean_headers)
from apps.core.database.query_constructor import QueryConstructor
from apps.xxx import assistant

logger.debug(f"{__name__} finish import")


async def admin_notify(user_id, notify_text: str, button: InlineKeyboardButton = None) -> bool:
    """Уведомление админов
    """

    logger.info(f"{notify_text = }")
    try:
        reply_markup = InlineKeyboardMarkup()
        reply_markup.add(InlineKeyboardButton(text=f'{user_id}', url=f"tg://user?id={user_id}"))

        if button:
            reply_markup.add(button)

        for bot_admin in await get_developer_id_list():
            await assistant.send_message(chat_id=bot_admin, text=notify_text, reply_markup=reply_markup)
        return True

    except (NetworkError, ClientConnectorError) as err:
        logger.error(f'{user_id = } connect err')
        logger.error(f'{user_id = } ошибка уведомления ADMIN_ID {repr(err)}')
        return False

    except Exception as err:
        logger.error(f'{user_id = } ошибка уведомления ADMIN_ID {repr(err)}')
        return False


async def get_developer_id_list() -> list:
    """Получение id разработчиков"""

    db_table_name: str = 'core_hseuser'

    kwargs: dict = {
        "action": 'SELECT',
        "subject": '*',
    }
    query: str = await QueryConstructor(table_name=db_table_name, **kwargs).prepare_data()
    datas_query: list = await db_get_data_list(query=query)
    if not datas_query:
        return []

    if not isinstance(datas_query, list):
        return []

    clean_headers: list = await db_get_clean_headers(table_name=db_table_name)
    if not clean_headers:
        return []

    try:
        hse_role_receive_df: DataFrame = DataFrame(datas_query, columns=clean_headers)
    except Exception as err:
        logger.error(f"create_dataframe {repr(err)}")
        return []

    current_act_violations_df: DataFrame = hse_role_receive_df.loc[
        hse_role_receive_df['hse_role_is_developer'] == 1
        ]

    unique_hse_telegram_id: list = current_act_violations_df.hse_telegram_id.unique().tolist()

    return unique_hse_telegram_id


# async def test2():
#     user_id: str = '373084462'
#     notify_text: str = f'User {user_id} попытка доступа к функциям без регистрации'
#     button = InlineKeyboardButton(text=f'{user_id}', url=f"tg://user?id={user_id}")
#     answer: bool = await admin_notify(user_id, notify_text, button)
#     print(answer)
#
#
# if __name__ == "__main__":
#     asyncio.run(test2())
