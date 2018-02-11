from jsonschema import validate, ValidationError

expense_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "ExpenseObject",
    "description": "timetmap regex from https://www.myintervals.com/blog/2009/05/20/iso-8601-date-validation-that-doesnt-suck/ and modified to require tz",
    "type": "object",
    "properties": {
        "id": {"type": ["number", "null"]},
        "name": {"type": "string"},
        "amount": {"type": "number"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "currency": {"type": "string", "pattern": "^[A-Z]{3}$"},
        "timestamp_utc": {
            "type": "string",
            "pattern": "^([\\+-]?\\d{4}(?!\\d{2}\\b))((-?)((0[1-9]|1[0-2])(\\3([12]\\d|0[1-9]|3[01]))?|W([0-4]\\d|5[0-2])(-?[1-7])?|(00[1-9]|0[1-9]\\d|[12]\\d{2}|3([0-5]\\d|6[1-6])))([T\\s]((([01]\\d|2[0-3])((:?)[0-5]\\d)?|24\\:?00)([\\.,]\\d+(?!:))?)?(\\17[0-5]\\d([\\.,]\\d+)?)?([zZ]|([\\+-])([01]\\d|2[0-3]):?([0-5]\\d)?))?)?$"
        },
        "timestamp_utc_created": {
            "type": "string",
            "pattern": "^([\\+-]?\\d{4}(?!\\d{2}\\b))((-?)((0[1-9]|1[0-2])(\\3([12]\\d|0[1-9]|3[01]))?|W([0-4]\\d|5[0-2])(-?[1-7])?|(00[1-9]|0[1-9]\\d|[12]\\d{2}|3([0-5]\\d|6[1-6])))([T\\s]((([01]\\d|2[0-3])((:?)[0-5]\\d)?|24\\:?00)([\\.,]\\d+(?!:))?)?(\\17[0-5]\\d([\\.,]\\d+)?)?([zZ]|([\\+-])([01]\\d|2[0-3]):?([0-5]\\d)?))?)?$"
        },
        "timestamp_utc_updated": {
            "type": "string",
            "pattern": "^([\\+-]?\\d{4}(?!\\d{2}\\b))((-?)((0[1-9]|1[0-2])(\\3([12]\\d|0[1-9]|3[01]))?|W([0-4]\\d|5[0-2])(-?[1-7])?|(00[1-9]|0[1-9]\\d|[12]\\d{2}|3([0-5]\\d|6[1-6])))([T\\s]((([01]\\d|2[0-3])((:?)[0-5]\\d)?|24\\:?00)([\\.,]\\d+(?!:))?)?(\\17[0-5]\\d([\\.,]\\d+)?)?([zZ]|([\\+-])([01]\\d|2[0-3]):?([0-5]\\d)?))?)?$"
        }
    },
    "required": ["id", "name", "amount", "tags", "currency", "timestamp_utc", "timestamp_utc_created",
                 "timestamp_utc_updated"]

}

if __name__ == "__main__":
    valid = {
        "id": 1,
        "name": "server id 1",
        "amount": 12,
        "currency": "EUR",
        "tags": [
            "work",
            "sport"
        ],
        "timestamp_utc": "2017-10-29T09:09:21.853071Z",
        "timestamp_utc_created": "2017-10-29T09:09:21.853071+00:00",
        "timestamp_utc_updated": "2017-10-29T09:09:21.853071Z",
    }

    invalid = {
        "id": 1,
        "name": "server id 1",
        "amount": 12,
        "currency": "EUR",
        "tags": [
            "work",
            "sport"
        ],
        "timestamp_utc": "2017-10-29T09:09:21.853071",
        "timestamp_utc_created": "2017-10-29T09:09:21.853071Z",
        "timestamp_utc_updated": "2017-10-29T09:09:21.853071Z",
    }
    try:
        validate(valid, schema=expense_schema)
        validate(invalid, schema=expense_schema)
    except ValidationError as err:
        pass
