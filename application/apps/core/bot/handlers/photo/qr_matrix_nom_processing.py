from __future__ import annotations

import asyncio
import io
import json
import os
import traceback
from itertools import chain

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup

from apps.MyBot import bot_send_document, bot_send_message, MyBot, bot_edit_message
from apps.core.bot.data.board_config import BoardConfig as board_config
from apps.core.bot.handlers.photo.qr_support_paths import qr_get_file_path
from apps.core.bot.keyboards.inline.build_castom_inlinekeyboard import (build_inlinekeyboard,
                                                                        build_text_for_inlinekeyboard,
                                                                        move_action)
from apps.core.bot.messages.messages import Messages
from apps.core.bot.reports.report_data import QRData
from config.config import Novolex_media_path
from loader import logger


@MyBot.dp.callback_query_handler(lambda call: call.data[0] == '#', state=QRData.all_states)
async def qr_matrix_nom_processing(hse_user_id: str, qr_data, state: FSMContext) -> None:
    """"""

    if not isinstance(qr_data, list):
        await bot_send_message(chat_id=hse_user_id, text='данных не найдено')
        return

    folder_path: str = await qr_get_file_path(Novolex_media_path, '!industrial_equipment_catalog')
    folders: list = await get_folders(str(folder_path))

    m_data: str = list(chain(*qr_data))[0].replace('qr_matrix_nom_', '')
    await set_violation_atr_data(atr_name='matrix_nom', art_val=m_data, state=state)

    equipment_folder: str = await get_equipment_folder(hse_user_id, m_data, folders)
    await set_violation_atr_data(atr_name='dir', art_val=equipment_folder, state=state)

    matrix_folder_path: str = await qr_get_file_path(
        Novolex_media_path, '!industrial_equipment_catalog', equipment_folder
    )
    folders: list = await get_folders(str(matrix_folder_path))

    filled_folders: list = [
        f'{item}*({await check_len_folder(sub_folder=item, state=state)})'
        for item in folders
        if await check_folder(sub_folder=item, state=state)
    ]

    menu_level = await board_config(state, "menu_level", 1).set_data()
    menu_list = await board_config(state, "menu_list", filled_folders).set_data()
    count_col = await board_config(state, "count_col", 1).set_data()

    reply_markup: InlineKeyboardMarkup = await build_inlinekeyboard(
        some_list=menu_list, num_col=count_col, level=menu_level, called_prefix='industrial_equipment_',
        state=state
    )

    await bot_send_message(
        chat_id=hse_user_id, text=Messages.Choose.folders_value, reply_markup=reply_markup
    )
    await QRData.equipment_folder.set()


@MyBot.dp.callback_query_handler(lambda call: 'industrial_equipment_' in call.data,
                                 state=QRData.equipment_folder)
