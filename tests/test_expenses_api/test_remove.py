from app.expenses_api.views import ApiError
from tests.base_test import BaseTestWithHTTPMethods


class TestRemove(BaseTestWithHTTPMethods):
    endpoint = 'expenses_api.remove'

    def test_normal_usage(self):
        payload = {
            id: 1
        }
        raw_resp = self.delete(url=self.endpoint, data=payload)
        self.assertEqual(200, raw_resp.status_code)

        self.assertTrue(False, "The expense should have been removed from the db")

    def test_404_on_non_existing_expense(self):
        payload = {
            id: 10000
        }
        raw_resp = self.delete(url=self.endpoint, data=payload)
        self.assertEqual(404, raw_resp.status_code)

        self.assertIn(ApiError.NO_EXPENSE_WITH_THIS_ID, raw_resp.get_data(as_text=True))
