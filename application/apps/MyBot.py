from __future__ import annotations

import asyncio
import sys
import traceback
from pprint import pprint

import aiohttp
import nest_asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatActions, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
from aiogram.utils import executor
from aiogram.utils.exceptions import MessageNotModified, MessageToEditNotFound

from apps.core.bot.messages.messages import Messages
from apps.core.bot.messages.messages_test import msg
from apps.core.bot.middlewares import setup_middlewares
from apps.core.set_bot_commands import set_default_commands
from apps.core.settyngs import get_sett
from apps.notify_admins import on_startup_notify_admins
from apps.xxx import assistant, dp_assistant
from config.config import SKIP_UPDATES
from loader import logger

nest_asyncio.apply()


# import heartrate
# heartrate.trace(browser=True)

def generate_payload(exclude: list = None, **kwargs) -> dict:
    """Generate payload
    Usage: payload = generate_payload(**locals(), exclude=['foo'])

    :param exclude: List
    :param kwargs: dict
    :return: dict
    """
    DEFAULT_FILTER = ['self', 'cls']

    if exclude is None:
        exclude = []

    return {key: value for key, value in kwargs.items() if
            key not in exclude + DEFAULT_FILTER
            and value is not None
            and not key.startswith('_')}


async def bot_send_document(*, chat_id: int | str, doc_path: str, caption: str = None, calling_fanc_name: str = None,
                            **kvargs: dict) -> bool:
    """Функция отправки документов

    :param calling_fanc_name: str
    :param caption: str
    :param chat_id: int
    :param doc_path: str
    :param kvargs: dict
    :return:
    """
    await MyBot.bot.send_chat_action(chat_id=chat_id, action=ChatActions.UPLOAD_DOCUMENT)
    await asyncio.sleep(2)  # скачиваем файл и отправляем его пользователю

    try:
        with open(file=doc_path, mode='rb') as doc:
            result: types.Message | None = await MyBot.bot.send_document(
                    chat_id=chat_id, document=doc, caption=caption, **kvargs
            )

        logger.info(f"{await MyBot.get_name()} {chat_id = } {calling_fanc_name} {caption} отправлен отчет {doc}")

    except OSError as err:
        logger.error(f"{await MyBot.get_name()} {calling_fanc_name} {repr(err)}")
        return False

    except Exception as err:
        logger.error(f"{await MyBot.get_name()} {calling_fanc_name} {repr(err)}")
        return False

    if result:
        return True
    return False


async def bot_send_photo(*, chat_id: int | str, photo=None, caption: str = None) -> bool:
    """Используйте этот метод для отправки текстовых сообщений.
    Источник: https://core.telegram.org/bots/api#sendmessage

    """
    await MyBot.bot.send_chat_action(chat_id=chat_id, action=ChatActions.UPLOAD_PHOTO)
    await asyncio.sleep(2)  # скачиваем файл и отправляем его пользователю

    try:
        result: types.Message | None = await MyBot.bot.send_photo(
                chat_id=chat_id, photo=photo, caption=caption
        )

    except OSError as err:
        logger.error(f"{await MyBot.get_name()}  {repr(err)}")
        return False

    except Exception as err:
        logger.warning(f'{await MyBot.get_name()} {chat_id = } {repr(err)}')
        return False

    if result:
        return True
    return False


