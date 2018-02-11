from json import loads

from app.expenses_api.views import ApiError
from tests.base_test import BaseTestWithHTTPMethods
from tests.common_methods import SINGLE_EXPENSE


class TestPersist(BaseTestWithHTTPMethods):
    endpoint = 'expenses_api.persist'

    def test_normal_usage(self):
        expense = SINGLE_EXPENSE.copy()
        expense['id'] = None
        raw_resp = self.post(url=self.endpoint, data=SINGLE_EXPENSE)
        self.assertEqual(200, raw_resp.status_code)

        json = loads(raw_resp.get_data(as_text=True))
        id = json['id']
        expense['id'] = id  # put it lipstick...
        self.assertDictEqual(expense, json, "The returned expense must be the same ")

    def test_fails_if_expense_with_id(self):
        raw_resp = self.post(url=self.endpoint, data=SINGLE_EXPENSE)

        self.assertEqual(400, raw_resp.status_code)
        self.assertIn(ApiError.ID_PROPERTY_FORBIDDEN, raw_resp.get_data(as_text=True))

    def test_fail_on_invalid_expense(self):
        raw_resp = self.post(url=self.endpoint, data={id: None})

        self.assertEqual(400, raw_resp.status_code)
        self.assertIn(ApiError.INVALID_EXPENSE, raw_resp.get_data(as_text=True))

    def test_persist_results_in_new_db_entry(self):
        self.assertTrue(False, "Not implemented")
