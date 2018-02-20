import uuid
import warnings
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key, And, Attr

from app.db_facade.misc import OrderingDirection
from app.db_facade.table_schema import index_for_property
from app.helpers.time import utc_now_str
from app.helpers.utils import deadline
from app.models.json_schema import expense_properties
from config import EnvironmentName
from tests.common_methods import is_valid_expense
from .dynamodb.reserved_attr_names import reserved_attr_names
from .table_schema import range_key, hash_key

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


def touch_timestamp(expense, ts_property):
    assert ts_property in expense
    expense[ts_property] = utc_now_str()


class ExpenseConverter(object):
    """
    responsible for converting expenses from/to format accepted by DynamoDB
    """

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


def sanitize_expense(exp):
    """
    Removes any properties from an expense that should only exist within the facade
    and should not be visible for the clients of the facade
    :param exp:
    :return:
    """
    if 'user_uid' in exp:
        del exp['user_uid']
    return exp


def sanitize_response_decorator(expected_type):
    def decorate(f):
        def new_f(*args, **kwargs):
            resp = f(*args, **kwargs)

            assert type(resp) == expected_type

            if expected_type == dict:
                return sanitize_expense(resp)
            elif expected_type == list:
                return list(map(sanitize_expense, resp))
            else:
                raise ValueError()

        return new_f

    return decorate


class __DbFacade(object):
    EXPENSES_TABLE_NAME_PREFIX = 'expenses-'
    HASH_KEY = hash_key
    RANGE_KEY = range_key
    EXPENSES_TABLE_NAME = EXPENSES_TABLE_NAME_PREFIX

    converter = ExpenseConverter()
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

    @sanitize_response_decorator(list)
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
        touch_timestamp(expense, 'timestamp_utc_created')
        touch_timestamp(expense, 'timestamp_utc_updated')

    @sanitize_response_decorator(dict)
    def update(self, expense, old_expense, user_uid):
        """

        :param expense: a valid expense object with an `id`. the updated expense.
        :param old_expense: a valid expense object with an `id`. the state of `expense` before it was updated
        :param user_uid:
        :return: upon success, the expense, but with updated timestamp_utc_updated

        :raises ValueError - expense doesn't have the `id` set to a non-None value or the id of the new
                             and old versions don't match
        :raises NoExpenseWithThisId - if there's not expense at rest that has the same `id`. This will be raised
        either when there's no expense with the same key, or when the expense at rest has a different id (which
        is not a valid application state) than `expense`.
        """
        expense = expense.copy()
        old_expense = old_expense.copy()

        if expense['id'] != old_expense['id']:
            raise ValueError("The `id`s of the updated and the old expense don't match")

        touch_timestamp(expense, 'timestamp_utc_updated')

        if expense[self.RANGE_KEY] == old_expense[self.RANGE_KEY]:
            self._standard_update(expense, user_uid)
        else:
            # https://stackoverflow.com/a/30314563/4509634 You can use UpdateItem to update any nonkey attributes.
            self._two_phase_update(expense, old_expense, user_uid)

        return expense

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

    def _standard_update(self, expense, user_uid):
        """
        given that there's already an item with the same hash and range keys,
        use the `expense` will replace the existing item.
        :param expense:
        :param user_uid:
        :return:
        :raises NoExpenseWithThisId if there's no expense with the same key found to update
                                    OR the expense at rest has a different `id`
        """
        try:
            previous_exp = self.expenses_table.put_item(
                Item=self.converter.convertToDbFormat({'user_uid': user_uid, **expense}),
                ReturnValues="ALL_OLD",
                # only replace if the item in the db and the updated item have the same id
                ConditionExpression=Attr('id').eq(expense['id'])
            )
            return previous_exp['Attributes'] if 'Attributes' in previous_exp else None
        except Exception as ex:
            if "ConditionalCheckFailedException" in str(ex):
                raise NoExpenseWithThisId \
                    ("no expense at rest found to update or the id of the expense at rest is not the same. "
                     "When trying to update the item, the item at rest had a different `id` attr")
            else:
                raise ex

    def _two_phase_update(self, expense, old_expense, user_uid):
        """
        This is only needed if the change in the newly update expense was to a property that we use as a SORT key
        in the main index
        :param expense:
        :param old_expense:
        :param user_uid:
        :return:
        """

        # delete the old expense and put the updated one in a single batch
        # it's fine because they have different sort keys
        with self.expenses_table.batch_writer() as batch:
            batch.delete_item(Key={
                'user_uid': user_uid,
                'timestamp_utc': old_expense['timestamp_utc']
            })
            self._facade_put_item(batch, expense=expense, user_uid=user_uid)

    def _facade_put_item(self, context, expense, user_uid):
        """
        prepares an expense for persisting and writes it to the db.
        returns the item that was written to the db

        :param context: either a Table object or a  batch_writer (http://boto3.readthedocs.io/en/latest/reference/services/dynamodb.html#DynamoDB.Table.batch_writer)
        :param expense: as received by the client. id is None
        :param user_uid:
        :return: the expense, as it was persisted
        """
        exp = expense.copy()
        exp['id'] = uuid.uuid4()
        exp['user_uid'] = user_uid
        context.put_item(Item=self.converter.convertToDbFormat(exp))

        return exp


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
