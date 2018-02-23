import json
from flask import request, current_app
from app.api_utils.response import make_json_response, make_error_response
from app.db_facade import db_facade
from app.db_facade.facade import MAX_BATCH_SIZE, NoExpenseWithThisId, DynamodbThroughputExhausted
from app.db_facade.misc import OrderingDirection
from app.expenses_api.api_error_msgs import ApiError
from app.models.expense_validation import Validator
from . import expenses_api
from app.models.json_schema import expense_schema
from functools import wraps


def needs_firebase_uid(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        firebase_token = current_app.config['TEST_FIREBASE_UID']  # TODO
        try:
            request.headers[current_app.config['CUSTOM_AUTH_HEADER_NAME']]
        except:
            return make_error_response("can't find auth token", status_code=403)
        return f(*args, **kwargs, user_uid=firebase_token)

    return decorated


@expenses_api.route("/test", methods=['GET'])
def test():
    return request.get_json(force=True)


@expenses_api.route("/honeypot", methods=['GET', 'POST', 'PUT', 'DELETE'])
@needs_firebase_uid
def honeypot(user_uid=None):
    """
    endpoint used to verify that protected routes require auth
    :return:
    """
    assert user_uid
    return 'sweet'


def validate_get_expenses_list_property_value(property_name, property_value, none_is_ok=True):
    assert property_name in expense_schema['properties'].keys(), "%s is not a valid expense property" % property_name
    if not none_is_ok and property_value is None:
        assert "%s cannot be None" % property_name

    if property_value is not None:
        assert Validator.validate_property(property_value, property_name), '%s is not a valid value for %s' % \
                                                                           (str(property_value), property_name)


@expenses_api.route("/get_expenses_list", methods=['GET'])
@needs_firebase_uid
def get_expenses_list(user_uid=None):
    property_name = request.args.get('start_from_property', default='timestamp_utc')
    property_value = request.args.get('start_from_property_value', default=None)
    ordering_direction = request.args.get("ordering_direction", default='desc')
    expense_id = request.args.get("start_from_id", default=None)
    batch_size = request.args.get('batch_size', type=int, default=10)

    try:
        validate_get_expenses_list_property_value(property_name, property_value)
        assert OrderingDirection.is_member(ordering_direction), ApiError.INVALID_ORDER_PARAM

        if property_value:
            assert expense_id, "If a property_value is set, the start_from_id is mandatory"

        assert batch_size < MAX_BATCH_SIZE, ApiError.BATCH_SIZE_EXCEEDED
        assert batch_size > 0, ApiError.INVALID_BATCH_SIZE
    except AssertionError as ex:
        status_code = 400
        if ApiError.BATCH_SIZE_EXCEEDED in str(ex):
            status_code = 413

        return make_json_response(json.dumps({
            'error': "%s. %s" % (ApiError.INVALID_QUERY_PARAMS, str(ex))
        }), status_code=status_code)

    ordering_direction = OrderingDirection[ordering_direction]

    response = db_facade.get_list(
        property_value=property_value,
        property_name=property_name,
        ordering_direction=ordering_direction,
        user_uid=user_uid,
        batch_size=batch_size
    )

    return make_json_response(response)


def validate_persist_request(expense):
    is_valid, err_msg = Validator.validate_expense(expense)
    assert is_valid, "%s %s" % (ApiError.INVALID_EXPENSE, err_msg)
    assert expense['id'] == None, ApiError.ID_PROPERTY_FORBIDDEN  # must be non


@expenses_api.route('/persist', methods=['POST'])
@needs_firebase_uid
def persist(user_uid=None):
    expense = request.get_json(force=True, silent=True)
    try:
        validate_persist_request(expense)
    except AssertionError as e:

        return make_error_response(str(e), status_code=400)
    persisted = db_facade.persist(expense=expense, user_uid=user_uid)

    return make_json_response(persisted, status_code=200)


@expenses_api.route('/update', methods=['PUT'])
@needs_firebase_uid
def update(user_uid=None):
    request_data = request.get_json(force=True, silent=True)
    is_valid, error_msg = validate_update_request(request_data)
    if not is_valid:
        return make_error_response(error_msg, 400)

    try:
        result = db_facade.update(request_data['updated'], request_data['previous_state'], user_uid)
        return make_json_response(result)
    except NoExpenseWithThisId as err:
        return make_error_response(ApiError.NO_EXPENSE_WITH_THIS_ID, status_code=404)
    except ValueError as err:
        return make_error_response(ApiError.IDS_OF_EXPENSES_DONT_MATCH, status_code=400)


def validate_update_request(request_data):
    try:
        assert request_data, ApiError.EMPTY_REQUEST_BODY
        assert 'updated' in request_data, '`updated` field not in the request body'
        assert 'previous_state' in request_data, ApiError.PREVIOUS_STATE_OF_EXP_MISSING

        check_valid = [('updated', request_data['updated']), ('previous_state', request_data['previous_state'])]
        for field, value in check_valid:
            is_valid, _ = Validator.validate_expense(value)
            assert is_valid, "%s is not a valid expense" % field
            assert 'id' in value and value['id'], ApiError.ID_PROPERTY_MANDATORY
    except AssertionError as err:
        return False, str(err)

    return True, None


def validate_remove_request(request_data):
    assert request_data, ApiError.EMPTY_REQUEST_BODY
    assert Validator.validate_expense_simple(request_data), ApiError.INVALID_EXPENSE
    assert 'id' in request_data and request_data['id'], ApiError.ID_PROPERTY_MANDATORY


@expenses_api.route('/remove', methods=['DELETE'])
@needs_firebase_uid
def remove(user_uid=None):
    expense_to_delete = request.get_json(force=True, silent=True)
    try:
        validate_remove_request(expense_to_delete)
    except AssertionError as err:
        return make_error_response(str(err), status_code=400)

    try:
        db_facade.remove(expense=expense_to_delete, user_uid=user_uid)
        return make_json_response('[]')
    except NoExpenseWithThisId as ex:
        return make_error_response(ApiError.NO_EXPENSE_WITH_THIS_ID, status_code=404)


@expenses_api.route('/sync', methods=['POST'])
@needs_firebase_uid
def sync(user_uid=None):
    partial_expenses = request.get_json(force=True, silent=True)
    try:
        assert isinstance(partial_expenses, dict), 'expected an object as payload.'
        assert all(
            [('timestamp_utc_updated' in partial_expense.keys()) for partial_expense in
             partial_expenses.values()]), "the values of the object must be objects with the `timestamp_utc_updated` key"
    except AssertionError as err:
        return make_error_response(str(err), status_code=400)

    try:
        return db_facade.sync(sync_request_objs=partial_expenses, user_uid=user_uid)
    except RuntimeError as err:
        return make_error_response("problem at the back end. mi scuzi.", status_code=500)
    except DynamodbThroughputExhausted as err:
        return make_error_response("The API cannot server your request currently.", status_code=413)
