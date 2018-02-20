import os
from jsonschema import validate, ValidationError
from json import load
from flask import current_app

dir_path = os.path.dirname(os.path.realpath(__file__))

with open(dir_path + "/../para-common/expense_json_schema.json") as file:  # todo better way to reference the file
    expense_schema = load(file)
    expense_properties = list(expense_schema['properties'].keys())
if __name__ == "__main__":
    valid = {
        "id": "1",
        "name": "server id 1",
        "amount": 12,
        "currency": "EUR",
        "tags": [
            "work",
            "sport"
        ],
        "timestamp_utc": "2017-10-29T09:09:21.853071Z",
        "timestamp_utc_created": "2017-10-29T09:09:21.853071Z",
        "timestamp_utc_updated": "2017-10-29T09:09:21.853071Z",
    }
    validate(valid, schema=expense_schema)
    # validate("2017-10-29T09:10:21.853071Z", timestamp_schema)
