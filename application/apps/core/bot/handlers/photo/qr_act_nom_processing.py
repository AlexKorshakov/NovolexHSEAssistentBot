import math

from apps.MyBot import bot_send_message
from apps.core.bot.handlers.photo.qr_worker import generate_text
from apps.core.bot.messages.messages_test import msg


async def qr_act_nom_processing(hse_user_id, data):
    """

    :param hse_user_id:
    :param data:
    :return:
    """
    answer_text: str = await generate_text(hse_user_id, qr_data=data)

    if not answer_text:
        answer_text: str = await msg(
            hse_user_id, cat='warning', msge='qr_not_found', default="QR-код, не распознан или отсутствует"
        ).g_mas()
        await bot_send_message(chat_id=hse_user_id, text=answer_text)

    for item_txt in await text_processor(text=answer_text):
        await bot_send_message(chat_id=hse_user_id, text=item_txt)


async def text_processor(text: str = None) -> list:
    """Принимает data_list_to_text[] для формирования текста ответа
    Если len(text) <= 3500 - отправляет [сообщение]
    Если len(text) > 3500 - формирует list_with_parts_text = []

    :param text:
    :return: list - list_with_parts_text
    """
    if not text:
        return []

    step = 3500
    if len(text) <= step:
        return [text]

    len_parts = math.ceil(len(text) / step)
    list_with_parts_text: list = [text[step * (i - 1):step * i] for i in range(1, len_parts + 1)]

    return list_with_parts_text
