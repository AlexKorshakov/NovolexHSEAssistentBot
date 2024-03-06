from loader import logger
logger.debug(f"{__name__} finish import")

from aiogram import types
from aiogram.dispatcher import FSMContext

from apps.MyBot import MyBot, bot_send_message
from apps.core.bot.callbacks.callback_action import cb_start
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.data.board_config import BoardConfig as board_config
from apps.core.bot.messages.messages import Messages
from apps.core.bot.reports.report_data import (ViolationData,
                                               user_data,
                                               global_reg_form,
                                               headlines_data)

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


@MyBot.dp.callback_query_handler(cb_start.filter(action=['select_abort_registration']), state=ViolationData.all_states)
async def callbacks_num_finish_fab(call: types.CallbackQuery, state: FSMContext):
    """Действия при отмене регистрации
    """
    logger.info(f'User @{call.message.chat.username}:{call.message.chat.id} регистрация отменена')

    chat_id = call.from_user.id
    if not await check_user_access(chat_id=chat_id):
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
    await board_config(state, "current_file", None).set_data()

    await bot_send_message(chat_id=chat_id, text=Messages.all_canceled)

    current_state = await state.get_state()
    logger.info(f'Cancelling state {current_state}')
    await state.finish()
    if current_state is None:
        logger.info(f'Cancelling state {current_state}')
        return

    await state.finish()
