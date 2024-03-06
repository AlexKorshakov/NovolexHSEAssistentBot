from aiogram import Dispatcher
from aiogram.types import Message
from config.apps import INSTALLED_APPS

from .. import services
from ...MyBot import bot_send_message


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start, commands=["start"])
    dp.register_message_handler(send_my_id, commands=["id"])
    dp.register_message_handler(send_my_apps, commands=["apps"])
    dp.register_message_handler(simple_handler, commands=["core"])


async def start(message: Message):
    chat_id = message.chat.id
    user, is_created = await services.add_user(
        tg_id=message.from_user.id,
        chat_id=message.chat.id,
        first_name=message.from_user.first_name,
    )

    if is_created:
        await bot_send_message(chat_id=chat_id, text="You have successfully registered in the bot!")
    else:
        await bot_send_message(chat_id=chat_id, text="You are already registered in the bot!")


async def send_my_id(message: Message):
    chat_id = message.chat.id
    await bot_send_message(chat_id=chat_id, text=f"User Id: <b>{message.from_user.id}</b>\n "
                                                 f"Chat Id: <b>{message.chat.id}</b>")


async def send_my_apps(message: Message):
    chat_id = message.chat.id

    # apps_names = ""
    # for app in INSTALLED_APPS:
    #     apps_names += app.Config.name + "\n"

    apps_names = ' \n'.join(app.Config.name for app in INSTALLED_APPS if app is not None)

    await bot_send_message(chat_id=chat_id, text="Installed apps:\n" f"{apps_names}")


async def simple_handler(message: Message):
    chat_id = message.chat.id
    await bot_send_message(chat_id=chat_id, text='Hello from "Core" app!')
