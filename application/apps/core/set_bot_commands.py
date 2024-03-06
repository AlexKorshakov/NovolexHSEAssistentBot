from aiogram import Dispatcher, types
from apps.core.bot.messages.messages import Messages
from loader import logger


async def set_default_commands(dp: Dispatcher):
    await dp.bot.set_my_commands(
        [
            types.BotCommand(command="/start", description="Начало работы"),
            types.BotCommand(command="/generate", description="Формирование документов"),
            types.BotCommand(command="/developer", description="Написать разработчику"),
            types.BotCommand(command="/help", description="Вызов справки"),
            types.BotCommand(command="/cancel", description="Отмена всех действий"),
            # types.BotCommand(command="/correct_entries", description="Изменение данных"),
            # types.BotCommand(command="/catalog", description="Справочник"),
            # types.BotCommand(command="/bagration", description="Багратион"),
            # types.BotCommand(command="/add_entries", description="Добавление данных"),
            types.BotCommand(command="/admin_func", description="Админка"),
            # types.BotCommand(command="/super_user_fanc", description="Админка2"),
            # types.BotCommand(command="/test_command", description="тестовые функции"),
            # types.BotCommand(command="/send_mail", description="Отправка отчета"),
        ]
    )
    logger.info(f'{dp.bot._me.first_name} {Messages.bot_setting_commands}')
