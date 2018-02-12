from json import loads
from unittest.mock import patch

from app.db_facade.facade import NoExpenseWithThisId
from app.expenses_api.views import ApiError, db_facade
from app.helpers.time import utc_now
from tests.base_test import BaseTestWithHTTPMethods
from tests.common_methods import SINGLE_EXPENSE, is_valid_expense
from tests.test_expenses_api import db_facade_path

endpoint = 'expenses_api.update'


@patch(db_facade_path, autospec=True)
class TestUpdate(BaseTestWithHTTPMethods):

    def test_normal_usage(self, mocked_db):
        mocked_db.update.return_value = SINGLE_EXPENSE

        raw_resp = self.put(url=endpoint, data=SINGLE_EXPENSE)
        self.assertEqual(200, raw_resp.status_code)
        exp_json = loads(raw_resp.get_data(as_text=True))
        self.assertTrue(is_valid_expense(exp_json))
        self.assertDictEqual(SINGLE_EXPENSE, exp_json)

    def test_404_on_non_existing_expense(self, mocked_db):
        mocked_db.update.side_effect = NoExpenseWithThisId()

        raw_resp = self.put(url=endpoint, data=SINGLE_EXPENSE)
        self.assertEqual(404, raw_resp.status_code, "Should have returned a 404 for a non-managed expense")
        self.assertIn(ApiError.NO_EXPENSE_WITH_THIS_ID, raw_resp.get_data(as_text=True))


@patch(db_facade_path, autospec=True)
class TestUpdateAndDbFacade(BaseTestWithHTTPMethods):
    def test_normal_usage(self, mocked_db: type(db_facade)):
        updated = SINGLE_EXPENSE.copy()
        updated['timestamp_utc_updated'] = utc_now()
        mocked_db.update.return_value = updated

        self.assertTrue(mocked_db.update.called)
        args, _ = mocked_db.update.call_args
        self.assertEqual(args, [updated, self.firebase_uid])