async def industrial_equipment_answer(call: types.CallbackQuery, user_id: str = None, state: FSMContext = None) -> None:
    """Обработка ответов
    """

    hse_user_id = call.message.chat.id if call else user_id
    logger.info(f'{hse_user_id = } message_id: {call.message.message_id} {call.data = }')

    v_data: dict = await state.get_data()
    folder: str = v_data.get('dir')

    sub_folder: str = call.data.split('_')[-1].replace('industrial_equipment_', '')
    sub_folder: str = sub_folder.split('*')[0]

    await set_violation_atr_data(atr_name='sub_folder', art_val=sub_folder, state=state)

    await notify_user_for_choice(call, data_answer=sub_folder if sub_folder else '')

    matrix_folder_path: str = await qr_get_file_path(Novolex_media_path, '!industrial_equipment_catalog', folder,
                                                     sub_folder)
    folders: list = await get_folders(str(matrix_folder_path))

    files: list = await get_files(folder_path=matrix_folder_path)
    if not files:
        await error_messeg(hse_user_id, state)
        return

    short_title: list = await get_short_title_list(files)
    data_list: list = await get_data_list(files)

    menu_level = await board_config(state, "menu_level", 1).set_data()
    menu_list = await board_config(state, "menu_list", short_title).set_data()
    count_col = await board_config(state, "count_col", 1).set_data()

    previous_level: str = v_data.get('dir')
    await board_config(state).set_data("previous_level", previous_level)

    zipped_list: list = list(zip(short_title, data_list))
    text_list: list = [f"{await get_character_text(item)}" for item in zipped_list if item[0][0] != '#']

    menu_text_list = await board_config(state).set_data("text_list", text_list)

    reply_markup: InlineKeyboardMarkup = await build_inlinekeyboard(
        some_list=menu_list, num_col=count_col, level=menu_level, called_prefix='equipment_doc_',
        previous_level=previous_level, use_search=False
    )
    reply_text: str = await build_text_for_inlinekeyboard(
        some_list=menu_text_list, level=menu_level, )
    text: str = f'{Messages.Choose.file_for_download}\n\n{reply_text}'

    await bot_send_message(chat_id=hse_user_id, text=text, reply_markup=reply_markup)

    await QRData.equipment_doc.set()


@MyBot.dp.callback_query_handler(lambda call: 'equipment_doc_' in call.data, state=QRData.equipment_doc)
async def industrial_equipment_answer(call: types.CallbackQuery, user_id: str = None, state: FSMContext = None) -> None:
    """Обработка ответов
    """

    hse_user_id = call.message.chat.id if call else user_id
    logger.info(f'{hse_user_id = } message_id: {call.message.message_id} {call.data = }')

    v_data: dict = await state.get_data()
    folder: str = v_data.get('dir')
    sub_folder: str = v_data.get('sub_folder')

    matrix_folder_path: str = await qr_get_file_path(
        Novolex_media_path, '!industrial_equipment_catalog', folder, sub_folder
    )

    files: list = await get_files(folder_path=matrix_folder_path)
    if not files:
        await error_messeg(hse_user_id, state)
        await state.finish()
        return

    call_data = call.data.replace("equipment_doc_", '')
    equipment_doc = [i for i in files if call_data in i]
    equipment_doc = equipment_doc[0] if equipment_doc else ''

    if not equipment_doc:
        await error_messeg(hse_user_id, state)
        await state.finish()
        return

    equipment_doc_path: str = await qr_get_file_path(
        Novolex_media_path, '!industrial_equipment_catalog', folder, sub_folder, equipment_doc
    )
    equipment_doc_path = str(equipment_doc_path)
    await bot_send_document(
        chat_id=hse_user_id,
        doc_path=equipment_doc_path,
        caption='Файл',
        calling_fanc_name=await fanc_name()
    )


@MyBot.dp.callback_query_handler(move_action.filter(action=["pre_paragraph"]), state=QRData.all_states)
async def previous_paragraph_answer(call: types.CallbackQuery, callback_data: dict,
                                    user_id: [int, str] = None, state: FSMContext = None):
    """Обработка ответов содержащихся в previous_paragraph
    """

    hse_user_id = call.message.chat.id if call else user_id

    logger.info(f'{hse_user_id = } message_id: {call.message.message_id} {call.data = }')
    message_id = call.message.message_id

    v_data: dict = await state.get_data()
    equipment_folder: str = v_data.get('dir')

    matrix_folder_path: str = await qr_get_file_path(
        Novolex_media_path, '!industrial_equipment_catalog', equipment_folder
    )
    folders: list = await get_folders(str(matrix_folder_path))

    filled_folders: list = [f'{item}*({await check_len_folder(sub_folder=item, state=state)})'
                            for item in folders
                            if await check_folder(sub_folder=item, state=state)]

    menu_level = await board_config(state, "menu_level", 1).set_data()
    menu_list = await board_config(state, "menu_list", filled_folders).set_data()
    count_col = await board_config(state, "count_col", 1).set_data()

    reply_markup: InlineKeyboardMarkup = await build_inlinekeyboard(
        some_list=menu_list, num_col=count_col, level=menu_level, called_prefix='industrial_equipment_',
        state=state
    )
    # await MyBot.bot.edit_message_text(
    #     text=Messages.Choose.folders_value, chat_id=hse_user_id, message_id=message_id, reply_markup=reply_markup
    # )
    result = await bot_edit_message(
        hse_user_id=hse_user_id, message_id=message_id,
        reply_markup=reply_markup, reply_text=Messages.Choose.folders_value, kvargs={'fanc_name': await fanc_name()}
    )

    await QRData.equipment_folder.set()

    return result


