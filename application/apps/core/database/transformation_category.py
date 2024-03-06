from apps.core.bot.messages.messages import Messages

CATEGORY_ID_TRANSFORM: dict = dict(
    location={
        'this_level_number': 0,

        'item': 'location',
        'column': 'location_id',
        'table': 'core_location',

        'description': 'Закреплённый участок',

        'this_level': 'core_location',
        'this_level_message': Messages.Choose.location,
        'this_level_count_col': 1,
        'previous_level': 'location',
        'previous_level_number': False,
        'next_level': 'core_mainlocation',
        'next_level_number': 1,
        'next_level_message': Messages.Choose.main_location,
    },
    main_location={
        'this_level_number': 1,

        'item': 'main_location',
        'column': 'main_location_id',
        'table': 'core_mainlocation',

        'description': 'Площадка',

        'this_level': 'core_mainlocation',
        'this_level_message': Messages.Choose.main_location,
        'this_level_count_col': 1,
        'previous_level': 'location',
        'previous_level_number': 0,
        'next_level': 'core_sublocation',
        'next_level_number': 2,
        'next_level_message': Messages.Choose.sub_location,
    },
    sub_locations={
        'this_level_number': 2,

        'item': 'sub_location',
        'column': 'sub_location_id',
        'table': 'core_sublocation',
        'description': 'Под площадка / участок',

        'this_level': 'core_sublocation',
        'this_level_message': Messages.Choose.sub_location,
        'this_level_count_col': 2,
        'previous_level_number': 1,
        'previous_level': 'main_location',
        'next_level': 'core_maincategory',
        'next_level_number': 3,
        'next_level_message': Messages.Choose.main_category,
    },
    main_category={
        'this_level_number': 3,

        'item': 'main_category',
        'column': 'main_category_id',
        'table': 'core_maincategory',
        'description': 'Основная категория',

        'this_level': 'core_maincategory',
        'this_level_message': Messages.Choose.main_category,
        'this_level_count_col': 1,
        'previous_level': 'main_location',
        'previous_level_number': 1,
        'previous_level_description': 'Возврат на одну категорию выше от порядка',
        'next_level': 'core_category',
        'next_level_number': 4,
        'next_level_message': Messages.Choose.category,
    },
    category={
        'this_level_number': 4,

        'item': 'category',
        'column': 'category_id',
        'table': 'core_category',
        'description': 'Глобальная категория / направление',

        'this_level': 'core_category',
        'this_level_message': Messages.Choose.category,
        'this_level_count_col': 2,
        'previous_level': 'main_category',
        'previous_level_number': 3,
        'next_level': 'core_normativedocuments',
        'next_level_number': 5,
        'next_level_message': Messages.Choose.violation_category,
    },
    violation_category={
        'this_level_number': 5,

        'item': 'violation_category',
        'column': 'violation_category_id',
        'table': 'core_violationcategory',
        'description': 'Категория нарушения',

        'this_level': 'core_violationcategory',
        'this_level_message': Messages.Choose.violation_category,
        'this_level_count_col': 2,
        'previous_level': 'category',
        'previous_level_number': 4,
        'next_level': 'core_generalcontractor',
        'next_level_number': 6,
        'next_level_message': Messages.Choose.normative_documents,
    },
    normative_documents={
        'this_level_number': 6,

        'item': 'normative_documents',
        'column': 'normative_documents_id',
        'table': 'core_normativedocuments',
        'description': 'Под Категория',

        'this_level': 'core_normativedocuments',
        'this_level_message': Messages.Choose.normative_documents,
        'this_level_count_col': 2,
        'previous_level': 'core_category',
        'previous_level_number': 5,
        'next_level': 'core_violationcategory',
        'next_level_message': Messages.Choose.category,
    },
    general_contractor={
        'this_level_number': 7,

        'item': 'general_contractor',
        'column': 'general_contractor_id',
        'table': 'core_generalcontractor',
        'description': 'Подрядчик',

        'this_level': 'core_generalcontractor',
        'this_level_message': Messages.Choose.general_contractor,
        'this_level_count_col': 1,
        'previous_level': 'violation_category',
        'previous_level_number': 5,
        'previous_level_description': 'Возврат на одну категорию выше от порядка',
        'next_level': 'core_actrequired',
        'next_level_number': 8,
        'next_level_message': Messages.Choose.act_required,
    },
    act_required={
        'this_level_number': 8,

        'item': 'act_required',
        'column': 'act_required_id',
        'table': 'core_actrequired',
        'description': 'Требуется оформление Акта-предписания?',

        'this_level': 'core_actrequired',
        'this_level_message': Messages.Choose.act_required,
        'this_level_count_col': 1,
        'previous_level': 'general_contractors',
        'previous_level_number': 7,
        'next_level': 'core_incidentlevel',
        'next_level_number': 9,
        'next_level_message': Messages.Choose.incident_level,
    },
    incident_level={
        'this_level_number': 9,

        'item': 'incident_level',
        'column': 'incident_level_id',
        'table': 'core_incidentlevel',
        'description': 'Уровень происшествия',

        'this_level': 'core_incidentlevel',
        'this_level_message': Messages.Choose.incident_level,
        'this_level_count_col': 1,
        'previous_level': 'act_required',
        'previous_level_number': 8,
        'next_level': 'core_eliminationtime',
        'next_level_number': 10,
        'next_level_message': Messages.Choose.elimination_time,
    },
    elimination_time={
        'this_level_number': 10,

        'item': 'elimination_time',
        'column': 'elimination_time_id',
        'table': 'core_eliminationtime',
        'description': 'Время на устранение',

        'this_level': 'core_eliminationtime',
        'this_level_message': Messages.Choose.elimination_time,
        'this_level_count_col': 1,
        'previous_level': 'act_required',
        'previous_level_number': 9,
        'next_level': '',
        'next_level_number': 11,
        'next_level_message': Messages.Choose.description,
    },
)
