from __future__ import annotations

from loader import logger

logger.debug(f"{__name__} start import")
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.data.board_config import BoardConfig as board_config
from apps.core.bot.messages.messages import Messages
from apps.core.bot.reports.report_data import (global_reg_form,
                                               headlines_data,
                                               user_data)
from apps.core.utils.misc import rate_limit
from apps.MyBot import MyBot, bot_send_message
from config.config import ADMIN_ID

logger.debug(f"{__name__} finish import")


class NamedDict(dict):
    def __init__(self, *args, **kwargs):
        try:
            self._name = kwargs.pop('name')
        except KeyError:
            raise KeyError('a "name" keyword argument must be supplied')
        super(NamedDict, self).__init__(*args, **kwargs)

    @classmethod
    def fromkeys(cls, name, seq, value=None):
        return cls(dict.fromkeys(seq, value), name=name)

    @property
    def name(self):
        return self._name


@rate_limit(limit=5)
@MyBot.dp.message_handler(Command('cancel'), state='*')
@MyBot.dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, user_id: int | str = None, state: FSMContext = None):
    """Корректирование уже введённых значений на локальном pc и на google drive

    :return:
    """
    try:
        user_id = message.chat.id if message else user_id
    except AttributeError:
        user_id = message.message.chat.id if message else user_id

    if not await check_user_access(chat_id=user_id):
        return

    dict_list = [
        NamedDict.fromkeys('user_data', user_data),
        NamedDict.fromkeys('global_reg_form', global_reg_form),
        NamedDict.fromkeys('headlines_data', headlines_data)
    ]

    for items_data in dict_list:
        items_data_name = list(items_data.keys())
        logger.debug(f"Report {str(items_data.name)} {items_data}")
        if items_data_name:
            items_data.clear()
            logger.info(f"Report is clear {str(items_data.name)} {items_data}")

    await board_config(state, "menu_level", 1).set_data()
    await board_config(state, "menu_list", []).set_data()
    await board_config(state, "violation_menu_list", []).set_data()
    await board_config(state, "violation_file", []).set_data()
    await board_config(state, "previous_level", '').set_data()
    await board_config(state, "current_file", 'None').set_data()

    await bot_send_message(chat_id=user_id, text=Messages.all_canceled)
    await bot_send_message(chat_id=ADMIN_ID, text=f'cancel_all from {user_id}')

    current_state = await state.get_state()
    logger.info(f'Cancelling state {current_state}')
    await state.finish()
    if current_state is None:
        logger.info(f'Cancelling state {current_state}')
        return

    await state.finish()
