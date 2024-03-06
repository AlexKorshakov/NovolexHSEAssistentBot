from loader import logger

logger.debug(f"{__name__} start import")
from apps.MyBot import MyBot

logger.debug(f"{__name__} finish import")


@MyBot.dp.errors_handler()
async def errors_handler(update, exception):
    """
    Exceptions handler. Catches all exceptions within task factory tasks.
    :param update:
    :param exception:
    :return: stdout logging
    """
    from aiogram.utils.exceptions import (CantDemoteChatCreator,
                                          CantParseEntities, InvalidQueryID,
                                          MessageCantBeDeleted,
                                          MessageNotModified,
                                          MessageTextIsEmpty,
                                          MessageToDeleteNotFound, RetryAfter,
                                          TelegramAPIError, Unauthorized, NetworkError)

    if isinstance(exception, NetworkError):
        logger.error("Cannot connect to host api.telegram.org:443 ssl:default [getaddrinfo failed]")
        return True

    if isinstance(exception, CantDemoteChatCreator):
        logger.debug("Can't demote chat creator")
        return True

    if isinstance(exception, MessageNotModified):
        logger.debug('Message is not modified')
        return True

    if isinstance(exception, MessageCantBeDeleted):
        logger.debug('Message cant be deleted')
        return True

    if isinstance(exception, MessageToDeleteNotFound):
        logger.debug('Message to delete not found')
        return True

    if isinstance(exception, MessageTextIsEmpty):
        logger.debug('MessageTextIsEmpty')
        return True

    if isinstance(exception, Unauthorized):
        logger.info(f'Unauthorized: {exception}')
        return True

    if isinstance(exception, InvalidQueryID):
        logger.exception(f'InvalidQueryID: {exception} \nUpdate: {update}')
        return True

    if isinstance(exception, TelegramAPIError):
        logger.exception(f'TelegramAPIError: {exception} \nUpdate: {update}')
        return True

    if isinstance(exception, RetryAfter):
        logger.exception(f'RetryAfter: {exception} \nUpdate: {update}')
        return True

    if isinstance(exception, CantParseEntities):
        logger.exception(f'CantParseEntities: {exception} \nUpdate: {update}')
        return True

    logger.exception(f'Update: {update} \n{exception}')
