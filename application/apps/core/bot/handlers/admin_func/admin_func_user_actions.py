from __future__ import annotations

from aiogram import types
from aiogram.dispatcher import FSMContext

from apps.MyBot import MyBot, bot_send_message
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.filters.custom_filters import is_admin_user_actions
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import posts_cb
from apps.core.bot.messages.messages import Messages
from apps.core.bot.messages.messages_test import msg
from apps.core.settyngs import get_sett
from loader import logger


@MyBot.dp.callback_query_handler(is_admin_user_actions, state='*')
async def admin_user_actions_answer(call: types.CallbackQuery, callback_data: dict[str, str] = None,
                                    state: FSMContext = None, user_id: int | str = None):
    """
    :return:
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {call.data = }')

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    if not get_sett(cat='enable_features', param='use_admin_add_user').get_set():
        msg_text: str = f"{await msg(hse_user_id, cat='error', msge='features_disabled', default=Messages.Error.features_disabled).g_mas()}"
        await bot_send_message(chat_id=hse_user_id, text=msg_text, disable_web_page_preview=True)
        return

    user_for_action = call.data.split(':')[-1].replace('admin_user_actions_', '')
    print(f'{user_for_action = }')

    main_reply_markup = types.InlineKeyboardMarkup()
    # hse_role_df: DataFrame = await get_role_receive_df()

    # if not await check_user_access(chat_id=chat_id, role_df=hse_role_df):
    #     logger.error(f'access fail {chat_id = }')
    #     return

    main_reply_markup = await add_inline_keyboard_with_action_for_admin(main_reply_markup, user_for_action)

    await bot_send_message(chat_id=hse_user_id, text=Messages.Choose.action, reply_markup=main_reply_markup)


async def add_inline_keyboard_with_action_for_admin(markup: types.InlineKeyboardMarkup, user_for_action):
    """Формирование сообщения с текстом и кнопками действий в зависимости от параметров

    :return:
    """

    if not markup:
        markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(
        text='добавить пользователя',
        callback_data=posts_cb.new(id='-', action=f'admin_add_user_{user_for_action}'))
    )
    return markup
