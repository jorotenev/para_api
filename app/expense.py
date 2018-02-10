import os, sys
from dateutil import parser
from app.helpers.currencies import currencies


def is_valid_utc_timestamp(cand):
    try:
        parsed = parser.parse(cand)
        return parsed.tzname() == "UTC"
    except ValueError:
        return False


def is_number(v):
    try:
        return type(float(str(v))) == float
    except:
        return False


class ExpenseModel:

    @staticmethod
    def validate(exp):
        """

        :param exp: a dictionary.
        :return: a tuple. if exp was valid, (True, []), if invalid, (False, [(<property_name>, <fail reason>)+]
        """
        validators = {
            'id': {
                'checker': lambda val: type(val) == int,
                'required': True,
                'nullable': True,
            },
            'tags': {
                'checker': lambda val: type(val) == list and all([type(tag) == str for tag in val]),
                'required': True,
                'nullable': False
            },
            'amount': {'checker': is_number, 'required': True, 'nullable': False},
            'name': {'checker': lambda val: type(val) == str, 'required': True, 'nullable': False},
            'currency': {'checker': lambda val: val in currencies.keys(), 'required': True, 'nullable': False},
            'timestamp_utc': {'checker': is_valid_utc_timestamp, 'required': True, 'nullable': False},
            'timestamp_utc_created': {'checker': is_valid_utc_timestamp, 'required': True, 'nullable': False},
            # TODO  - updated can't be before created
            'timestamp_utc_updated': {'checker': is_valid_utc_timestamp, 'required': False, 'nullable': False},
        }

        errors = []
        for property_name, validator in validators.items():
            if validator['required'] and property_name not in exp:
                errors.append((property_name, 'missing required property %s' % property_name))
                continue

            if not validator['nullable'] and exp[property_name] == None:
                errors.append((property_name, 'non-nullable property %s has value None' % property_name))
                continue
            try:
                if not validator['checker'](exp[property_name]):
                    errors.append((property_name, "validation failed"))
                    continue
            except Exception as err:
                errors.append((property_name, 'EXCEPTION in validation: %s ' % str(err)))
                continue

        return len(errors) == 0, errors
