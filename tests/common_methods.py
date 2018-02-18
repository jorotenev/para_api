from app.models.expense_validation import Validator
from app.models.sample_expenses import sample_expenses

SINGLE_EXPENSE = sample_expenses[0]
TESTER_USER_FIREBASE_UID = 'my fake uid'

def currentDay():
    from datetime import datetime as DT
    return DT.now().day


def is_valid_expense(exp):
    is_valid, _ = Validator.validate_expense(exp)
    return is_valid


def is_number(val):
    try:
        return type(float(str(val))) == float
    except:
        return False
