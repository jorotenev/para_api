from json import loads

from app.expenses_api.views import ApiError
from tests.base_test import BaseTestWithHTTPMethods
from tests.common_methods import SINGLE_EXPENSE


class TestUpdate(BaseTestWithHTTPMethods):
    endpoint = 'expenses_api.update'

    def test_normal_usage(self):
        # self.assertTrue(False, "Not implemented")
        raw_resp = self.put(url=self.endpoint, data=SINGLE_EXPENSE)
        self.assertEqual(200, raw_resp.status_code)
        exp_json = loads(raw_resp.get_data(as_text=True))
        self.assertDictEqual(SINGLE_EXPENSE, exp_json)

    def test_404_on_non_existing_expense(self):
        # self.assertTrue(False, "Not implemented")
        expense = SINGLE_EXPENSE.copy()
        expense['id'] = 10000
        raw_resp = self.put(url=self.endpoint, data=expense)
        self.assertEqual(404, raw_resp.status_code, "Should have returned a 404 for a non-managed expense")
        self.assertIn(ApiError.NO_EXPENSE_WITH_THIS_ID, raw_resp.get_data(as_text=True))
