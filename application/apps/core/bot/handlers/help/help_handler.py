import traceback
from pprint import pprint

from aiogram.dispatcher import FSMContext

from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.messages.messages import Messages
from apps.core.settyngs import get_sett
from loader import logger

logger.debug(f"{__name__} start import")
from aiogram import types
from aiogram.dispatcher.filters import Command
from aiogram.utils.markdown import text
from apps.core.bot.keyboards.inline.help_inlinekeyboard import help_inline_button
from apps.core.bot.messages.messages_test import msg
from apps.core.utils.misc import rate_limit
from apps.MyBot import MyBot, bot_send_message

logger.debug(f"{__name__} finish import")


@rate_limit(limit=10)
@MyBot.dp.message_handler(Command('help'), state='*')
async def help_command_handler(message: types.Message, state: FSMContext = None):
    """Обработка команды help
    """
    chat_id = message.chat.id
    if not await check_user_access(chat_id=chat_id):
        return

    current_state = await state.get_state()
    await state.finish()

    if not get_sett(cat='enable_features', param='use_help_command_handler').get_set():
        msg_text: str = f"{await msg(chat_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=chat_id, text=msg_text, disable_web_page_preview=True)
        return

    answer_text = f"{await msg(chat_id, cat='help', msge='bot_developer', default='Меня создал').g_mas()}"
    await bot_send_message(chat_id=chat_id, text=answer_text)

    help_message = text(
        f"{await msg(chat_id, cat='help', msge='command_help', default='Справка по командам').g_mas()}"
        "\n",
        f"/developer - {await msg(chat_id, cat='help', msge='developer', default='Написать разработчику').g_mas()}",
        f"/cancel- {await msg(chat_id, cat='help', msge='cancel', default='Отмена всех действий').g_mas()}",
        f"/generate - {await msg(chat_id, cat='help', msge='generate', default='Формирование документов').g_mas()}",
        f"/start - {await msg(chat_id, cat='help', msge='start', default='Начало работы').g_mas()}",
        # f"/correct_entries - {await msg(hse_id, cat='help', msge='correct_entries', default='Корректирование введённых значений').g_mas()}",
        f"/admin_func - {await msg(chat_id, cat='help', msge='admin_func', default='Функции администратора').g_mas()}",
        "\n"
        f"{await msg(chat_id, cat='help', msge='video_instruction', default='Видео инструкция').g_mas()}",
        sep="\n"
    )

    await bot_send_message(chat_id=chat_id, text=help_message, reply_markup=await help_inline_button(hse_id=chat_id))


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])
