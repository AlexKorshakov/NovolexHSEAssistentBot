from aiogram.dispatcher.filters.state import State, StatesGroup


class AnswerUserState(StatesGroup):
    # ответ пользователя Описание
    address = State()
    address_set_file = State()
    description = State()
    # ответ пользователя Состояние
    comment = State()
    current_file = State()

    location = State()
