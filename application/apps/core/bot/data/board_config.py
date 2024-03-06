from __future__ import annotations

import traceback

from aiogram.dispatcher import FSMContext

from loader import logger


class BoardConfig:
    """Класс для действий над состоянием state"""

    def __init__(self, state: FSMContext = None, atr_name: str = None, art_val: any = None, call_func: str = None):
        self.state: FSMContext = state
        self.atr_name: str = atr_name
        self.art_val: any = art_val
        self.call_func: str = f'{call_func = }' if call_func else ''

    async def set_data(self, atr_name: str = None, art_val: any = None, call_func: str = None) -> any:
        """Присвоение значений состоянию self.state. Возвращает значение атрибута art_val

        :param call_func:
        :param atr_name: str - имя атрибута
        :param art_val: any значение атрибута
        :return: art_val
        """
        atr_name: str = atr_name if atr_name else self.atr_name
        art_val: any = art_val if art_val else self.art_val
        call_func = f'{call_func = }' if call_func else self.call_func

        if art_val is None:
            return self.state

        if self.state is None:
            logger.error(f'{__name__} {await fanc_name()} Invalid state is None {call_func}')
            return art_val

        try:
            await self.state.update_data({atr_name: art_val})

        except AttributeError as err:
            logger.error(f'{__name__} {await fanc_name()} {call_func} Invalid err. {repr(err)}')

        return art_val

    async def get_data(self) -> dict:
        """Получение данных состояния self.state

        :return: dict
        """
        v_data: dict = await self.state.get_data()
        return v_data


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])