class MyBot:
    """Основной класс запуска бота

    """
    bot = assistant
    dp = dp_assistant

    Bot.set_current(bot)
    Dispatcher.set_current(dp)
    # name = 'STNGBot'
    __instance = None

    def __new__(cls, val):
        if MyBot.__instance is None:
            MyBot.__instance = object.__new__(cls)
        MyBot.__instance.val = val
        return MyBot.__instance

    @classmethod
    async def get_name(cls):
        try:
            first_name = cls.dp.bot._me.first_name
            return first_name

        except AttributeError as err:
            logger.error(f'{__name__} {await fanc_name()} {repr(err)}')
            return ''

    @classmethod
    async def run(cls):
        """Сборка и запуск бота"""
        try:
            await executor.start_polling(
                    dispatcher=cls.dp,
                    on_startup=cls.on_startup,
                    on_shutdown=cls.on_shutdown,
                    timeout=200,
                    skip_updates=SKIP_UPDATES,
                    allowed_updates=await cls.get_handled_updates_list(cls.dp)
            )
        except RuntimeWarning as err:
            logger.error(f"Bot start RuntimeWarning {repr(err)}")

        except aiohttp.client_exceptions.ClientConnectorError as err:
            logger.error(f"Bot start ClientConnectorError {repr(err)}")

        except Exception as err:
            logger.error(f"Bot start Exception {repr(err)}")

        finally:
            # with suppress(RuntimeWarning, DeprecationWarning):
            await cls.dp.storage.close()
            await cls.dp.storage.wait_closed()
            # session = await cls.dp.get_session()
            # session.close()

    @staticmethod
    async def on_startup(dp: Dispatcher):
        logger.info(f"{dp.bot._me.first_name} started Установка обработчиков...")
        print(f"{dp.bot._me.first_name} Установка обработчиков...")
        try:
            import apps.core.bot.filters
            import apps.core.bot.callbacks
            import apps.core.bot.handlers
            logger.info(f"{dp.bot._me.first_name} Все части зарегистрированы...")

        except Exception as err:
            logger.warning(f'{dp.bot._me.first_name} Exception in app.py {err}')
            sys.exit()

        await setup_middlewares(dp)
        await on_startup_notify_admins(dp)
        await set_default_commands(dp)

        on_startup_text: str = f'{dp.bot._me.first_name} {Messages.Successfully.bot_start}'
        logger.info(on_startup_text)
        print(on_startup_text)

        # await register_apps(dp)

    @staticmethod
    async def get_handled_updates_list(dp: Dispatcher):
        """
        Here we collect only the needed updates for bot based on already registered handlers types.
        This way Telegram doesn't send unwanted updates and bot doesn't have to proceed them.

        Здесь мы собираем только необходимые обновления для бота на основе уже зарегистрированных типов обработчиков.
        Таким образом, Telegram не отправляет нежелательные обновления, и боту не нужно их обрабатывать.
        :param dp: Dispatcher
        :return: a list of registered handlers types
        """
        available_updates = (
            "callback_query_handlers",
            "channel_post_handlers",
            "chat_member_handlers",
            "chosen_inline_result_handlers",
            "edited_channel_post_handlers",
            "edited_message_handlers",
            "inline_query_handlers",
            "message_handlers",
            "my_chat_member_handlers",
            "poll_answer_handlers",
            "poll_handlers",
            "pre_checkout_query_handlers",
            "shipping_query_handlers",
        )
        return [item.replace("_handlers", "") for item in available_updates
                if len(dp.__getattribute__(item).handlers) > 0]

    @staticmethod
    async def on_shutdown(dp: Dispatcher):
        logger.warning('Bye! Shutting down connection')
        logger.warning(f'{dp.bot._me.first_name} Bye! Shutting down connection')

        payload: dict = generate_payload(**locals())
        pprint(f'{__file__} {await fanc_name()} {payload = }', width=200)

        state = dp.get_current().current_state(user=373084462)
        v_data: dict = await state.get_data()
        pprint(f'{__file__} {await fanc_name()} {v_data = }', width=200)

        session = await dp.bot.get_session()
        pprint(f'{__file__} {await fanc_name()} {session = }', width=200)

        # await MyBot.loop.run_in_executor(None, input)

        dp.stop_polling()
        await dp.storage.close()

    @staticmethod
    async def get_user_ids(dp: Dispatcher, chat_id: int | str) -> list:
        """Получение списка участников чата chat_id

        :param dp:
        :param chat_id:
        :return:
        """
        chat_members = await dp.bot.get_chat_members_count(chat_id)
        user_ids: list = [member.user.id for member in chat_members]
        return user_ids


async def bot_send_message(
        *,
        chat_id: int | str,
        text: str,
        reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | ReplyKeyboardRemove | ForceReply | None = None,
        **kvargs
) -> bool:
    """Используйте этот метод для отправки текстовых сообщений.
    Источник: https://core.telegram.org/bots/api#sendmessage

    """
    try:
        result: types.Message | None = await _send_message(
                chat_id=chat_id, text=text, reply_markup=reply_markup, **kvargs
        )

    except AttributeError as err:
        logger.warning(f'{await MyBot.get_name()} {chat_id = } {repr(err)}')
        return False

    if result:
        return True
    return False


async def _send_message(*, chat_id: int | str, text: str,
                        reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | ReplyKeyboardRemove | ForceReply | None = None,
                        **kvargs) -> types.Message | None:
    """Отправка сообщения

    :param chat_id:
    :param text:
    :param reply_markup:
    :param kvargs:
    :return:
    """
    try:
        result: types.Message | None = await MyBot.bot.send_message(
                chat_id=chat_id, text=text, reply_markup=reply_markup, **kvargs
        )
        return result

    except Exception as err:
        logger.error(f'{await MyBot.get_name()} {chat_id = } {repr(err)}')
        return None


async def bot_edit_message(*, hse_user_id: int, message_id: int, reply_text: str,
                           reply_markup: InlineKeyboardMarkup = None, **kvargs: dict) -> bool:
    """Изменение сообщения по message_id

    :return:
    """
    # pprint(f'{__name__} {await fanc_name()} {kvargs = }', width=200)

    result: bool = await MyBot.bot.edit_message_text(
            chat_id=hse_user_id,
            text=reply_text,
            message_id=message_id,
            reply_markup=reply_markup
    )

    return result


