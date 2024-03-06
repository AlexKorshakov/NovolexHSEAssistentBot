"""Модуль класса QueryConstructor для формирования запроса по условиям """
from loader import logger

logger.debug(f"{__name__} start import")
import asyncio
from abc import ABCMeta
from datetime import datetime

logger.debug(f"{__name__} finish import")


class QueryStorageFields(metaclass=ABCMeta):

    def __init__(self):
        self.user_id = None
        self.table_name = None

        self.type_query = None
        self.user_data_dict = None

        self.action = None
        self.subject = None

        self.conditions = None

        self.period = None
        self.is_admin = None
        self.main_location = None
        self.main_location_id = None
        self.title = None
        self.location = None
        self.act_number = None
        self.short_title = None
        self.status_id = None
        self.finished_id = None
        self.violation_id = None
        self.hashtag = None
        self.category_id = None
        self.normative_documents_id = None
        self.id = None

        self.query = None

        self.main_part = None
        self.__part_period = None
        self.__part_user = None
        self.__part_location = None
        self.__part_act_number = None
        self.__part_short_title = None
        self.__part_status = None
        self.__part_finished = None
        self.__part_violation = None
        self.__part_hashtags = None
        self.__part_lazy_query = None
        self.__part_title = None
        self.__part_id = None
        self.__part_general_contractor_id = None
        self.lazy_query = None

        self.date_start = None
        self.date_stop = None

        self.week_number = None
        self.hse_telegram_id = None
        self.general_contractor_id = None
        self.file_id = None


