from aiogram.dispatcher.filters.state import State, StatesGroup


class RegisterState(StatesGroup):
    name = State()
    function = State()
    phone_number = State()
    work_shift = State()
    location = State()
