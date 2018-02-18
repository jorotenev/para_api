from enum import Enum

import boto3
from decimal import Decimal

from app.helpers.utils import deadline
from config import EnvironmentName

"""
http://boto3.readthedocs.io/en/latest/reference/services/dynamodb.html
"""
raw_db = None


class ItemConverter(object):
    def convertToDbFormat(self, exp: dict):
        copy = exp.copy()
        for key, value in copy.items():
            if type(value) in [int, float]:
                copy[key] = Decimal(value)

        return copy

    def convertFromDbFormat(self, exp):
        copy = exp.copy()
        for key, value in copy.items():
            if isinstance(value, Decimal):
                copy[key] = int(value) if value % 1 == 0 else float(value)
        return copy


class OrderingDirection(Enum):
    asc = 'asc'
    desc = 'desc'

    @classmethod
    def is_member(cls, candidate: str):
        return candidate in [ord.name for ord in OrderingDirection]


class __DbFacade(object):
    EXPENSES_TABLE_NAME_PREFIX = 'expenses-'
    HASH_KEY = 'user_uid'
    RANGE_KEY = 'timestamp_utc'
    EXPENSES_TABLE_NAME = EXPENSES_TABLE_NAME_PREFIX

    converter = ItemConverter()

    def __init__(self):
        self.db_url = None

    def init_app(self, app):
        global raw_db
        self.EXPENSES_TABLE_NAME = self.EXPENSES_TABLE_NAME_PREFIX + app.config['APP_STAGE'].lower()
        kwargs = {}
        if app.config['APP_STAGE'] in [EnvironmentName.development, EnvironmentName.testing]:
            local_dynamodb_url = app.config['LOCAL_DYNAMODB_URL']
            kwargs['endpoint_url'] = local_dynamodb_url

        raw_db = boto3.resource('dynamodb', **kwargs)
        self.ping_db(raw_db)

        self.raw_db = raw_db

    @deadline(3, "DB health check failed. Is the table created and is the db reachable?")
    def ping_db(self, db):

        """
        makes a simple request to dynamodb to ensure that there's connectivity. will fail fast if there isn't
        :return:
        :raises Exception - if the db is not available
        """
        try:
            len(list(db.tables.all()))
            print("valid connection to the DynamoDB. Endpoint url [%s]" % db.meta.client.meta.endpoint_url)
        except Exception as err:
            raise Exception("DB not ready. raw error: " + str(err))

    def get_list(self,
                 property_value,
                 user_uid,
                 property_name='timestamp_utc',
                 ordering_direction='desc',
                 batch_size=25):
        """
        :param property_value:  the value of the property `property_name`
        :param property_name: which expense property to use as sort key
        :param user_uid:
        :param ordering_direction: OrderingDirection instance
        :param batch_size: int
        :return: list of expense objects
        """
        return None

    def persist(self, expense, user_uid):
        """

        :param expense: expense with `id` parameter set to None
        :param user_uid:
        :return: the persisted expense
        :raises
        """

    def update(self, expense, user_uid):
        """

        :param expense: a valid expense object with an `id`
        :param user_uid:
        :return: upon success, the expense, but with update timestamp_utc_updated
        :raises ValueError - expense doesn't have the `id` set to a non-None value
        :raises NoExpenseWithThisId
        :raises NoSuchUser
        """
        pass

    def remove(self, expense, user_uid):
        """
        :param expense: expense object
        :param user_uid:
        :return: boolean True on successful deletion
        :raises NoSuchUser
        :raises NoExpenseWithThisId
        :returns void
        """

    def sync(self, sync_request_objs, user_uid):
        """

        :param sync_request_objs: a list of dicts with `id` and `timestamp_utc_updated`
        :return:
        :raises NoSuchUser
        """

    def expense_exists(self, exp_id, user_uid):
        """
        :param exp_id:
        :param user_uid:
        :return: boolean
        :raises NoSuchUser
        """

    def largest_expense_id(self, user_uid):
        """
        :param user_uid:
        :return: int | None
        :raises  NoSuchUser
        """


class NoSuchUser(Exception):
    """
    Raised when an operation was performed using an uid, but there's no
    user with such uid
    """

    def __init__(self, *args):
        super(NoSuchUser, self).__init__(*args)


class NoExpenseWithThisId(Exception):
    def __init__(self, *args):
        super(NoExpenseWithThisId, self).__init__(*args)


class PersistFailed(Exception):
    def __init__(self, *args):
        super(PersistFailed, self).__init__(*args)


dynamodb_users_table_init_information = {
    "KeySchema": [
        {
            'AttributeName': __DbFacade.HASH_KEY,
            'KeyType': 'HASH'  # Partition key
        },
        {
            'AttributeName': __DbFacade.RANGE_KEY,
            'KeyType': 'RANGE'  # Sort key
        }
    ],
    "AttributeDefinitions": [
        {
            'AttributeName': __DbFacade.HASH_KEY,
            'AttributeType': 'S'
        },
        {
            'AttributeName': __DbFacade.RANGE_KEY,
            'AttributeType': 'S'
        },

    ],
    "ProvisionedThroughput": {"ReadCapacityUnits": 3, "WriteCapacityUnits": 3}
}
MAX_BATCH_SIZE = 25
db_facade = __DbFacade()