class QueryStorageMethods(QueryStorageFields):
    """Класс хранилище методов"""

    def __init__(self):
        super().__init__()
        self.exception = [None, 'all', 'not', 'not including']

    async def get_part_status(self) -> str:
        """Обработка параметра status_id и формирование части запроса и part_status """
        if self.status_id is None: return ''
        if isinstance(self.status_id, str):
            if self.status_id == '': return ''
            return f'`status_id` {self.status_id}'
        if isinstance(self.status_id, int):
            return f'`status_id` = {self.status_id}'
        return ''

    async def get_part_short_title(self) -> str:
        """Обработка параметра short_title и формирование части запроса и part_short_title """
        if not self.short_title: return ''
        if self.short_title: return f"`short_title` = '{self.short_title}' "

    async def get_part_act_number(self) -> str:
        """Обработка параметра act_number и формирование части запроса и part_act_number """
        if self.act_number in self.exception:
            return ''
        if self.act_number is None:
            return ''
        if self.act_number == '':
            return '(`act_number` = "" or `act_number` is NULL) '
        if self.act_number:
            return f'`act_number` = {self.act_number} '

    async def get_part_is_admin(self) -> str:
        """Обработка параметра is_admin и формирование части запроса и part_is_admin """
        if self.is_admin: return ''
        if self.user_id is None: return ''
        return f"`user_id` = {self.user_id} "

    async def get_part_period(self) -> str:
        """Обработка параметра period и формирование части запроса и part_period """
        self.date_start, self.date_stop = await self.get_period()

        if self.date_start is None and self.date_stop is None: return ''
        return f"`created_at` BETWEEN date('{self.date_start}') AND date('{self.date_stop}') "

    async def get_part_finished(self) -> str:
        """Обработка параметра finished и формирование части запроса и part_finished """

        if self.finished_id is None: return ''

        try:
            self.finished_id = int(self.finished_id)
        except ValueError as err:
            logger.debug(f'{repr(err)}')

        if isinstance(self.finished_id, str):
            if self.finished_id == '': return ''
            return f'`finished_id` {self.finished_id}'

        if isinstance(self.finished_id, int):
            return f'`finished_id` = {self.finished_id}'

    async def get_part_violation(self) -> str:
        """Обработка параметра violation и формирование части запроса и part_violation """
        if self.violation_id is None: return ''
        if self.violation_id: return f'`violation_id` = {self.violation_id} '

    async def get_part_location(self) -> str:
        """Обработка параметра location и формирование части запроса и part_location """
        if self.location is None: return ''
        return f"`location_id` = '{self.location}' "

    async def get_part_main_location(self):
        """Обработка параметра main_location и формирование части запроса и part_main_location """
        if self.main_location_id is None: return ''

        return f"`main_location_id` = '{self.main_location_id}' "

    async def get_part_hashtags(self) -> str:
        """Обработка параметра hashtags и формирование части запроса и part_hashtags """
        if self.hashtag is None: return ''

        if isinstance(self.hashtag, str):
            hashtag_condition = self.conditions.get('hashtag_condition', None)
            if not hashtag_condition: return f"`hashtags` LIKE '%{self.hashtag}%' "
            if hashtag_condition.upper() != 'LIKE': return f"`hashtags` {hashtag_condition} '{self.hashtag}' "
            return f"`hashtags` LIKE '%{self.hashtag}%' "

        if isinstance(self.hashtag, list):
            return ''

        return ''

    async def get_normative_documents_id(self):
        if self.normative_documents_id is None: return ''
        if isinstance(self.normative_documents_id, str):
            if self.normative_documents_id == '': return ''
            return f'`normative_documents_id` {self.normative_documents_id}'

        if isinstance(self.normative_documents_id, int):
            return f'`normative_documents_id` = {self.normative_documents_id}'

    async def get_part_category_id(self):
        if self.category_id is None: return ''
        return f"`category_id` = {self.category_id} "

    async def get_part_title(self):
        if self.title is None: return ''
        return f"`title` = '{self.title}' "

    async def get_part_id(self):
        if self.id is None: return ''
        return f" `id` = '{self.id}' "

    async def get_part_lazy_query(self) -> str:
        """Обработка параметра status_id и формирование части запроса и part_lazy_query """
        if self.lazy_query is None: return ''
        return f" {self.lazy_query} "

    async def get_part_week_number(self) -> str:
        """Обработка параметра status_id и формирование части запроса и part_week_number """
        if self.week_number is None: return ''
        return f" `week_number` = {self.week_number} "

    async def get_part_hse_telegram_id(self) -> str:
        """Обработка параметра status_id и формирование части запроса и hse_telegram_id """
        if self.hse_telegram_id is None: return ''
        return f" `hse_telegram_id` = {self.hse_telegram_id} "

    async def get_part_file_id(self) -> str:
        if self.file_id is None: return ''
        return f"`file_id` = '{self.file_id}' "

    async def get_general_contractor_id(self) -> str:
        """Обработка параметра status_id и формирование части запроса и general_contractor_id """
        if self.general_contractor_id is None: return ''
        return f" `general_contractor_id` = {self.general_contractor_id} "

    async def get_period(self):
        """Формирование периода"""
        if isinstance(self.period, list):
            self.date_start, self.date_stop = await self.get_date_list()
            return self.date_start, self.date_stop

        if isinstance(self.period, dict):
            self.date_start, self.date_stop = await self.get_date_dict()
            return self.date_start, self.date_stop

        if isinstance(self.period, str):
            self.period = await self.format_data(self.period)
            return self.period, self.period

        if self.period is None:
            return None, None

    async def get_date_list(self):
        """Обработка частей периода из list. """
        if isinstance(self.period, list):
            return await self.format_data(self.period[0]), await self.format_data(self.period[1])

    async def get_date_dict(self):
        """Обработка частей периода из dict."""
        if isinstance(self.period, dict):
            return self.period.get('date_start', None), self.period.get('date_stop', None)

    @staticmethod
    async def format_data(date_item: str) -> str:
        """ Форматирование даты в формат даты БВ
        """
        try:
            return datetime.strptime(date_item, "%d.%m.%Y").strftime("%Y-%m-%d")
        except ValueError as err:
            logger.error(f'QueryConstructor.format_data {date_item = } {repr(err)}')
            return date_item


