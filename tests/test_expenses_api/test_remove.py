from unittest.mock import patch

from app.db_facade.facade import NoExpenseWithThisId
from app.expenses_api.views import db_facade
from app.expenses_api.views import ApiError
from tests.base_test import BaseTestWithHTTPMethods
from tests.test_expenses_api import db_facade_path

endpoint = 'expenses_api.remove'


@patch(db_facade_path, autospec=True)
class TestRemove(BaseTestWithHTTPMethods):

    def test_normal_usage(self, mocked_db):
        mocked_db.remove.return_value = True

        raw_resp = self.delete(url=endpoint, url_for_args={'expense_id': 1})
        self.assertEqual(200, raw_resp.status_code)
        self.assertTrue(mocked_db.remove.called)
        args, _ = mocked_db.remove.call_args
        self.assertEqual(args, [1, self.firebase_uid])

    def test_404_on_non_existing_expense(self, mocked_db):
        mocked_db.remove.side_effect = NoExpenseWithThisId()

        raw_resp = self.delete(url=endpoint, url_for_args={"expense_id": 10000})
        self.assertEqual(404, raw_resp.status_code)

        self.assertIn(ApiError.NO_EXPENSE_WITH_THIS_ID, raw_resp.get_data(as_text=True))


@patch(db_facade_path, autospec=True)
class TestRemoveAndDbFacade(BaseTestWithHTTPMethods):
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
