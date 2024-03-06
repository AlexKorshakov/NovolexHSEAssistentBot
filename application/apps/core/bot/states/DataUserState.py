from aiogram.dispatcher.filters.state import State, StatesGroup


class DataUserState(StatesGroup):

    user_data = State()
