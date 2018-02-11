from app.models.expense_validation import ExpenseValidator
from app.models.sample_expenses import sample_expenses

SINGLE_EXPENSE = sample_expenses[0]


def currentDay():
    from datetime import datetime as DT
    return DT.now().day


def is_valid_expense(exp):
    is_valid, _ = ExpenseValidator.validate(exp)
    return is_valid


def is_number(val):
    try:
        return type(float(str(val))) == float
    except:
        return False
