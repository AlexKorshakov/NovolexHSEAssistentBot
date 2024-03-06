from aiogram.dispatcher.filters.state import StatesGroup, State

from loader import logger

logger.debug(f"{__name__} start import")

from pprint import pprint

logger.debug(f"{__name__} finish import")


class Report(object):

    def __init__(self, name=None):
        self.report_data: dict[str, str] = {}
        self.name = name

    def _print(self):
        pprint(self._report_data)

    @property
    def report_data(self):
        return self._report_data

    @report_data.setter
    def report_data(self, value):
        self._report_data = value
        if value == {}:
            return
        self._print()


# violation_data = Report().report_data
user_data = Report().report_data
global_reg_form = Report().report_data
headlines_data = Report().report_data


class ViolationData(StatesGroup):
    starting = State()

    main_location = State()
    sub_location = State()

    description = State()
    comment = State()
    location = State()

    inquiry = State()

    equipment_folder = State()
    equipment_doc = State()

    add_many_photo = State()
    finish = State()
    add_act_number = State()


class QRData(StatesGroup):
    inquiry = State()

    equipment_folder = State()
    equipment_doc = State()
