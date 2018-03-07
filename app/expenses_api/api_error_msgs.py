from app.db_facade.misc import OrderingDirection


class ApiError:
    MAXIMUM_TIME_WINDOW_EXCEEDED = "Maximum time window exceeded"
    EMPTY_REQUEST_BODY = "Empty request body"
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
    ID_PROPERTY_MANDATORY = 'The `id` property must be non-null'
