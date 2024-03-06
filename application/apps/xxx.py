from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config.config import BOT_TOKEN

assistant = Bot(token=BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()

dp_assistant = Dispatcher(bot=assistant, storage=storage)
