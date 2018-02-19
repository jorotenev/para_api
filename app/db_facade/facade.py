import warnings
import boto3
from boto3.dynamodb.conditions import Key, And
from decimal import Decimal

from app.db_facade.misc import OrderingDirection
from app.helpers.utils import deadline
from app.db_facade.table_schema import index_for_property
from app.models.json_schema import expense_properties

from config import EnvironmentName
from tests.common_methods import is_valid_expense
from .table_schema import range_key, hash_key
from .dynamodb.reserved_attr_names import reserved_attr_names

"""
http://boto3.readthedocs.io/en/latest/reference/services/dynamodb.html
"""
raw_db = None
"""
https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ReservedWords.html
we know the property names of an expense. in this dict we keep valid property names that can
be used in query expressions.
"""
escaped_attr_names = {}
for property in expense_properties:
    safe_property_name = property
    if property.upper() in reserved_attr_names:
        safe_property_name = "#%s" % safe_property_name
    escaped_attr_names[safe_property_name] = property


class ItemConverter(object):
    def convertToDbFormat(self, exp: dict):
        copy = exp.copy()
        for key, value in copy.items():
            if type(value) in [int, float]:
                copy[key] = self.convertNumberToDbFormat(str(value))

        return copy

    def convertFromDbFormat(self, exp):
        copy = exp.copy()
        for key, value in copy.items():
            if isinstance(value, Decimal):
                copy[key] = self.convertNumberFromDbFormat(value)
        return copy

    def convertNumberToDbFormat(self, num):
        return Decimal(num)

    def convertNumberFromDbFormat(self, num):
        if isinstance(num, Decimal):
            return int(num) if num % 1 == 0 else float(num)
        else:
            return num


class __DbFacade(object):
    EXPENSES_TABLE_NAME_PREFIX = 'expenses-'
    HASH_KEY = hash_key
    RANGE_KEY = range_key
    EXPENSES_TABLE_NAME = EXPENSES_TABLE_NAME_PREFIX

    converter = ItemConverter()
    reserved_dynamodb_words = ['name']

    def __init__(self):
        self.expenses_table = None
        self.lazy_ping = False

    def init_app(self, app):
        global raw_db

        self.EXPENSES_TABLE_NAME = (self.EXPENSES_TABLE_NAME_PREFIX + app.config['APP_STAGE']).lower()
        self.lazy_ping = app.config['DB_PING_LAZY']
        kwargs = {}
        if app.config['APP_STAGE'] in [EnvironmentName.development, EnvironmentName.testing]:
            local_dynamodb_url = app.config['LOCAL_DYNAMODB_URL']

            kwargs['endpoint_url'] = local_dynamodb_url

        raw_db = boto3.resource('dynamodb', **kwargs)
        self.ping_db(raw_db)

        self.raw_db = raw_db
        self.expenses_table = raw_db.Table(self.EXPENSES_TABLE_NAME)

    @deadline(3, "Fail fast. DB health check failed. Is the table created and is the db reachable?")
    def ping_db(self, db):

        """
        makes a simple request to dynamodb to ensure that there's connectivity. will fail fast if there isn't
        :return:
        :raises Exception - if the db is not available
        """
        try:

            list(db.tables.all())  # this can timeout if the db is not up

            if self.lazy_ping:
                print("lazy pinging the db - not checking if the expenses table exists")
            else:
                assert len(list(db.tables.all())), "No tables created!"

                assert self.EXPENSES_TABLE_NAME in [t.name for t in
                                                    db.tables.all()], "%s doesn't exist!" % self.EXPENSES_TABLE_NAME

            print("Valid connection to the DynamoDB. Endpoint url [%s]" % db.meta.client.meta.endpoint_url)
        except Exception as err:
            raise Exception("DB not ready. raw error: " + str(err))

    def validate_get_list(self, property_name, ordering_direction, batch_size):
        if property_name not in index_for_property.keys():
            raise UnindexedPropertySelected("%s is not allowed as query-able property" % property_name)

        assert type(ordering_direction) is OrderingDirection, \
            "%s is not a valid ordering_direction" % ordering_direction

        if batch_size > MAX_BATCH_SIZE:
            warnings.warn("%i is above MAX_BATCH_SIZE=%i. Capping the parameter to the max allowed value." % (
                batch_size, MAX_BATCH_SIZE))

    def get_list(self,
                 property_value,
                 user_uid,
                 property_name='timestamp_utc',
                 ordering_direction: OrderingDirection = OrderingDirection.desc,
                 batch_size=25):
        """
        :param property_value:  the value of the property `property_name`. could be None
        :param property_name: which expense property to use as sort key
        :param user_uid:
        :param ordering_direction: OrderingDirection instance
        :param batch_size: int
        :return: list of expense objects

        :raises UnindexedPropertySelected if `property_name` is not a property that can be used to query
        """

        # validation
        self.validate_get_list(property_name, ordering_direction, batch_size)
        batch_size = min(batch_size, MAX_BATCH_SIZE)

        property_is_main_sort_key = index_for_property[property_name] is None

        # configure the query
        escaped_expense_properties = []

        query_kwargs = {
            "Select": "SPECIFIC_ATTRIBUTES",
            "ProjectionExpression": ", ".join(escaped_attr_names.keys()),
            "ExpressionAttributeNames": {k: escaped_attr_names[k] for k in escaped_attr_names if k.startswith("#")},
            "Limit": batch_size,
            "ConsistentRead": False,
            "ScanIndexForward": True if ordering_direction is OrderingDirection.asc else False,
        }

        # choose which index to query, if applicable
        if property_name in index_for_property.keys():
            if not property_is_main_sort_key:
                query_kwargs['IndexName']: index_for_property[property_name]
                query_kwargs['TableName'] = self.EXPENSES_TABLE_NAME

        # configure the hash and sort keys
        if not property_value:
            # e.g. if querying via timestamp_utc, desc - search will start from the newest items
            query_kwargs['KeyConditionExpression'] = Key(self.HASH_KEY).eq(user_uid)
        else:
            # e.g. if querying via timestamp_utc, desc - search will start from the given property_value
            sort_key_cond = Key(property_name).gt if ordering_direction is OrderingDirection.asc else Key(
                property_name).lt

            query_kwargs['KeyConditionExpression'] = And(Key(self.HASH_KEY).eq(user_uid), sort_key_cond(property_value))

        result = self.expenses_table.query(**query_kwargs)['Items']
        result = [self.converter.convertFromDbFormat(e) for e in result]
        ready_expenses = list(filter(is_valid_expense, result))

        if len(ready_expenses) is not len(result):
            warnings.warn("%i invalid expenses in the response were discarded!" % (len(ready_expenses) - len(result)))

        return ready_expenses

    def persist(self, expense, user_uid):
        """

        :param expense: expense with `id` parameter set to None
        :param user_uid:
        :return: the persisted expense
        :raises
        """

    def update(self, expense, old_expense, user_uid):
        """

        :param expense: a valid expense object with an `id`. the updated expense.
        :param old_expense: a valid expense object with an `id`. the state of `expense` before it was updated
        :param user_uid:
        :return: upon success, the expense, but with updated timestamp_utc_updated
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


class UnindexedPropertySelected(Exception):
    def __init__(self, *args):
        super(UnindexedPropertySelected, self).__init__(*args)


MAX_BATCH_SIZE = 25
db_facade = __DbFacade()
