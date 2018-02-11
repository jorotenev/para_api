from app.models.expense import ExpenseValidator


def currentDay():
    from datetime import datetime as DT
    return DT.now().day


def is_valid_expense(exp):
    is_valid, _ = ExpenseValidator.validate(exp)
    return is_valid
