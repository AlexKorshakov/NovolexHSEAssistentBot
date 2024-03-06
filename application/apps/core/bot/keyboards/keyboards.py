from loader import logger

logger.debug(f"{__name__} start import")

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from apps.core.bot.callbacks.sequential_action.category import ADMIN_MENU_LIST
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import \
    build_inlinekeyboard

logger.debug(f"{__name__} finish import")


class Keyboard:
    btns_dict: dict = {

        'Показать всех пользователей': InlineKeyboardButton(text='Показать всех пользователей',
                                                            callback_data='Показать всех пользователей'),
        'Оповещение': InlineKeyboardButton(text='Оповещение', callback_data='Оповещение'),

        'nav_first': InlineKeyboardButton(text='|<<', callback_data='nav_first'),
        'nav_prev': InlineKeyboardButton(text='<Prev', callback_data='nav_prev'),
        'nav_random': InlineKeyboardButton(text='Rand', callback_data='nav_random'),
        'nav_next': InlineKeyboardButton(text='Next>', callback_data='nav_next'),
        'nav_last': InlineKeyboardButton(text='>>|', callback_data='nav_last'),
        'explain': InlineKeyboardButton(text='Explain', callback_data='explain'),
        'ru': InlineKeyboardButton(text='🇷🇺RU', callback_data='ru'),
        'en': InlineKeyboardButton(text='🇬🇧EN', callback_data='en'),

        'trav_stop': InlineKeyboardButton(text='Stop', callback_data='trav_stop'),
        'trav_step': InlineKeyboardButton(text='Next>', callback_data='trav_step'),
        'trav_ru': InlineKeyboardButton(text='🇷🇺RU', callback_data='trav_ru'),
        'trav_en': InlineKeyboardButton(text='🇬🇧EN', callback_data='trav_en'),

        'subscribe': InlineKeyboardButton(text='🔔Subscribe', callback_data='subscribe'),
        'unsubscribe': InlineKeyboardButton(text='🔕Unsubscribe', callback_data='unsubscribe'),
        'add_lang_btn': InlineKeyboardButton(text='Add 🇷🇺LANG🇬🇧 Button', callback_data='add_lang_btn'),
        'remove_lang_btn': InlineKeyboardButton(text='Remove 🇷🇺LANG🇬🇧 Button', callback_data='remove_lang_btn'),
        'start_xkcding': InlineKeyboardButton(text='Start xkcding!', callback_data='start_xkcding'),
        'continue_xkcding': InlineKeyboardButton(text='Continue xkcding!', callback_data='continue_xkcding'),
        'menu': InlineKeyboardButton(text='Menu', callback_data='menu'),

        'users_info': InlineKeyboardButton(text='USERS\' INFO', callback_data='users_info'),
        'change_spec_status': InlineKeyboardButton(text='CHANGE SPEC STATUS', callback_data='change_spec_status'),
        'send_actions': InlineKeyboardButton(text='SEND ACTLOG', callback_data='send_actions'),
        'send_errors': InlineKeyboardButton(text='SEND ERRLOG', callback_data='send_errors'),
        'broadcast_admin_msg': InlineKeyboardButton(text='BROADCAST', callback_data='broadcast_admin_msg')
    }

    async def _create_keyboard(self, btns_keys: list, row_width: int) -> InlineKeyboardMarkup:
        btns = [self.btns_dict[key] for key in btns_keys]
        keyboard = InlineKeyboardMarkup(row_width=row_width)
        keyboard.add(*btns)

        return keyboard

    async def admin_panel(self) -> InlineKeyboardMarkup:
        return await build_inlinekeyboard(some_list=ADMIN_MENU_LIST, num_col=1, level=1)


kboard = Keyboard()
