import json
from flask import request, current_app
from app.api_utils.response import make_json_response, make_error_response
from app.db_facade import db_facade
from app.db_facade.facade import MAX_BATCH_SIZE, NoExpenseWithThisId
from app.db_facade.misc import OrderingDirection
from app.models.expense_validation import Validator
from tests.common_methods import TESTER_USER_FIREBASE_UID
from . import expenses_api
from app.models.json_schema import expense_schema
from functools import wraps


def needs_firebase_uid(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        firebase_token = TESTER_USER_FIREBASE_UID  # TODO
        try:
            request.headers[current_app.config['CUSTOM_AUTH_HEADER_NAME']]
        except:
            return make_error_response("can't find auth token", status_code=403)
        return f(*args, **kwargs, user_uid=firebase_token)

    return decorated


class ApiError:
    IDS_OF_EXPENSES_DONT_MATCH = "When updating, the `id` properties of both the updated expense and its previous state must be the same"
    INVALID_BATCH_SIZE = "Received an invalid batch_size. Must be >0 integer."
    BATCH_SIZE_EXCEEDED = "Serving this request would exceed the maximum size of the response, %i. "
    INVALID_QUERY_PARAMS = "Invalid URL query parameters"
    NO_EXPENSE_WITH_THIS_ID = "Can't find an expense with this id in this account"
    ID_PROPERTY_FORBIDDEN = "The id property MUST be null"
    INVALID_EXPENSE = "The expense doesn't match the expected format"
    INVALID_ORDER_PARAM = "Invalid value for ordering direction. Allowed: [%s]" % ", ".join(
        [o.name for o in OrderingDirection])
    PREVIOUS_STATE_OF_EXP_MISSING = "When updating an expense, both the update expense and its previous state are required"


@expenses_api.route("/test", methods=['GET'])
def test():
    return 'asd' + str(db_facade.asd())


@expenses_api.route("/honeypot", methods=['GET', 'POST', 'PUT', 'DELETE'])
@needs_firebase_uid
def honeypot(user_uid=None):
    """
    endpoint used to verify that protected routes require auth
    :return:
    """
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


@expenses_api.route("/get_expense_by_id/<int:expense_id>", methods=['GET'])
def get_expense_by_id(expense_id):
    return ""


@expenses_api.route('/persist', methods=['POST'])
def persist():
    return '{}'


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
        assert request_data, "Empty request body"
        assert 'updated' in request_data, '`updated` field not in the request body'
        assert 'previous_state' in request_data, ApiError.PREVIOUS_STATE_OF_EXP_MISSING

        check_valid = [('updated', request_data['updated']), ('previous_state', request_data['previous_state'])]
        for field, value in check_valid:
            is_valid, _ = Validator.validate_expense(value)
            assert is_valid, "%s is not a valid expense" % field
            assert 'id' in value, 'The `id` field is mandatory'
    except AssertionError as err:
        return False, str(err)

    return True, None


@expenses_api.route('/remove', methods=['DELETE'])
def remove():
    return '{}'


@expenses_api.route('/sync', methods=['GET'])
def sync():
    return '{}'