async def check_folder(sub_folder: str, state: FSMContext) -> bool:
    return True
    # v_data: dict = await state.get_data()
    # folder: str = v_data.get('dir')
    #
    # directory: str = await qr_get_file_path(Novolex_media_path, '!industrial_equipment_catalog', folder, sub_folder)
    #
    # files = all(files for (_, _, files) in os.walk(directory))
    # if not files:
    #     return False
    # return True


async def check_len_folder(sub_folder: str, state: FSMContext) -> int:
    v_data: dict = await state.get_data()
    folder: str = v_data.get('dir')

    directory: str = await qr_get_file_path(Novolex_media_path, '!industrial_equipment_catalog', folder, sub_folder)

    for _, _, files in os.walk(directory):
        if not files:
            return 0

        return len(files)


async def get_equipment_folder(hse_user_id, m_data, folders) -> str:
    """

    :param hse_user_id:
    :param m_data:
    :param folders:
    :return:
    """

    equipment_folder = [item for item in folders if m_data in item]
    if not equipment_folder:
        await bot_send_message(chat_id=hse_user_id, text='данных не найдено')
        return ''

    if len(equipment_folder) > 1:
        logger.info(f'Задвоение папок {equipment_folder[0]}')
        equipment_folder = equipment_folder[0:1]

    if isinstance(equipment_folder, list):
        equipment_folder = equipment_folder[0]

    return equipment_folder


async def error_messeg(hse_user_id, state):
    """

    :param hse_user_id:
    :param state:
    :return:
    """
    v_data: dict = await state.get_data()
    previous_level: str = v_data.get('dir')

    reply_markup: InlineKeyboardMarkup = await build_inlinekeyboard(previous_level=previous_level)
    text = 'Нет данных для отображения'

    await bot_send_message(chat_id=hse_user_id, text=text, reply_markup=reply_markup)


async def notify_user_for_choice(call_msg: types.CallbackQuery | types.Message, user_id: int | str = None,
                                 data_answer: str = None) -> bool:
    """Уведомление пользователя о выборе + логирование

    :param data_answer:
    :param user_id: int | str id пользователя
    :param call_msg:
    :return None :
    """

    if isinstance(call_msg, types.CallbackQuery):

        for i in ('previous_paragraph', 'move_up', 'move_down'):
            if i in call_msg.data: return True

        mesg_text: str = f"Выбрано: {data_answer}"
        if call_msg.data in call_msg.message.text:
            mesg_list: list = [item for item in call_msg.message.text.split('\n\n') if call_msg.data in item]
            mesg_text = f"Выбрано: {mesg_list[0]}"

        try:
            hse_user_id = call_msg.message.chat.id if call_msg else user_id
            logger.debug(f"{hse_user_id = } Выбрано: {data_answer} {call_msg.data}")
            await call_msg.message.edit_text(text=mesg_text, reply_markup=None)
            return True

        except Exception as err:
            logger.debug(f"{call_msg.message.chat.id = } {repr(err)}")

    if isinstance(call_msg, types.Message):

        for i in ('previous_paragraph', 'move_up', 'move_down'):
            if i in call_msg.text: return True

        mesg_text: str = f"Выбрано: {data_answer}"
        if call_msg.text in call_msg.text:
            mesg_list: list = [item for item in call_msg.text.split('\n\n') if call_msg.text in item]
            mesg_text = f"Выбрано: {mesg_list[0] if mesg_list else ''}"

        try:
            hse_user_id = call_msg.chat.id if call_msg else user_id
            logger.debug(f"{hse_user_id = } Выбрано: {data_answer} {call_msg.text}")
            await call_msg.edit_text(text=mesg_text, reply_markup=None)
            return True

        except Exception as err:
            logger.debug(f"{call_msg.chat.id = } {repr(err)}")


