from unittest.mock import patch

from app.db_facade.facade import NoExpenseWithThisId
from app.expenses_api.views import db_facade
from app.expenses_api.views import ApiError
from app.models.sample_expenses import sample_expenses
from tests.base_test import BaseTest, BaseTestWithHTTPMethodsMixin
from tests.common_methods import SINGLE_EXPENSE
from tests.test_expenses_api import db_facade_path

endpoint = 'expenses_api.remove'


@patch(db_facade_path, autospec=True)
class TestRemove(BaseTest, BaseTestWithHTTPMethodsMixin):

    def test_normal_usage(self, mocked_db):
        mocked_db.remove.return_value = None
        raw_resp = self.delete(url=endpoint, data=SINGLE_EXPENSE.copy())

        self.assertTrue(mocked_db.remove.called)
        self.assertEqual(200, raw_resp.status_code)

    def test_404_on_non_existing_expense(self, mocked_db):
        mocked_db.remove.side_effect = NoExpenseWithThisId()
        to_delete = sample_expenses[0].copy()
        raw_resp = self.delete(url=endpoint, data=to_delete)
        self.assertEqual(404, raw_resp.status_code)

        self.assertIn(ApiError.NO_EXPENSE_WITH_THIS_ID, raw_resp.get_data(as_text=True))

    def test_400_on_invalid_expense(self, mocked_db):
        mocked_db.remove.side_effect = RuntimeError("Shouldn't be called")

        invalid_expenses = []
        invalid_expenses.append({**sample_expenses[0], 'timestamp_utc': ''})
        invalid_expenses.append({**sample_expenses[0], 'id': ''})

        for invalid_expense in invalid_expenses:
            raw_resp = self.delete(url=endpoint, data=invalid_expense)
            self.assertEqual(400, raw_resp.status_code)
            self.assertFalse(mocked_db.remove.called)
            mocked_db.remove.reset_mock()


@patch(db_facade_path, autospec=True)
class TestRemoveAndDbFacade(BaseTest, BaseTestWithHTTPMethodsMixin):
    def test_normal_usage(self, mocked_db: type(db_facade)):
        mocked_db.remove.return_value = True
        exp = SINGLE_EXPENSE.copy()
        self.delete(url=endpoint, data=exp)
        self.assertTrue(mocked_db.remove.called)
        call_args, call_kwargs = mocked_db.remove.call_args
        self.assertDictEqual({
            'expense': exp,
            'user_uid': self.firebase_uid
        }, call_kwargs)
