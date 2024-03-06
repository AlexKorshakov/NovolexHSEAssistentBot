import traceback

from aiogram import types

from apps.MyBot import MyBot
from apps.core.bot.bot_utils.check_access import check_developer_access, check_user_access
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from loader import logger

# import reload_and_start_bot_with_bash


@MyBot.dp.callback_query_handler(posts_cb.filter(action=['s_user_shutdown']))
async def s_user_set_current_file(call: types.CallbackQuery, callback_data: dict[str, str]):
    """Обработка ответов содержащихся в s_user_get_files
    """

    hse_user_id = call.message.chat.id
    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'{await fanc_name()} access fail {hse_user_id = }')
        return

    if not await check_developer_access(chat_id=hse_user_id):
        logger.error(f'{await fanc_name()} check_super_user_access fail {hse_user_id = }')
        return

    logger.warning(f'{MyBot.bot._me.first_name} Bye! Shutting down connection')
    await MyBot.dp.storage.close()
    await MyBot.dp.storage.wait_closed()
    MyBot.bot.session.close()
    MyBot.bot.close()

    # await reload_and_start_bot_with_bash.reload_bot()


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])
