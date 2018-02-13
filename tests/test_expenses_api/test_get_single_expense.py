from json import loads
from unittest.mock import patch

from app.db_facade.facade import NoExpenseWithThisId
from app.expenses_api.views import ApiError, db_facade as DbFacade
from tests.base_test import BaseTest, BaseTestWithHTTPMethodsMixin
from tests.common_methods import is_valid_expense, SINGLE_EXPENSE

endpoint = 'expenses_api.get_expense_by_id'

from . import db_facade_path


@patch(db_facade_path, autospec=True)
class TestGetSingleExpense(BaseTest, BaseTestWithHTTPMethodsMixin):

    def test_normal_usage(self, mocked_db):
        mocked_db.get_list.return_value = [SINGLE_EXPENSE]

        resp = self.get(url=endpoint, url_for_args={"expense_id": 1}, raw_response=False)
        json = loads(resp)

        self.assertTrue(is_valid_expense(json), "Response is not a valid expense")
        self.assertEqual(SINGLE_EXPENSE['id'], json['id'])

    def test_404_on_non_existing(self, mocked_db):
        mocked_db.get_single.side_effect = NoExpenseWithThisId()

        resp = self.get(url=endpoint, url_for_args={"expense_id": 10000}, raw_response=True)
        self.assertEqual(404, resp.status_code)

        self.assertIn(ApiError.NO_EXPENSE_WITH_THIS_ID, resp.get_data(as_text=True))


@patch(db_facade_path, autospec=True)
class TestGetSingleExpense(BaseTest, BaseTestWithHTTPMethodsMixin):
    def test_normal_usage(self, mocked_db: type(DbFacade)):
        mocked_db.get_list.return_value = SINGLE_EXPENSE
        exp_id = SINGLE_EXPENSE['id']
        _ = self.get(url=endpoint, url_for_args={"expense_id": exp_id})

        self.assertTrue(mocked_db.get_list.called, "get_list should have been called")
        call_args, _ = mocked_db.get_list.call_args
        self.assertEqual(call_args, [exp_id, 1, self.firebase_uid],
                         "get_list wasn't called with the expected arguments")
