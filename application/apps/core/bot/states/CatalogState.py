from aiogram.dispatcher.filters.state import StatesGroup, State


class CatalogState(StatesGroup):
    inquiry = State()


class CatalogStateEmployee(StatesGroup):
    inquiry = State()


class CatalogStateLNA(StatesGroup):
    inquiry = State()

