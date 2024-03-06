import pyqrcode


def generate_qr_code(qr_data: int, qr_name: str, my_path: str = None) -> None:
    """ Функция создания QR-кодов по внешним данным
    :param qr_data: - данные для кодирования
    :param qr_name: - имя сохраняемого файла
    :param my_path: - пуьт сохранения сгенерированного файла
    :return: None
    """
    # version - сложность QR-кода  - 2
    # scale - размер QR-кода 1-40
    # quiet_zone - рамка вокруг QR-кода 0-10

    big_code = pyqrcode.create(qr_data, version=2, encoding="utf8")
    big_code.png(my_path + qr_name + '.png', scale=10, module_color=[0, 0, 0, 128], background=[0xff, 0xff, 0xcc],
                 quiet_zone=1)
    # print(big_code.get_png_size())


if __name__ == '__main__':

    QR_path: str = f'C:\\Users\\DeusEx\\Desktop\\Qr\\'

    my_list: list = [
        (995705, "Фукс Алексей Валерьевич"),
        (995706, "Меженов Андрей Александрович"),
        (995707, "Сокол Владимир Анатольевич"),
        (995708, "Логвиненко Валерий Анатольевич"),
        (995709, "Кравченко Владимир Сергеевич"),
        (995710, "Санжура Руслан Ильич"),
    ]

    for folder in my_list:
        generate_qr_code(folder[0], folder[1], QR_path)
