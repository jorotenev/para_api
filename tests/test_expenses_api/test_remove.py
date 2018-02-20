from unittest.mock import patch

from app.db_facade.facade import NoExpenseWithThisId
from app.expenses_api.views import db_facade
from app.expenses_api.views import ApiError
from app.models.sample_expenses import sample_expenses
from tests.base_test import BaseTest, BaseTestWithHTTPMethodsMixin
from tests.test_expenses_api import db_facade_path

endpoint = 'expenses_api.remove'


@patch(db_facade_path, autospec=True)
class TestRemove(BaseTest, BaseTestWithHTTPMethodsMixin):

    def test_normal_usage(self, mocked_db):
        mocked_db.remove.return_value = None

        raw_resp = self.delete(url=endpoint, url_for_args={'expense_id': 1})
        self.assertEqual(200, raw_resp.status_code)
        self.assertTrue(mocked_db.remove.called)
        args, _ = mocked_db.remove.call_args
        self.assertEqual(args, [1, self.firebase_uid])

    def test_404_on_non_existing_expense(self, mocked_db):
        mocked_db.remove.side_effect = NoExpenseWithThisId()
        to_delete = sample_expenses[0].copy()
        raw_resp = self.delete(url=endpoint, data=to_delete)
        self.assertEqual(404, raw_resp.status_code)

        self.assertIn(ApiError.NO_EXPENSE_WITH_THIS_ID, raw_resp.get_data(as_text=True))

    def test_400_on_invalid_expense(self, mocked_db):
        mocked_db.remove.side_effect = RuntimeError("Shouldn't be called")
        invalid_expenses = []

        invalid_expenses.push({**sample_expenses[0], 'timestamp_utc': ''})
        invalid_expenses.push({**sample_expenses[0], 'id': ''})
        for invalid_expense in invalid_expenses:
            raw_resp = self.delete(url=endpoint, data=invalid_expense)
            self.assertEqual(400, raw_resp.status_code)
            self.assertFalse(mocked_db.remove.called)
            mocked_db.remove.calls.reset_mock()


@patch(db_facade_path, autospec=True)
class TestRemoveAndDbFacade(BaseTest, BaseTestWithHTTPMethodsMixin):
    def test_normal_usage(self, mocked_db: type(db_facade)):
        mocked_db.remove.return_value = True
        exp_id = 1

        self.delete(url=endpoint, url_for_args={'expense_id': exp_id})
        self.assertTrue(mocked_db.remove.called)
        call_args, _ = mocked_db.remove.call_args
        self.assertEqual([exp_id, self.firebase_uid], call_args)

    def test_not_called_on_invalid(self, mocked_db: type(db_facade)):
        raw_resp = self.delete(url=endpoint, url_for_args={'expense_id': -1})
        self.assertFalse(mocked_db.remove.called)
