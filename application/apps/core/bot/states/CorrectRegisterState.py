from aiogram.dispatcher.filters.state import State, StatesGroup


class CorrectRegisterState(StatesGroup):
    name = State()
    function = State()
    phone_number = State()
    work_shift = State()
    name_location = State()