class QueryConstructor(QueryStorageMethods):
    """Класс конструктор запросов к БД
    "action": 'SELECT',
    "subject": '*',
    "conditions": {
        "period": query_period,
        "period_description": 'Период для формирования запроса. Может состоять из одной или двух дат',

        "is_admin": stat_kwargs.get('is_admin', None),
        "is_admin_description": 'Является ли пользователь админом.'
                                'Если является - в запросе опускается часть с id пользователя',

        "location": stat_kwargs.get('location', None),
        "location_description": 'location_id локации по которой выполняется запрос'
                                'Если отсутствует или None - в запросе опускается часть с location_id',

        'act_number': None, '', int, str
        "act_number_description": 'Если отсутствует или None - в запросе опускается часть с location_id',
        }

        https://ru.stackoverflow.com/questions/988604/
    """
    __part_user: str
    __part_period: str
    __part_location: str
    __part_main_location: str
    __part_normative_documents_id: str
    __part_act_number: str
    __part_short_title: str
    __part_status: str
    __part_finished: str
    __part_violation: str
    __part_hashtags: str
    __part_general_contractor_id: str
    __part_lazy_query: str
    __part_category_id: str
    __part_title: str
    __part_id: str
    __part_week_number: str
    __part_hse_telegram_id: str
    __part_file_id: str

    def __init__(self, chat_id: [str, int] = None, table_name: str = '', **kwargs: object):
        """ """
        super().__init__()
        self.exception = [None, 'all', 'not', 'not including']
        self.main_actions = ['SELECT', 'UPDATE', 'DELETE', 'INSERT']
        self.value = kwargs.get('value', None)

        self.user_id = chat_id
        self.table_name = table_name

        self.type_query = kwargs.get('type_query', None)
        self.user_data_dict = kwargs.get('user_data_dict', None)

        self.action = kwargs.get('action', None)
        self.subject = kwargs.get('subject', None)

        self.conditions: dict = kwargs.get('conditions', None)
        if self.conditions is None:
            return

        self.period = self.conditions.get('period', None)
        self.is_admin = self.conditions.get('is_admin', None)
        self.location = self.conditions.get('location', None)
        self.main_location_id = self.conditions.get('main_location_id', None)
        self.normative_documents_id = self.conditions.get('normative_documents_id', None)

        self.title = self.conditions.get('title', None)

        self.act_number = self.conditions.get('act_number', None)
        self.short_title = self.conditions.get('short_title', None)
        self.status_id = self.conditions.get('status_id', None)
        self.finished_id = self.conditions.get('finished_id', None)
        self.violation_id = self.conditions.get("violation_id", None)
        self.category_id = self.conditions.get("category_id", None)
        self.id = self.conditions.get("id", None)
        self.file_id = self.conditions.get('file_id', None)

        self.lazy_query = self.conditions.get("lazy_query", None)

        self.general_contractor_id = self.conditions.get("general_contractor_id", None)
        self.hashtag = self.conditions.get('hashtag', None)
        self.week_number = self.conditions.get('week_number', None)
        self.hse_telegram_id = self.conditions.get('hse_telegram_id', None)

    async def prepare_data(self) -> str:
        """Формирование частей запроса """
        self.action = await self.get_action_part()
        self.subject = await self.get_subject_part()

        if self.action == "SELECT":
            self.main_part = await self.get_main_part_select()
        if self.action == "UPDATE":
            self.main_part = await self.get_main_part_update()

        self.__part_user = await self.get_part_is_admin()
        self.__part_period = await self.get_part_period()
        self.__part_main_location = await self.get_part_main_location()
        self.__part_location = await self.get_part_location()
        self.__part_act_number = await self.get_part_act_number()
        self.__part_short_title = await self.get_part_short_title()
        self.__part_status = await self.get_part_status()
        self.__part_finished = await self.get_part_finished()
        self.__part_violation = await self.get_part_violation()
        self.__part_category_id = await self.get_part_category_id()
        self.__part_normative_documents_id = await self.get_normative_documents_id()
        self.__part_title = await self.get_part_title()
        self.__part_id = await self.get_part_id()
        self.__part_general_contractor_id = await self.get_general_contractor_id()
        self.__part_hashtags = await self.get_part_hashtags()
        self.__part_lazy_query = await self.get_part_lazy_query()
        self.__part_week_number = await self.get_part_week_number()
        self.__part_hse_telegram_id = await self.get_part_hse_telegram_id()
        self.__part_file_id = await self.get_part_file_id()

        # if self.action == 'UPDATE':
        #     self.query = await self.get_query_update()
        #
        # if self.action == 'SELECT':
        #     self.query = await self.get_query_select()

        self.query = await self.get_query()
        logger.debug(f'\nQueryConstructor: {self.query = }')
        return self.query

    async def get_action_part(self) -> str:
        """Формирование основной части action запроса """

        if self.action in self.main_actions:
            self.action = self.action.upper()
            return self.action
        logger.error(f"{self.action = } not in self.main_actions")

    async def get_subject_part(self):
        """Формирование части запроса """
        if not self.subject: return '*'
        if self.subject: return f"{self.subject}"

    async def get_main_part_select(self) -> str:
        """Формирование основной части запроса """
        self.main_part = f'{self.action} {self.subject} FROM `{self.table_name}` '

        if self.conditions:
            self.main_part = f'{self.action} {self.subject} FROM `{self.table_name}` WHERE '

        return self.main_part

    async def get_main_part_update(self) -> str:
        self.main_part = f"{self.action} `{self.table_name}` SET `{self.subject}` = '{self.value}' "

        if self.conditions:
            self.main_part = f"{self.action} `{self.table_name}` SET `{self.subject}` = '{self.value}' WHERE "

        return self.main_part

    async def get_query(self) -> str:
        """Формирование запроса SELECT
        атрибуты не равные '' или None
        нужные self._part_* не равные '' или None

        :return: str query
        """
        parts: list = [part.split('__')[-1] for part in self.__dict__ if (self.__dict__[part] and '__' in part)]
        logger.debug(f'{parts = }')
        conditions: list = [
            str(getattr(self, f'_{self.__class__.__name__}__{key}'))
            for key in parts
            if hasattr(self, f'_{self.__class__.__name__}__{key}')
        ]
        logger.debug(f'{conditions = }')

        return self.main_part + ' AND '.join(cond for cond in conditions if cond)


