from tests.base_test import BaseTestWithHTTPMethodsMixin, BaseTest, NoAuthenticationMarkerMixin

from json import loads
from unittest.mock import patch

from app.db_facade.facade import NoExpenseWithThisId
from app.expenses_api.api_error_msgs import ApiError
from app.models.expense_validation import Validator
from tests.common_methods import SINGLE_EXPENSE
from tests.test_expenses_api import db_facade_path

endpoint = 'expenses_api.update'
valid_payload = {'updated': SINGLE_EXPENSE.copy(), 'previous_state': SINGLE_EXPENSE.copy()}


class TestUpdateAuth(BaseTest, BaseTestWithHTTPMethodsMixin):
    def test_update(self):
        resp = self.put(url=endpoint, data=valid_payload)
        self.assertEqual(403, resp.status_code)


@patch(db_facade_path, autospec=True)
class TestUpdate(BaseTestWithHTTPMethodsMixin, BaseTest, NoAuthenticationMarkerMixin):

    def test_normal_usage(self, mocked_facade):
        mocked_facade.update.return_value = SINGLE_EXPENSE
        updated = valid_payload['updated'].copy()

        raw_resp = self.put(url=endpoint, data=valid_payload)

        self.assertEqual(200, raw_resp.status_code)
        exp_json = loads(raw_resp.get_data(as_text=True))
        self.assertTrue(Validator.validate_expense_simple(exp_json))

        # the facade would have updated these (tested in the db facade tests)
        del exp_json['timestamp_utc_updated']
        del updated['timestamp_utc_updated']
        self.assertDictEqual(updated, exp_json)

    def test_400_if_previous_state_not_send(self, mocked_facade):
        data = {'updated': SINGLE_EXPENSE.copy()}

        raw_resp = self.put(url=endpoint, data=data)
        self.assertEqual(400, raw_resp.status_code)
        self.assertIn(ApiError.PREVIOUS_STATE_OF_EXP_MISSING, raw_resp.get_data(as_text=True))

    def test_404_on_non_existing_expense(self, mocked_facade):
        mocked_facade.update.side_effect = NoExpenseWithThisId()

        raw_resp = self.put(url=endpoint, data=valid_payload)
        self.assertEqual(404, raw_resp.status_code, "Should have returned a 404 for a non-managed expense")
        self.assertIn(ApiError.NO_EXPENSE_WITH_THIS_ID, raw_resp.get_data(as_text=True))

    def test_400_if_ids_dont_match(self, _):
        data = {
            'updated': {**SINGLE_EXPENSE},
            'previous_state': {**SINGLE_EXPENSE, 'id': 'musaka'}
        }

        raw_resp = self.put(url=endpoint, data=data)
        self.assertEqual(400, raw_resp.status_code)
        self.assertIn(ApiError.IDS_OF_EXPENSES_DONT_MATCH, raw_resp.get_data(as_text=True))
