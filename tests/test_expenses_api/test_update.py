from json import loads
from unittest.mock import patch

from app.db_facade.facade import NoExpenseWithThisId
from app.expenses_api.views import ApiError, db_facade
from app.helpers.time import utc_now_str
from tests.base_test import BaseTestWithHTTPMethodsMixin, BaseTest
from tests.common_methods import SINGLE_EXPENSE, is_valid_expense
from tests.test_expenses_api import db_facade_path

endpoint = 'expenses_api.update'


@patch(db_facade_path, autospec=True)
class TestUpdate(BaseTestWithHTTPMethodsMixin, BaseTest):

    def test_normal_usage(self, mocked_db):
        mocked_db.update.return_value = SINGLE_EXPENSE
        updated = SINGLE_EXPENSE.copy()
        raw_resp = self.put(url=endpoint, data={
            'updated': updated,
            'previous_state': updated
        })

        self.assertEqual(200, raw_resp.status_code)
        exp_json = loads(raw_resp.get_data(as_text=True))
        self.assertTrue(is_valid_expense(exp_json))

        # the facade would have updated these (tested in the db facade tests)
        del exp_json['timestamp_utc_updated']
        del updated['timestamp_utc_updated']
        self.assertDictEqual(updated, exp_json)

    def test_400_if_previous_state_not_send(self):
        raw_resp = self.put(url=endpoint, data={
            'updated': SINGLE_EXPENSE
        })
        self.assertEqual(400, raw_resp.status_code)
        self.assertIn(ApiError.PREVIOUS_STATE_OF_EXP_MISSING, raw_resp.get_data(as_text=True)['error'])

    def test_404_on_non_existing_expense(self, mocked_db):
        mocked_db.update.side_effect = NoExpenseWithThisId()

        raw_resp = self.put(url=endpoint, data=SINGLE_EXPENSE)
        self.assertEqual(404, raw_resp.status_code, "Should have returned a 404 for a non-managed expense")
        self.assertIn(ApiError.NO_EXPENSE_WITH_THIS_ID, raw_resp.get_data(as_text=True))
