import json
from flask import request
from app.api_utils.response import make_json_response
from app.db_facade import db_facade
from app.db_facade.facade import MAX_BATCH_SIZE, OrderingDirection
from app.helpers.time import ensure_ts_str_ends_with_z
from app.models.expense_validation import Validator
from . import expenses_api
from datetime import datetime as dt, timezone as tz
from app.models.json_schema import expense_schema


class ApiError:
    BATCH_SIZE_EXCEEDED = "Serving this request would exceed the maximum size of the response, %i. "
    INVALID_QUERY_PARAMS = "Invalid URL query parameters"
    NO_EXPENSE_WITH_THIS_ID = "Can't find an expense with this id in this account"
    ID_PROPERTY_FORBIDDEN = "The id property MUST be null"
    INVALID_EXPENSE = "The expense doesn't match the expected format"
    INVALID_ORDER_PARAM = "Invalid value for ordering direction. Allowed: [%s]" % ", ".join(
        [o.name for o in OrderingDirection])


@expenses_api.route("/test", methods=['GET'])
def test():
    return 'asd' + str(db_facade.asd())


def validate_get_expenses_list_property_value(property_name, property_value):
    assert property_name in expense_schema['properties'].keys(), "%s is not a valid expense property" % property_name

    assert Validator.validate_property(property_value, property_name), '%s is not a valid value for %s' % \
                                                                         (str(property_value), property_name)


@expenses_api.route("/get_expenses_list", methods=['GET'])
def get_expenses_list():
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

    except AssertionError as ex:
        status_code = 400
        if ApiError.BATCH_SIZE_EXCEEDED in str(ex):
            status_code = 413

        return make_json_response(json.dumps({
            'error': "%s. %s" % (ApiError.INVALID_QUERY_PARAMS, str(ex))
        }), status_code=status_code)

    ordering_direction = OrderingDirection[ordering_direction]  # make it an enum

    response = []

    # response.sort(key=lambda expense: expense[property_value],
    #               reverse=True if ordering_direction is OrderingDirection.desc else False)
    #
    return make_json_response(response)


@expenses_api.route("/get_expense_by_id/<int:expense_id>", methods=['GET'])
def get_expense_by_id(expense_id):
    return ""


@expenses_api.route('/persist', methods=['POST'])
def persist():
    return '{}'


@expenses_api.route('/update', methods=['PUT'])
def update():
    return '{}'


@expenses_api.route('/remove/<int:expense_id>', methods=['DELETE'])
def remove(expense_id):
    return '{}'


@expenses_api.route('/sync', methods=['GET'])
def sync():
    return '{}'
