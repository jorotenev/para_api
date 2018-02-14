import boto3
from decimal import Decimal

from app.helpers.utils import deadline
from config import EnvironmentName

raw_db = None
dynamodb_users_table_init_information = {
    "KeySchema": [
        {
            'AttributeName': 'user_uid',
            'KeyType': 'HASH'  # Partition key
        },
        {
            'AttributeName': 'id',
            'KeyType': 'RANGE'  # Sort key
        }
    ],
    "AttributeDefinitions": [
        {
            'AttributeName': 'user_uid',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'id',
            'AttributeType': 'N'
        },

    ],
    "ProvisionedThroughput": {"ReadCapacityUnits": 3, "WriteCapacityUnits": 3}
}


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


class __DbFacade(object):
    EXPENSES_TABLE_NAME_PREFIX = 'expenses-'
    HASH_KEY = 'user_uid'
    RANGE_KEY = 'id'
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

    @deadline(3, "The db didn't respond within the time limit")
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

    def get_single(self, expense_id, user_id):
        """
        :param expense_id:
        :param user_id:
        :return: the expense object
        :raises NoExpenseWithThisId
        """

    def get_list(self, start_id, user_uid, batch_size):
        """
        :param start_id: inclusive, from where to start the search
        :param user_uid: the user for which to search
        :param batch_size: how many items (at most)
        :return: a list of expense objects
        :raises NoSuchUser
        """
        batch_size = min(batch_size, MAX_BATCH_SIZE)
        return None

    def persist(self, expense, user_uid):
        """

        :param expense: expense with `id` parameter set to None
        :param user_uid:
        :return: the persisted expense
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

    def remove(self, expense_id, user_uid):
        """

        :param expense_id: int
        :param user_uid:
        :return: boolean True on successful deletion
        :raises NoSuchUser
        :raises NoExpenseWithThisId
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

    def asd(self):
        return self.db_url


class NoSuchUser(Exception):
    """
    Raised when an operation was performed using an uid, but there's no
    user with such uid
    """

    def __init__(self, *args, **kwargs):
        super(Exception, self).__init__(*args, **kwargs)


class NoExpenseWithThisId(Exception):
    def __init__(self, *args, **kwargs):
        super(Exception, self).__init__(*args, **kwargs)


MAX_BATCH_SIZE = 100
db_facade = __DbFacade()
