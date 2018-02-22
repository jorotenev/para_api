import os
from jsonschema import validate, ValidationError
from json import load

dir_path = os.path.dirname(os.path.realpath(__file__))

with open(dir_path + "/../para-common/expense_json_schema.json") as file:  # todo better way to reference the file
    expense_schema = load(file)
    expense_properties = list(expense_schema['properties'].keys())
