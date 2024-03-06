import sys
import asyncio

from loader import logger

logger.info('start app load')


async def run_app():
    try:
        from apps.MyBot import MyBot
        # from apps.MyServer import MyServer
        # from apps.PeriodicCheck import PeriodicCheck

        my_bot_task = asyncio.create_task(MyBot.run(), name='MyBot.run')
        # my_server_task = asyncio.create_task(MyServer.run(), name='MyServer.run')
        # periodic_check_task = asyncio.create_task(PeriodicCheck.run(), name='PeriodicCheck.run')

        await my_bot_task
        # await my_server_task
        # await periodic_check_task

    except KeyboardInterrupt as err:
        logger.error(f'Error run_app {repr(err)}')
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(run_app())
