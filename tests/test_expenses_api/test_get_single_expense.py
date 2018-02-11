from json import loads

from app.expenses_api.views import ApiError
from tests.base_test import BaseTestWithHTTPMethods
from tests.common_methods import is_valid_expense


class TestGetSingleExpense(BaseTestWithHTTPMethods):
    endpoint = 'expenses_api.get_expense_by_id'

    def test_normal_usage(self):
        resp = self.get(url=self.endpoint, url_for_args={"expense_id": 1}, raw_response=False)
        json = loads(resp)
        self.assertTrue(is_valid_expense(json), "Response is not a valid expense")
        self.assertEqual(1, json['id'])

    def test_404_on_non_existing(self):
        resp = self.get(url=self.endpoint, url_for_args={"expense_id": 10000}, raw_response=True)
        self.assertEqual(404, resp.status_code)

        self.assertIn(ApiError.NO_EXPENSE_WITH_THIS_ID, resp.get_data(as_text=True))
