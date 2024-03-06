from __future__ import annotations

import traceback

from aiogram.dispatcher import FSMContext

from apps.core.bot.filters.custom_filters import filter_is_private
from loader import logger

logger.debug(f"{__name__} start import")

import asyncio
from pprint import pprint

from aiogram import types
from aiogram.dispatcher.filters import Command

from apps.MyBot import MyBot, bot_send_message
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.messages.messages import Messages
from apps.core.bot.messages.messages_test import msg
from apps.core.settyngs import get_sett
from apps.core.utils.misc import rate_limit

logger.debug(f"{__name__} finish import")


class CatalogSpot(object):

    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

    def __init__(self):
        self.catalog_spot_data: dict[str, str] = {}

    def _print(self):
        pprint(self._catalog_spot_data)

    @property
    def catalog_spot_data(self):
        return self._catalog_spot_data

    @catalog_spot_data.setter
    def catalog_spot_data(self, value):
        self._catalog_spot_data = value
        if value == {}:
            return
        self._print()


catalog_spot_data = CatalogSpot().catalog_spot_data


@rate_limit(limit=10)
@MyBot.dp.message_handler(Command('catalog'), filter_is_private, state='*')
async def catalog_func_handler(message: types.Message = None, user_id: str | int = None, state: FSMContext = None):
    """Обработка команд генерации документов

    :return:
    """
    if message.chat.type in ['group', 'supergroup']:
        return
    # if message.from_user.id not in [member.user.id for member in await message.chat.get_administrators()]:
    #     return
    try:
        hse_user_id = message.chat.id if message else user_id
    except AttributeError as err:
        logger.debug(f'{__file__} {repr(err)}')
        hse_user_id = user_id if user_id else message.message.from_user.id

    current_state = await state.get_state()
    await state.finish()
    logger.info(f'{await fanc_name()} state is finish {current_state = }')

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    if not get_sett(cat='enable_features', param='use_catalog_func').get_set():
        msg_text: str = f"{await msg(hse_user_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=hse_user_id, text=msg_text, disable_web_page_preview=True)
        return

    reply_markup = await add_correct_inline_keyboard_with_action()
    text: str = 'Выберите действие'

    await bot_send_message(chat_id=hse_user_id, text=text, reply_markup=reply_markup)


async def add_correct_inline_keyboard_with_action():
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """

    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            text='Справочник сотрудников',
            callback_data=posts_cb.new(id='-', action='catalog_employee')
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            text='Справочник нормативных документов',
            callback_data=posts_cb.new(id='-', action='catalog_normative_documents')
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            text='Справочник ЛНА',
            callback_data=posts_cb.new(id='-', action='catalog_lna')
        )
    )

    return markup


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])


async def test():
    """test"""

    call: types.CallbackQuery = None
    user_id = 373084462
    await catalog_func_handler(call=call, user_id=user_id)


if __name__ == '__main__':
    asyncio.run(test())
