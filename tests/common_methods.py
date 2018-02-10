from app.expense import ExpenseModel


def currentDay():
    from datetime import datetime as DT
    return DT.now().day


def is_valid_expense(exp):
    is_valid, _ = ExpenseModel.validate(exp)
    return is_valid