# async def add_employee_inline_keyboard_with_action(item: dict) -> InlineKeyboardMarkup:
#     """Формирование сообщения с текстом и кнопками действий в зависимости от параметров
#
#     :return:
#     """
#
#     markup = types.InlineKeyboardMarkup()
#
#     if item.get("matrix_code"):
#         markup.add(types.InlineKeyboardButton(
#             text='Матрица изоляции',
#             callback_data=posts_cb.new(id='-', action='еquipment_matrix_doc')))
#
#     if item.get("matrix_post"):
#         markup.add(types.InlineKeyboardButton(
#             text='Следующая установка',
#             callback_data=posts_cb.new(id='-', action='еquipment_matrix_next')))
#
#     if item.get("matrix_prev"):
#         markup.add(types.InlineKeyboardButton(
#             text='Предыдущая установка',
#             callback_data=posts_cb.new(id='-', action='еquipment_matrix_prev')))
#
#     markup.add(types.InlineKeyboardButton(
#         text='Параметры работы оборудования',
#         callback_data=posts_cb.new(id='-', action='еquipment_operation_parameters')))
#
#     markup.add(types.InlineKeyboardButton(
#         text='Заявка на ремонт',
#         callback_data=posts_cb.new(id='-', action='equipment_repair_request')))
#
#     markup.add(types.InlineKeyboardButton(
#         text='Заказать пиццу',
#         callback_data=posts_cb.new(id='-', action='ORDER_PIZZA')))
#
#     return markup


async def get_folders(folder_path: str) -> list:
    """

    :param folder_path:
    :return:
    """
    if not folder_path:
        return []

    for _, dirs, _ in os.walk(folder_path):
        return dirs


async def get_files(folder_path: str) -> list:
    """

    :param folder_path:
    :return:
    """
    if not folder_path:
        return []

    for _, _, files in os.walk(folder_path):
        return files


async def set_violation_atr_data(atr_name: str, art_val: str | int, state: FSMContext = None, **kvargs) -> bool:
    """Запись данных  атрибута 'atr_name': art_val глобального словаря violation_data в файл json

    :param state:
    :param atr_name: str имя ключа
    :param art_val: str|int значение ключа
    :return: bool True если успешно.
    """

    logger.debug(f'set_violation_atr_data: {atr_name = } {art_val = }')

    if not atr_name:
        return False

    await state.update_data({atr_name: art_val})

    state_dict: dict = await state.get_data()
    json_full_name = state_dict.get("json_full_name")
    if json_full_name:
        await write_json_file(data=state_dict, name=json_full_name)

    return True


async def get_short_title_list(data_list) -> list:
    replace_list = []
    for i in data_list:
        replace_list.append(' '.join(i.split(' ')[:3]))

    return replace_list


async def get_data_list(data_list: list = None) -> list:
    """ Функция получения данных из базы данных. При отсутствии данных поиск в json.
    При наличии condition - формирование данных согласно  condition

    :param data_list:
    :return: data_list or [ ]
    """

    # replace_list = []
    # for i in data_list:
    #     replace_list.append(i.split(' ')[:3])

    return data_list


