from loader import logger

logger.debug(f"{__name__} start import")

from . import photo_handler

logger.debug(f"{__name__} finish import")
