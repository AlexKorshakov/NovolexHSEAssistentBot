from __future__ import annotations


class Messages:
    """Класс со всеми текстовыми сообщениями
    """

    default_answer_text: str = 'У вас нет прав доступа \n По всем вопросам обращайтесь к администратору\n' \
                               'https://t.me/AlexKor_MSK \n\n Для ускорения процесса отправьте администратору ' \
                               'свой табельный номер'

    help_message: str = "Справка по командам бота /help \n\n" \
                        "Видео инструкция https://www.youtube.com/channel/UCbq0Z7aDzYc3S4dAPTFDtkA \n\n" \
                        "Чтобы написать разработчику нажмите /developer"
    application_language: str = 'Язык приложения успешно изменен'

    wait: str = "Это может занять некоторое время"
    cancel: str = "Отмена!"
    correct_cancel: str = "продолжить без изменений"
    hi: str = "Приветствую"
    user_greeting: str = 'Этот бот предназначен для регистрации нарушений и создания ежедневных отчетов. Для начала работы просто отправьте боту фотографию'

    bot_setting_commands: str = 'Установка команд бота...'

    defined_recipient_list: str = 'Определён список получателей'
    all_canceled: str = "Все действия отменены"

    class Registration:
        user_registration: str = "Начинаю процедуру регистрации"
        confirm: str = "При завершении регистрации дальнейшее изменение невозможно!"
        canceled: str = "OK! если хотите зарегистрироваться, отправьте /start заново"
        cancel: str = "Отменить регистрацию"
        successful: str = 'Всего фотографий загружено '

    class Violations:
        canceled: str = "Изменения отменены"

    class Viewer:
        canceled: str = "Действия отменены"

    class Removed:
        violation_data_pc: str = "Запись о нарушении удалена с сервера"
        violation_photo_pc: str = "Фотоматериалы нарушения удалены с сервера"
        violation_data_gdrive_delete: str = "Запись о нарушении удалена с Google Drive"
        violation_photo_gdrive: str = "Фотоматериалы нарушения удалены с Google Drive"

    class Ask:
        name: str = "Введите ваше ФИО полностью"
        function: str = "Введите вашу должность полностью"
        phone_number: str = "Введите свой номер телефона с кодом (в формате +7xxxxxxxxxx)"
        work_shift: str = "Выберите в  какую смену вы работаете? (пример дневная смена / ночная смена)"
        location: str = "Выберите ваше местоположение"
        construction_manager: str = "Введите ФИО руководителя строительства полностью"
        building_control_engineer: str = "Введите полностью ФИО инженера строительного контроля"
        contractor: str = 'Выберите подрядчика из списка'
        subcontractor: str = "Введите полностью наименование субподрядчика "
        linear_bypass: str = "Введите наименование линейного обхода. Например Первичный"
        date_linear_bypass: str = "Введите дату проведения линейного обхода. Например 12.12.2021"
        contractor_representative = "Введите ФИО и должность представителя подрядчика полностью." \
                                    " Например Иванов Иван Иванович. Технический директор"
        subcontractor_representative: str = "Введите ФИО и должность представителя субподрядчика полностью." \
                                            " Например Иванов Иван Иванович. Технический директор"

    class Report:
        create_successfully: str = "Отчет сформирован на сервере"
        done: str = 'Процедура завершена'
        start_report: str = "Начинаю генерацию отчетов"
        start_act: str = 'Начало генерации актов-предписания'
        sent_successfully: str = "Отчет успешно отправлен"
        generated_successfully: str = "Отчет успешно создан"
        begin: str = "Запись загружается"
        completed_successfully: str = "Запись загружена  в базу данных." \
                                      "Вы можете сформировать акт нажав /generate или используя соответствующую команду."
        convert_successfully: str = "Отчет успешно конвертирован в pdf"
        error: str = 'не удалось конвертировать отчет в pdf'
        acts_generated_successfully: str = 'Акт(-ы) успешно созданы'

    class HSEUserAnswer:
        user_access_success: str = "Вам предоставлен доступ к функциям бота"

    class Successfully:
        bot_start: str = "Бот успешно запущен..."
        save_data_on_g_drive: str = "Данные сохранены в Google Drive"
        registration_completed: str = "Регистрация прошла успешно"
        registration_completed_in_registry: str = "Регистрация в хранилище прошла успешно"
        correct_registration_completed: str = "Изменение данных регистрации прошло успешно"
        correct_headlines_completed: str = "Изменение данных шапки отчета прошло успешно"
        correct_violations_completed: str = "Изменение данных нарушения прошло успешно"
        registration_data_received: str = "Регистрационные данные получены"
        list_tutors_received: str = "Список получателей получен"
        mail_send: str = "Письмо с отчетами успешно отправлено"
        letter_formed: str = "Письмо сформировано"

    class Enter:
        comment: str = "Введите комментарий к устранению"
        description_violation: str = "Введите описание нарушения"

    class Admin:
        answer: str = "Выберите действие"

    class Choose:
        file_for_download: str = 'Выберите файл для скачивания'
        choose_value: str = 'Выберите значение'

        folders_value: str = "Выберите информацию для отображения"

        location: str = 'Выберите подразделение'
        main_location: str = "Выберите основную локацию"
        main_category: str = "Выберите основную категорию"
        entry: str = "Выберите запись или действие для корректировки"
        elimination_time: str = "Выберите количество дней на устранение"
        violation_category: str = "Выберете степень опасности ситуации"
        normative_documents: str = "Выберете нарушение нажав на кнопку соответствующего нарушения"
        sub_location: str = "Выберете площадку нажав на соответствую кнопку "
        act_required: str = "Выберите требуется ли оформление акта - предписания"
        general_contractor: str = "Выберите подрядную организацию"
        category: str = "Выберите категорию нарушения"
        incident_level: str = "Выберите уровень происшествия"
        comment: str = "Введите комментарий к устранению"
        description: str = "Введите описание нарушения"

        period: str = "Выберите период формирования акта"

        generate_doc: str = "Выберите вид документа для формирования"

        correct_entries: str = "Выберите запись для изменения"
        action: str = 'Выберите действие'

    class Error:
        features_disabled: str = 'Функции отключены\nПо всем вопросам обращайтесь к разработчику\n https://t.me/AlexKor_MSK'
        error_command: str = 'Неверно выбрана команда'
        error_call: str = 'Нет данных сообщения'
        error_call_text: str = 'Нет текстовых данных в сообщении'
        error_action: str = "Раздел находится в разработке. обратитесь к разработчику..."

        workbook_not_found: str = "Файл с отчетом не найден! Обратитесь к разработчику! \n" \
                                  'чтобы написать разработчику нажмите /developer'
        worksheet_not_found: str = "Страница с отчетом не найден! Обратитесь к разработчику! \n" \
                                   'чтобы написать разработчику нажмите /developer'
        fill_report_path_not_found: str = "Путь к файлу с отчетом не найден! Обратитесь к разработчику! \n" \
                                          'чтобы написать разработчику нажмите /developer'
        dataframe_not_found: str = 'Не удалось получить массив данных для формирования отчета! \n' \
                                   'Обратитесь к разработчику! \n' \
                                   'чтобы написать разработчику нажмите /developer'
        dataframe_is_empty: str = 'Массив данных для формирования отчета пуст!'

        file_list_not_found: str = "Список файлов не найден! \n"
        workbook_not_create: str = "Файл с отчетом не создан! Обратитесь к разработчику! \n" \
                                   'чтобы написать разработчику нажмите /developer'

        registration_file_list_not_found: str = "Не удалось получить регистрационные данные!" \
                                                " Обратитесь к разработчику! \n" \
                                                'чтобы написать разработчику нажмите /developer'
        authorized_google_drive: str = "Не удалось авторизоваться на Google Drive!"
        upload_on_web: str = "Файл не обнаружен, загрузка на web прервана"
        file_not_found: str = "Файлы не найдены. Вероятно они были удалены"
        data_not_found: str = "Данные для составления Акта не найдены."
        location_name_not_found: str = "Не найдены данные о местоположении!"
        invalid_input: str = "Отправь мне свой номер телефона с кодом (пример +7xxxxxxxxxx)"
        no_file_too_send: str = "Нет файлов для отправки"

        list_too_send_not_found: str = "Не найден список получателей!\n Пройдите процедуру регистрации повторно" \
                                       "Для регистрации нажмите /start" \
                                       "Если ошибка повторится обратитесь к разработчику " \
                                       "Чтобы написать разработчику нажмите /developer"
        act_prescription_path_not_found: str = 'Фалл отчета не найден'
        entry_in_bd_fail: str = 'Не удалось загрузить данные в базу данных'
        entry_in_registry_fail: str = 'Не удалось загрузить данные в реестр'

    class AddUser:
        hse_full_name = 'Введите ФИО сотрудника'
        hse_full_name_dative = 'Введите ФИО сотрудника в дательном падеже'
        hse_short_name = 'Введите короткое ФИО сотрудника'
        hse_full_name_telegram = 'Введите ФИО в телеграмм'
        hse_function = 'Введите должность сотрудника'
        hse_function_dative = 'Введите должность сотрудника в дательном падеже'
        hse_department = 'Введите отдел сотрудника'
        hse_department_dative = 'Введите отдел сотрудника в дательном падеже'
        hse_is_work = 'Сотрудник находится на работе? 1 / 0'
        hse_add_finish = 'Данные внесены с настройками ролей по умолчанию. ' \
                         'Выберите дальнейшие действия или завершите загрузку.'

        hse_add_finish_success = 'Данные успешно внесены!'


class LogMessage:
    class Check:
        no_violations: str = "check_violations_final_date_elimination ::: No violations for check in DataBase"
        complete_successfully: str = 'check DataBase complete successfully'
        no_query: str = 'check_violations_status ::: No query for check violations in DataBase'
        date_created_at: str = "check_violations_final_date_elimination ::: " \
                               "No date_created_at for check violations in DataBase"
        periodic_check_unclosed_points: str = "check unclosed points complete successfully"
        time_period_error: str = 'Проверка будет выполнена в разрешенный промежуток времени'
        periodic_check_indefinite_normative: str = 'check indefinite normative documents complete successfully'