async def bot_delete_message(*, chat_id: int | str, message_id: int | str, sleep_sec: int = 5) -> bool:
    """Используйте этот метод для удаления сообщения, в том числе служебного, со следующими ограничениями:
         - Сообщение может быть удалено только в том случае, если оно было отправлено менее 48 часов назад.
         - Боты могут удалять исходящие сообщения в приватных чатах, группах и супергруппах.
         - Боты могут удалять входящие сообщения в приватных чатах.
         - Боты с разрешениями can_post_messages могут удалять исходящие сообщения в каналах.
         - Если бот является администратором группы, он может удалить там любое сообщение.
         - Если у бота есть разрешение can_delete_messages в супергруппе или канале, он может удалить там любое сообщение.
    Источник: https://core.telegram.org/bots/api#deletemessage

        :param sleep_sec:
        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param message_id: Identifier of the message to delete
        :type message_id: :obj:`base.Integer`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
    :return:
    """
    if not get_sett(cat='enable_features', param='bot_delete_message').get_set():
        msg_text: str = await msg(chat_id, cat='error', msge='features_disabled',
                                  default=Messages.Error.features_disabled).g_mas()
        logger.warning(f'{await MyBot.get_name()} {chat_id = } {msg_text = }')
        return False

    if sleep_sec:
        await asyncio.sleep(sleep_sec)

    try:
        result: types.Message | None = await MyBot.bot.delete_message(chat_id=chat_id, message_id=message_id)

    except Exception as err:
        logger.warning(f'{await MyBot.get_name()} {chat_id = } {repr(err)}')
        return False

    if result:
        return True
    return False


async def bot_delete_markup(message: types.Message, sleep_sec: int = None):
    """Удаление клавиатуры сообщения

    :param sleep_sec:
    :param message:
    :return:
    """
    # удаляем кнопки у последнего сообщения
    chat_id = message.chat.id

    if sleep_sec:
        await asyncio.sleep(sleep_sec)

    try:
        result = await MyBot.bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=message.message_id - 1,
                reply_markup=None
        )
    except MessageNotModified as err:
        logger.warning(f'{await MyBot.get_name()} {chat_id = } {repr(err)}')
        return False

    except MessageToEditNotFound as err:
        logger.warning(f'{await MyBot.get_name()} {chat_id = } {repr(err)}')
        return False

    except Exception as err:
        logger.warning(f'{await MyBot.get_name()} {chat_id = } {repr(err)}')
        return False

    if result:
        return True
    return False


async def notify_user_for_choice(call_msg: types.CallbackQuery | types.Message, user_id: int | str = None,
                                 data_answer: str = None) -> bool:
    """Уведомление пользователя о выборе + логирование

    :param data_answer:
    :param user_id: int | str id пользователя
    :param call_msg:
    :return None :
    """
    if isinstance(call_msg, types.CallbackQuery):
        for i in ('previous_paragraph', 'move_up', 'move_down'):
            if i in call_msg.data: return True

        mesg_text: str = f"Выбрано: {data_answer}"
        if call_msg.data in call_msg.message.text:
            mesg_list: list = [item for item in call_msg.message.text.split('\n\n') if call_msg.data in item]
            mesg_text = f"Выбрано: {mesg_list[0]}"

        try:
            hse_user_id = call_msg.message.chat.id if call_msg else user_id
            logger.debug(f"{hse_user_id = } Выбрано: {data_answer} {call_msg.data}")
            await call_msg.message.edit_text(text=mesg_text, reply_markup=None)
            return True

        except Exception as err:
            logger.debug(f"{call_msg.message.chat.id = } {repr(err)}")

    if isinstance(call_msg, types.Message):
        for i in ('previous_paragraph', 'move_up', 'move_down'):
            if i in call_msg.text: return True

        mesg_text: str = f"Выбрано: {data_answer}"
        if call_msg.text:
            mesg_list: list = [item for item in call_msg.text.split('\n\n') if call_msg.text in item]
            mesg_text = f"Выбрано: {mesg_list[0] if mesg_list else ''}"

        try:
            hse_user_id = call_msg.chat.id if call_msg else user_id
            logger.debug(f"{hse_user_id = } Выбрано: {data_answer} {call_msg.text}")
            await call_msg.edit_text(text=mesg_text, reply_markup=None)
            return True

        except Exception as err:
            logger.debug(f"{call_msg.chat.id = } {repr(err)}")


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])


async def test():
    try:
        my_bot_task = asyncio.create_task(MyBot.run(), name='MyBot.run')
        await my_bot_task

    except KeyboardInterrupt as err:
        logger.error(f'Error run_app {repr(err)}')
        sys.exit(0)


if __name__ == '__main__':
    asyncio.run(test())