async def get_character_text(param_list: list | str) -> list | str:
    """

    :return:
    """

    if isinstance(param_list, list):
        if not param_list: return []

        text_list: list = [
            f"item {item.get('id')} {item.get('title')} " \
            # f"\nvalue : {'on' if item.get('value') == 1 else 'off'}"
            for item in param_list if
            item.get('id') is not None
        ]
        return text_list

    if isinstance(param_list, dict):
        if not param_list: return ''

        text_list: str = f"item {param_list.get('id')} {param_list.get('title')} {param_list.get('comment')} " \
            # f"\nvalue : {'on' if param_list.get('value') == 1 else 'off'}"

        return text_list

    if isinstance(param_list, tuple):
        if not param_list: return ''
        if param_list[0][0] == '#': return ''

        text_list: str = f"{param_list[0].split('_')[0]} : {param_list[1]}"

        return text_list


async def write_json_file(*, data: dict | str = None, name: str = None) -> bool:
    """Запись данных в json

    :param name: полный путь к файлу
    :param data: dict  с данными для записи
    """

    result: bool = await write_json(name=name, data=data)
    return result


async def write_json(name: str, data) -> bool:
    """Запись данных в json

    :param name: полный путь для записи / сохранения файла включая расширение,
    :param data: данные для записи / сохранения
    :return: True or False
    """
    try:
        with io.open(name, 'w', encoding='utf8') as outfile:
            str_ = json.dumps(data,
                              indent=4,
                              sort_keys=True,
                              separators=(',', ': '),
                              ensure_ascii=False)
            outfile.write(str_)
            return True
    except TypeError as err:
        logger.error(f"TypeError: {repr(err)}")
        return False


async def fanc_name() -> str:
    stack = traceback.extract_stack()
    return str(stack[-2][2])


async def test():
    hse_user_id = 373084462
    data = [['qr_matrix_nom_CM51-PU-002']]
    await qr_matrix_nom_processing(hse_user_id, data)


# async def get_data_for_test(hse_user_id, qr_data):
#     matrix_data = [
#         {
#             "file": "матрица изоляции CM51-PU-002.docx",
#             "matrix_code": 'CM51-PU-002',
#             "matrix_post": 'CM51-PU-003',
#             "matrix_prev": 'CM51-PU-001',
#             "main_location": 'Участки технологического комплекса',
#             "glob_location": 'УАВиН',
#             "location": 'литер здания',
#             "sub_location": 'участок или площадка',
#             "description": 'Насос шламовый Warman 10/8F-AH/WRT',
#             "technology": 'как то работает и ладно',
#             "responsible": 'Иванов Петр Сидорович',
#             "subdir": 'C:\\Users\\KDeusEx\\PycharmProjects\\SWTS\\application\\apps\\core\\bot\\handlers\\photo'
#                       '\\isolation_matrix\\Все матрицы\\Участки технологического комплекса\\УАВиН\\'
#                       'Матрицы УАВиН\\Выщелачивание',
#
#         },
#     ]
#
#     for item in matrix_data:
#         if item.get('matrix_code') != list(chain(*qr_data))[0].replace('qr_matrix_nom_', ''): continue
#
#         reply_markup = await add_employee_inline_keyboard_with_action(item)
#
#         doc_path: str = f"{item.get('subdir')}\\{item.get('file')}"
#         caption: str = f"{item.get('main_location')} " \
#                        f"{item.get('glob_location')} " \
#                        f"{item.get('location')} " \
#                        f"{item.get('sub_location')} " \
#                        f"Установка: {item.get('description')}\n" \
#                        f"Ответственный: {item.get('responsible')}\n" \
#                        f"Технология: {item.get('technology')}"
#
#         kwargs: dict = {
#             'reply_markup': reply_markup
#         }
#
#         await bot_send_document(
#             chat_id=hse_user_id,
#             doc_path=doc_path,
#             caption=caption,
#             fanc_name=await fanc_name(),
#             **kwargs
#         )
#         print()


if __name__ == '__main__':
    asyncio.run(test())
