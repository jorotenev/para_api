from jsonschema import validate, ValidationError
from app.models.json_schema import expense_schema


class ValidatorErrorPrefix:
    MISSING_PROPERTY = "missing required property: "
    WRONG_TYPE = "property has the wrong type: "
    PATTERN_DOESNT_MATCH = 'the value %s for %s doesn\'t match the expected regex'
    INVALID_TIMESTAMP = "the value %s for property %s is not a valid timestamp. It MUST be in UTC and NOT naive."


class ExpenseValidator:

    @staticmethod
    def validate(exp):
        """
        :param exp: a dictionary.
        :return: a tuple. if exp was valid, (True, ""), if invalid, (False, "<msg>") where msg is formatted via ValidateErrorPrefix
        """

        is_valid = True
        err_msg = ""
        try:
            validate(exp, schema=expense_schema)
        except ValidationError as err:
            is_valid = False
            msg = err.message
            prefix = ""

            if err.validator == 'required':
                prefix = ValidatorErrorPrefix.MISSING_PROPERTY
            elif err.validator == 'type':
                prefix = ValidatorErrorPrefix.WRONG_TYPE
            elif err.validator == 'pattern':
                path = err.path.pop()
                if 'timestamp' in path:
                    prefix = ValidatorErrorPrefix.INVALID_TIMESTAMP % (err.instance, path)
                else:
                    prefix = ValidatorErrorPrefix.PATTERN_DOESNT_MATCH % (err.instance, path)

            err_msg = prefix + msg
        return is_valid, err_msg
