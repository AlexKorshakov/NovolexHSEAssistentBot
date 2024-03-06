from __future__ import annotations

from aiogram import types
from aiogram.dispatcher import FSMContext

from apps.MyBot import MyBot, bot_send_message
from apps.core.bot.bot_utils.check_access import check_super_user_access, check_user_access
from apps.core.bot.filters.custom_filters import filter_is_super_user
from apps.core.bot.handlers.bagration.bagration_utils import DataBaseEmployeeID
from apps.core.bot.handlers.catalog.catalog_support import DataBaseCatalogEmployee

from apps.core.bot.handlers.photo.qr_personal_id_processing import DataBaseSubconEmployeeID
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages_test import DataBaseMSG

from apps.core.checker.check_utils import DataBaseForCheck
from apps.core.checker.periodic_check_data_base import DataBaseForPeriodicCheck
from apps.core.database.ViolationsDataBase import DataBaseViolations
from apps.core.settyngs import DataBaseSettings

from apps.core.utils.misc import rate_limit
from apps.notify_admins import DataBaseAccessToAdmins
from loader import logger


@rate_limit(limit=2)
@MyBot.dp.callback_query_handler(posts_cb.filter(action=['s_user_backup_all_databases']), filter_is_super_user,
                                 state='*')
async def call_s_user_backup_all_databases(call: types.CallbackQuery, callback_data: dict[str, str] = None,
                                                  state: FSMContext = None):
    """Обработка ответов содержащихся в s_user_backup_all_databases
    """
    hse_user_id = call.message.chat.id
    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    if not await check_super_user_access(chat_id=hse_user_id):
        logger.error(f'check_super_user_access fail {hse_user_id = }')
        return

    result_list: list = []
    result = await DataBaseSettings().create_backup()
    print(f'{DataBaseSettings().name} {result = }')
    result_list.append(result)

    result = await DataBaseViolations().create_backup()
    print(f'{DataBaseViolations().name} {result = }')
    result_list.append(result)

    result = await DataBaseForCheck().create_backup()
    print(f'{DataBaseForCheck().name} {result = }')
    result_list.append(result)

    result = await DataBaseForPeriodicCheck().create_backup()
    print(f'{DataBaseForPeriodicCheck().name} {result = }')
    result_list.append(result)

    result = await DataBaseEmployeeID().create_backup()
    print(f'{DataBaseEmployeeID().name} {result = }')
    result_list.append(result)

    result = await DataBaseSubconEmployeeID().create_backup()
    print(f'{DataBaseSubconEmployeeID().name} {result = }')
    result_list.append(result)

    result = await DataBaseAccessToAdmins().create_backup()
    print(f'{DataBaseAccessToAdmins().name} {result = }')
    result_list.append(result)

    result = await DataBaseMSG().create_backup()
    print(f'{DataBaseMSG().name} {result = }')
    result_list.append(result)

    result = await DataBaseCatalogEmployee().create_backup()
    print(f'{DataBaseCatalogEmployee().name} {result = }')
    result_list.append(result)

    result_list = list(set((item for item in [item for item in result_list if item is not None])))

    logger.info(f'for bd create backup {result_list = }')

    result_list_text = ", \n".join(result_list)
    await bot_send_message(chat_id=hse_user_id, text=f'backup created for:\n{result_list_text}')

    return result_list
