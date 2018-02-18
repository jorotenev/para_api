from datetime import datetime, timezone as tz

from app.models.expense_validation import Validator, ValidatorErrorPrefix
from tests.base_test import BaseTest
from app.models.sample_expenses import sample_expenses

valid_expense = sample_expenses[0]


class TestExpenseModel(BaseTest):
    def test_validation(self):
        is_valid, errs = Validator.validate_expense(valid_expense)
        errs = list(map(str, errs))
        self.assertTrue(is_valid, "A valid expense is reported as invalid with reason: \n[%s] " % "\n".join(errs))

    def test_invalid_expense(self):
        no_id = valid_expense.copy()
        no_id.pop('id')
        is_valid, errs = Validator.validate_expense(no_id)
        self.assertFalse(is_valid, "Should be reported as invalid")
        self.assertIn(ValidatorErrorPrefix.MISSING_PROPERTY, errs)

        amount_is_null = valid_expense.copy()
        amount_is_null['amount'] = None
        is_valid, errs = Validator.validate_expense(amount_is_null)
        self.assertFalse(is_valid, "Should be reported as invalid")
        self.assertIn(ValidatorErrorPrefix.WRONG_TYPE, errs)

    def test_timestamp_validation(self):
        invalid_ts = valid_expense.copy()
        invalid_ts['timestamp_utc'] = str(datetime.now())

        is_valid, errs = Validator.validate_expense(invalid_ts)
        self.assertFalse(is_valid, 'Should be reported as invalid because it is a naive ts and not a UTC ts.')
        self.assertIn('timestamp_utc', errs)
        self.assertIn('not a valid timestamp', errs)

    def test_timestamp_must_end_with_z(self):
        invalid_ts = valid_expense.copy()
        invalid_ts['timestamp_utc'] = datetime.now(tz.utc).isoformat()  # ends with +00:00
        is_valid, errs = Validator.validate_expense(invalid_ts)
        self.assertFalse(is_valid)
        self.assertIn('timestamp_utc', errs)
        self.assertIn('not a valid timestamp', errs)
