import asyncio
import importlib
import os
import sys
import traceback
from itertools import chain

import loader

loader.logger.debug(f"{__name__} start import")


async def run_custom_import():
    print(f'{await fanc_name()} :: {__file__}')

    directory: str = f'{os.sep}'.join(__file__.split(f'{os.sep}')[:-1])
    moduls_path: list = list(chain(*[files for (_, _, files) in os.walk(directory)]))

    for module_name in [file.split('.')[0] for file in moduls_path if file.endswith('.py')]:
        if module_name in sys.modules: continue
        spec = importlib.util.spec_from_file_location(module_name, f'{directory}{os.sep}{module_name}.py')
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)


async def fanc_name() -> str:
    """Возвращает имя вызываемой функции"""
    stack = traceback.extract_stack()
    return str(stack[-2][2])


asyncio.run(run_custom_import())

