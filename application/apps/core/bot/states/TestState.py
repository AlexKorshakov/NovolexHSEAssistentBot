from aiogram.dispatcher.filters.state import State, StatesGroup


class TestState(StatesGroup):
    somelist = State()
    level = State()
