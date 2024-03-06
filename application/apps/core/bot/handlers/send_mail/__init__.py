from loader import logger

logger.debug(f"{__name__} start import")

from . import send_mail_handler

logger.debug(f"{__name__} finish import")
