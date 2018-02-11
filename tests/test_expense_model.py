from datetime import datetime

from app.models.expense import ExpenseValidator, ValidatorErrorPrefix
from tests.base_test import BaseTest

valid_expense = {
    'id': 1,
    'name': 'a',
    'amount': 1,
    'tags': ['work'],
    'currency': "EUR",
    'timestamp_utc': '2018-02-10T18:55:40.561052+00:00',
    'timestamp_utc_created': '2018-02-10T18:55:40.561052+00:00',
    'timestamp_utc_updated': '2018-02-10T18:55:40.561052+00:00',
}


class TestExpenseModel(BaseTest):
    def test_validation(self):
        is_valid, errs = ExpenseValidator.validate(valid_expense)
        errs = list(map(str, errs))
        self.assertTrue(is_valid, "A valid expense is reported as invalid with reason: \n[%s] " % "\n".join(errs))

    def test_invalid_expense(self):
        no_id = valid_expense.copy()
        no_id.pop('id')
        is_valid, errs = ExpenseValidator.validate(no_id)
        self.assertFalse(is_valid, "Should be reported as invalid")
        self.assertIn(ValidatorErrorPrefix.MISSING_PROPERTY, errs)

        amount_is_null = valid_expense.copy()
        amount_is_null['amount'] = None
        is_valid, errs = ExpenseValidator.validate(amount_is_null)
        self.assertFalse(is_valid, "Should be reported as invalid")
        self.assertIn(ValidatorErrorPrefix.WRONG_TYPE, errs)

    def test_timestamp_validation(self):
        invalid_ts = valid_expense.copy()
        invalid_ts['timestamp_utc'] = str(datetime.now())

        is_valid, errs = ExpenseValidator.validate(invalid_ts)
        self.assertFalse(is_valid, 'Should be reported as invalid because it is a naive ts and not a UTC ts.')
        self.assertIn('timestamp_utc', errs)
        self.assertIn('not a valid timestamp', errs)
