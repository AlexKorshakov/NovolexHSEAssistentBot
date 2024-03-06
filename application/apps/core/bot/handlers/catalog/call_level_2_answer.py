from __future__ import annotations

from aiogram import types
from aiogram.dispatcher import FSMContext
from pandas import DataFrame

from apps.MyBot import MyBot, bot_send_message
from apps.core.bot.bot_utils.check_access import check_user_access
from apps.core.bot.data.board_config import BoardConfig as board_config
from apps.core.bot.handlers.catalog.catalog_func_handler import catalog_spot_data
from apps.core.bot.handlers.catalog.catalog_support import get_dataframe, get_level_2_list_dict, get_nan_value_text, \
    text_processor_level, text_processor, list_number, level_2_column, level_3_column
from apps.core.bot.handlers.catalog.catalog_support import check_dataframe
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import build_inlinekeyboard
from apps.core.bot.messages.messages import Messages
from loader import logger


@MyBot.dp.callback_query_handler(lambda call: 'level_2__' in call.data)
async def call_level_2_answer(call: types.CallbackQuery, user_id: int | str = None, state: FSMContext = None) -> None:
    """Обработка ответов
    """
    hse_user_id = call.message.chat.id if call else user_id
    logger.debug(f'{hse_user_id = } {call.data = }')

    if not await check_user_access(chat_id=hse_user_id):
        logger.error(f'access fail {hse_user_id = }')
        return

    dataframe = await get_dataframe(hse_user_id, column_number=list_number)
    if not await check_dataframe(dataframe, hse_user_id=hse_user_id):
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены dataframe')
        return

    level_2_num: str = call.data
    level_2_list_dicts: list = await get_level_2_list_dict(hse_user_id, dataframe)
    level_2_name: str = [item[level_2_num] for item in level_2_list_dicts if level_2_num in item][0]

    catalog_spot_data['level_2_name'] = level_2_name

    df_level_2: DataFrame = dataframe.loc[
        dataframe[dataframe.columns[level_2_column]] == catalog_spot_data['level_2_name']]
    if not await check_dataframe(df_level_2, hse_user_id=hse_user_id):
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены dataframe')
        return

    level_3: list = df_level_2[df_level_2.columns[level_3_column]].unique().tolist()

    if not level_3:
        await bot_send_message(chat_id=hse_user_id, text='Данные не найдены level_3')

    title_list: list = [f"level_3__{num}" for num, item in enumerate(level_3, start=1) if item is not None]

    menu_level = await board_config(state, "menu_level", 1).set_data()
    menu_list = await board_config(state, "menu_list", title_list).set_data()
    count_col = await board_config(state, "count_col", 2).set_data()

    nan_value_text = await get_nan_value_text(hse_user_id, df_level_2, column_nom=level_3_column)
    text = await text_processor_level(
        df_level_2,
        # nan_value=nan_value_text,
        level=level_3_column, level_name=level_2_name)

    for item_txt in await text_processor(text=text):
        await bot_send_message(chat_id=hse_user_id, text=item_txt)

    reply_markup = await build_inlinekeyboard(some_list=menu_list, num_col=count_col, level=menu_level, )
    await bot_send_message(chat_id=hse_user_id, text=Messages.Choose.choose_value)


