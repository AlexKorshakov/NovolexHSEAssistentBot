import os
import asyncio

import subprocess
from pathlib import Path
from psutil import Process, NoSuchProcess
from application.loader import logger

DELAY: int = 5


async def load_bot(bot_path: str = '') -> None:
    """Запуск бота в цикле с помощью .bat"""
    logger.info(f'{bot_path = }')
    prog = await start_bot()

    bot_is_work: bool = True
    try:
        while bot_is_work:
            await asyncio.sleep(DELAY)
            trigger: str = await get_trigger(bot_path)

            if trigger == 'reload':
                await del_trigger(bot_path)
                await kill_bot(prog)
                await asyncio.sleep(DELAY)
                prog = await start_bot()

            elif trigger == 'stop':
                await del_trigger(bot_path)
                await asyncio.sleep(DELAY)
                bot_is_work = False

    except Exception as err:
        logger.error(f'{repr(err)}')
        await kill_bot(prog)
        prog = await start_bot()
        # await load_bot()

    finally:
        await del_trigger(bot_path)
        await kill_bot(prog)


async def start_bot() -> subprocess.Popen:
    """Запуск процесса бота из .bat"""
    proc_path: str = str(Path(__file__).resolve().parent)
    proc_path_file: str = str(Path(proc_path, "Bot_Run.bat"))

    process: subprocess.Popen = subprocess.Popen(
        [proc_path_file, '-m'],
        # "MyBot_Run.bat",
        # stdout=subprocess.PIPE,
        # stderr=subprocess.PIPE,
        shell=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    logger.info(f'load_bot {process.pid = } ')
    return process


async def kill_bot(proc):
    """Остановка процесса бота и всех дочерних процессов"""
    pobj = Process(proc.pid)

    try:
        for children in pobj.children(recursive=True):  # list children & kill them
            try:
                children.kill()
                logger.info(f'{children = }')
            except NoSuchProcess:
                logger.info('NoSuchProcess')

        pobj.kill()
        logger.info('all children processes kill')

    except Exception as err:
        logger.error(f'{repr(err)}')
        logger.info("taskkill /f /im Bot_Run.bat")


async def get_trigger(bot_path: str = '') -> str:
    """Получение команды из имени файла-триггера"""
    trigger_file: list = [file.split('_')[-1] for file in await get_trigger_file(bot_path) if isinstance(file, str)]
    return trigger_file[-1] if trigger_file else ''


async def del_trigger(bot_path: str = ''):
    """Удаление файла-триггера"""
    for trigger_file in await get_trigger_file(bot_path):
        try:
            logger.info(f'{trigger_file = }')
            os.remove(Path(bot_path, trigger_file))

        except FileNotFoundError as err:
            logger.error(f'{trigger_file = } {repr(err)}')
            continue

    return True


async def get_trigger_file(trigger_path: str) -> list:
    """Получение триггеров"""
    dir_files = Path(trigger_path).iterdir() if trigger_path else Path('.').iterdir()
    return [str(item) for item in list(dir_files) if 'trigger_' in str(item)]


if __name__ == '__main__':
    asyncio.run(load_bot(bot_path=''))