async def test():
    """Функция тестирования """
    pass
    # now = datetime.now()
    # stat_date_period: list = ['01.01.2023', now.strftime("%d.%m.%Y"), ]
    # logger.info(f"{stat_date_period = }")
    #
    # kwargs = {
    #     "action": 'SELECT', "subject": '*',
    #     "conditions": {
    #         "period": stat_date_period,
    #         "location": 2
    #     }
    # }
    # query = await QueryConstructor(None, 'core_violations', **kwargs).prepare_data()
    #
    # db_table_name = 'core_normativedocuments'
    # hashtag_test = '#Документация'
    # query_test: str = f"SELECT * FROM {db_table_name} WHERE `category_id` == {16} AND `hashtags` LIKE '%{hashtag_test}%'"
    #
    # kwargs = {
    #     "action": 'SELECT', "subject": 'hashtags',
    #     "conditions": {
    #         # "hashtag": hashtag_test,
    #         # "hashtag_condition": 'like',
    #         "category_id": 16
    #     }
    # }
    # query_test = await QueryConstructor(None, db_table_name, **kwargs).prepare_data()
    #
    # query_test = "SELECT hashtags  FROM `core_sublocation` WHERE `main_location_id` = '1' "
    # datas_query: list = await db_get_data_list(query=query_test)
    # print(f'{len(datas_query) = }')
    #
    # data = [item[0] for item in datas_query if item[0]]
    # print(f'{len(data) = }')
    # print(f'{data = }')
    #
    # list_of_lists = [item.split(';') for item in data if item]
    # print(f'{len(list_of_lists) = }')
    # print(f'{list_of_lists = }')
    #
    # data_unpac = [item for sublist in list_of_lists for item in sublist]
    # print(f'{len(data_unpac) = }')
    # print(f'{data_unpac = }')
    #
    # data = [item[0] for item in datas_query if item[0]]
    # list_of_lists = [item[0].split(';') for item in datas_query if isinstance(item[0], str)]
    # data_unpac = [item for sublist in list_of_lists for item in sublist]
    # print(f'{len(data_unpac) = }')
    #
    # unique_item = list(set(data_unpac))
    # print(f'{len(unique_item) = }')
    # print(f'{unique_item = }')


if __name__ == '__main__':
    asyncio.run(test())
