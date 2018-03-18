import uuid
import warnings
from decimal import Decimal
from itertools import groupby

import boto3
from boto3.dynamodb.conditions import Key, And, Attr

from app.db_facade.misc import OrderingDirection
from app.db_facade.table_schema import index_for_property
from app.helpers.time import utc_now_str
from app.helpers.utils import deadline
from app.models.expense_validation import Validator
from app.models.json_schema import expense_properties
from config import EnvironmentName
from .dynamodb.reserved_attr_names import reserved_attr_names
from .table_schema import range_key, hash_key

"""
http://boto3.readthedocs.io/en/latest/reference/services/dynamodb.html
"""
raw_db = None
expense_type = dict
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
# to be included in queries if all expense properties are to be retrieved (EXcluding item attributes that don't belong
# to the expense schema). handles property names which are Dynamodb reserved words
projection_expr_expenseONLY_attrs = {
    "ProjectionExpression": ", ".join(escaped_attr_names.keys()),
    "ExpressionAttributeNames": {k: escaped_attr_names[k] for k in escaped_attr_names if k.startswith("#")},
}


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
        if len(copy['tags']) == 0:
            # dynamodb doesn't accept empty lists
            del copy['tags']
        if not copy['name']:
            del copy['name']
        return copy

    def convertFromDbFormat(self, exp):
        copy = exp.copy()
        for key, value in copy.items():
            if isinstance(value, Decimal):
                copy[key] = self.convertNumberFromDbFormat(value)
        if 'tags' not in copy:
            copy['tags'] = []
        if 'name' not in copy:
            copy['name'] = ''
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

            if expected_type == expense_type:
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

    DEFAULT_ORDERING = OrderingDirection.desc
    converter = ExpenseConverter()
    reserved_dynamodb_words = ['name']

    def __init__(self):
        self.expenses_table = None
        self.lazy_ping = False
        self.max_sync_request_size = 10  # default. overridden in init_app()

    def init_app(self, app):
        global raw_db

        self.EXPENSES_TABLE_NAME = (self.EXPENSES_TABLE_NAME_PREFIX + app.config['APP_STAGE']).lower()
        self.lazy_ping = app.config['DB_PING_LAZY']
        kwargs = {}
        if app.config['APP_STAGE'] in [EnvironmentName.development, EnvironmentName.testing]:
            local_dynamodb_url = app.config['LOCAL_DYNAMODB_URL']
            print("Will attempt to connect to a local DynamoDB instance")
            kwargs['endpoint_url'] = local_dynamodb_url
        else:
            print("Will attempt to connect to an AWS instance of DynamoDB")

        raw_db = boto3.resource('dynamodb', **kwargs)
        print("Target DynamoDB endpoint %s" % raw_db.meta.client.meta.endpoint_url)
        self.ping_db(raw_db)
        self.raw_db = raw_db
        self.expenses_table = raw_db.Table(self.EXPENSES_TABLE_NAME)
        self.max_sync_request_size = app.config['MAX_SYNC_REQUEST_SIZE']

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
                 ordering_direction: OrderingDirection = DEFAULT_ORDERING,
                 batch_size=25,
                 inclusive_start=False):
        """
        :param property_value:  the value of the property `property_name`. could be None
        :param property_name: which expense property to use as sort key
        :param user_uid:
        :param ordering_direction: OrderingDirection instance
        :param batch_size: int
        :param inclusive_start - only valid if property_value is set. if true, `property_value` will be included in the results
        :return: list of expense objects

        :raises UnindexedPropertySelected if `property_name` is not a property that can be used to query
        """

        # validation
        self.validate_get_list(property_name, ordering_direction, batch_size)
        batch_size = min(batch_size, MAX_BATCH_SIZE)

        property_is_main_sort_key = index_for_property[property_name] is None

        # configure the query
        query_kwargs = {
            **projection_expr_expenseONLY_attrs,
            "Select": "SPECIFIC_ATTRIBUTES",
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
            greater = Key(property_name).gte if inclusive_start else Key(property_name).gt
            less = Key(property_name).lte if inclusive_start else Key(property_name).lt

            # e.g. if querying via timestamp_utc, desc - search will start(exclusive) from the given property_value
            sort_key_cond = greater if ordering_direction is OrderingDirection.asc else less

            query_kwargs['KeyConditionExpression'] = And(Key(self.HASH_KEY).eq(user_uid), sort_key_cond(property_value))

        result = self.expenses_table.query(**query_kwargs)['Items']

        return [self.converter.convertFromDbFormat(e) for e in result]

    @sanitize_response_decorator(expense_type)
    def persist(self, expense, user_uid):
        """
        :param expense: expense with `id` parameter set to None
        :param user_uid:
        :return: the persisted expense
        :raises ItemWithSameRangeKeyExists
        :raises PersistFailed
        """
        expense = expense.copy()
        touch_timestamp(expense, 'timestamp_utc_created')
        touch_timestamp(expense, 'timestamp_utc_updated')
        raw_persisted = self._facade_put_item(context=self.expenses_table, expense=expense, user_uid=user_uid)
        # still has user_uid
        persisted = self.converter.convertFromDbFormat(raw_persisted)

        return persisted

    @sanitize_response_decorator(expense_type)
    def update(self, expense, old_expense, user_uid):
        """

        :param exp: a valid expense object with an `id`. the updated expense.
        :param old_expense: a valid expense object with an `id`. the state of `expense` before it was updated
        :param user_uid:
        :return: upon success, the expense, but with updated timestamp_utc_updated

        :raises ValueError - expense doesn't have the `id` set to a non-None value or the id of the new
                             and old versions don't match
        :raises NoExpenseWithThisId - if there's not expense at rest that has the same `id`. This will be raised
        either when there's no expense with the same key, or when the expense at rest has a different id (which
        is not a valid application state) than `expense`.
        """
        exp = expense.copy()
        old_expense = old_expense.copy()

        if exp['id'] != old_expense['id']:
            raise ValueError("The `id`s of the updated and the old expense don't match")

        touch_timestamp(exp, 'timestamp_utc_updated')

        if exp[self.RANGE_KEY] == old_expense[self.RANGE_KEY]:
            self._standard_update(exp, user_uid)
        else:
            # https://stackoverflow.com/a/30314563/4509634 You can use UpdateItem to update any nonkey attributes.
            self._two_phase_update(exp, old_expense, user_uid)

        return exp

    def remove(self, expense, user_uid):
        """
        :param expense: expense object
        :param user_uid:
        :return: None
        :raises NoExpenseWithThisId
        :returns void
        """
        expense = expense.copy()
        try:
            self.expenses_table.delete_item(
                Key={
                    'user_uid': user_uid,
                    'timestamp_utc': expense['timestamp_utc']
                },
                # ensure that the expense at rest has the same `id` AND that the expense at rest exists at all
                ConditionExpression=And(Attr('id').eq(expense['id']), Attr(self.RANGE_KEY).exists())
            )
        except Exception as err:
            if "ConditionalCheckFailedException" in str(err):
                # either there's not expense with such Key,or the expense at rest has different `id`.
                raise NoExpenseWithThisId()
            else:
                raise err

    def sync(self, sync_request_objs, user_uid):
        """
        given a list from the client of request objects (each containing `timestamp_utc_updated` & the `id` of an expense,
        this method will return which of the input objects the client should remove, add and update.

        :param sync_request_objs: a dict with expense `id` as a key and a dict with a key `timestamp_utc_updated` as value
        {
            "some-expense-id": {"timestamp_utc_updated": "<iso8601>", "timestamp_utc_updated": "<iso8601>"},
            ...
        }
        :return: dict with keys "to_add", "to_remove", "to_update".
        :raises RuntimeError if no LSI is setup
        :raises DynamodbThroughputExhausted - if the operation exhausted the allowed RCUs dedicated to the base table.
        """
        try:
            assert 'id' in index_for_property
            assert index_for_property['id']
        except AssertionError:
            raise RuntimeError("Invalid application state. a LSI with `id` as RANGE key is required for /sync")

        try:
            items = self._sync_get_items(user_uid, sync_request_objs)
            result = self._sync_process_items(items, sync_request_objs)
            convert = self.converter.convertFromDbFormat

            result['to_update'] = [convert(sanitize_expense(e)) for e in result['to_update']]
            result['to_add'] = [convert(sanitize_expense(e)) for e in result['to_add']]

            return result
        except Exception as ex:
            if "ProvisionedThroughputExceededException" in str(ex):
                raise DynamodbThroughputExhausted()
            else:
                raise ex

    def statistics(self, from_dt, to_dt, user_uid):
        query_kwargs = {
            # **projection_expr_expenseONLY_attrs,
            "ProjectionExpression": "currency,amount,timestamp_utc",
            "Select": "SPECIFIC_ATTRIBUTES",
            "ConsistentRead": False,
            "ScanIndexForward": False,  # descending order
            "KeyConditionExpression":
                And(
                    Key("timestamp_utc").between(from_dt, to_dt),
                    Key('user_uid').eq(user_uid)
                )
        }

        result = self.expenses_table.query(**query_kwargs)['Items']
        if result and result[0][
            'timestamp_utc'] == to_dt:  # simulate exclusive lte (between() is inclusive on both sides)
            result.pop(0)
        return self._groupStatisticsItems(result)

    def _groupStatisticsItems(self, items):
        """
        [
            {"currency":"EUR", "amount":10},
            {"currency":"USD", "amount":20},
            {"currency":"EUR", "amount":10},
        ] ===> {"EUR":20, "USD":20}
        """
        key = lambda k: k['currency']
        items.sort(key=key)

        def shrt_num(x): return float("%.2f" % x)

        list_of_dicts = [
            {
                currencyName:
                    shrt_num(sum(self.converter.convertNumberFromDbFormat((i['amount'])) for i in itemsOfSameCurrency))}
            for (currencyName, itemsOfSameCurrency)
            in groupby(items, key=key)
        ]
        result = {}
        for d in list_of_dicts:
            result.update(d)
        return result

    def _sync_get_items(self, user_uid, request_objects):
        choose = max if self.DEFAULT_ORDERING is OrderingDirection.desc else min
        start_timestamp = choose([exp['timestamp_utc'] for exp in request_objects.values()])
        from_db = self.get_list(user_uid=user_uid,
                                property_name='timestamp_utc',
                                property_value=None,
                                ordering_direction=self.DEFAULT_ORDERING,
                                batch_size=self.max_sync_request_size,
                                )
        result = {}
        for exp in from_db:
            result[exp['id']] = exp
        return result

    def _sync_process_items(self, items_from_db, request_objects):
        """
        :param items_from_db: a dict with key an expense `id` and value the expense
        :param request_objects: list of (`id`, `timestamp_utc_updated`) objects
        :return: see `sync()`
        """
        result = {
            'to_add': [],
            'to_remove': [],
            'to_update': []
        }

        ids_on_db = set(items_from_db.keys())
        ids_on_client = set(request_objects.keys())

        ids_on_db_only = ids_on_db - ids_on_client  # https://docs.python.org/3.6/library/stdtypes.html#frozenset.difference
        ids_on_client_only = ids_on_client - ids_on_db
        ids_on_both = ids_on_db & ids_on_client  # https://docs.python.org/3.6/library/stdtypes.html#frozenset.intersection

        result['to_remove'] = list(ids_on_client_only)
        result['to_add'] = [items_from_db[item_id] for item_id in ids_on_db_only]

        ts_key = 'timestamp_utc_updated'
        result['to_update'] = [items_from_db[exp_id] for exp_id in ids_on_both if
                               items_from_db[exp_id][ts_key] > request_objects[exp_id][ts_key]]

        return result

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

        :raises see _facade_put_item
        """

        # delete the old expense and put the updated one in a single batch
        # it's fine because they have different sort keys

        updated = self._facade_put_item(context=self.expenses_table, expense=expense, user_uid=user_uid, add_id=False)

        # wouldn't delete the old expense if the put_item above raised an exception (ItemWithSameRangeKeyExists)
        self.expenses_table.delete_item(Key={

            'user_uid': user_uid,
            'timestamp_utc': old_expense['timestamp_utc']
        })
        return updated

    def _facade_put_item(self, context, expense, user_uid, add_id=True):
        """
        prepares an expense for persisting and writes it to the db.
        returns the item that was written to the db

        :param context: either a Table object or a  batch_writer (http://boto3.readthedocs.io/en/latest/reference/services/dynamodb.html#DynamoDB.Table.batch_writer)
        :param expense: as received by the client. id is None
        :param user_uid:
        :return: the expense, as it was persisted

        :raises ItemWithSameSortKeyExists
        :raises PersistFailed
        """
        exp = expense.copy()
        if add_id:
            if (expense['id']):
                raise RuntimeError('dangerous operation. cannot add id to an expense which already has id')
            exp['id'] = str(uuid.uuid4())
        exp['user_uid'] = user_uid

        query_kwargs = {
            "ConditionExpression": Attr(self.RANGE_KEY).not_exists()
        }

        try:
            context.put_item(
                Item=self.converter.convertToDbFormat(exp),
                **query_kwargs)

            return exp
        except Exception as ex:
            if "ConditionalCheckFailedException" in str(ex):
                raise ItemWithSameRangeKeyExists("Item with RANGE key %s already exists" % exp[self.RANGE_KEY])
            elif "One of the required keys was not given a value" in str(ex):
                raise PersistFailed(str(ex))
            else:
                raise ex


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


class DynamodbThroughputExhausted(Exception):
    def __init__(self, *args):
        super(DynamodbThroughputExhausted, self).__init__(*args)


class ItemWithSameRangeKeyExists(Exception):
    def __init__(self, *args):
        super(ItemWithSameRangeKeyExists, self).__init__(*args)


MAX_BATCH_SIZE = 25
db_facade = __DbFacade()
