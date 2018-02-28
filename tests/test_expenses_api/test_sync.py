from tests.base_test import BaseTestWithHTTPMethodsMixin, BaseTest, NoAuthenticationMarkerMixin

from json import loads, dumps
from unittest.mock import patch

from app.db_facade.facade import DynamodbThroughputExhausted
from app.helpers.time import utc_now_str
from app.models.expense_validation import Validator
from app.models.sample_expenses import sample_expenses
from tests.common_methods import SINGLE_EXPENSE
from tests.test_db_facade.test_sync import generate_sync_request
from tests.test_expenses_api import db_facade_path

endpoint = 'expenses_api.sync'
valid_payload = generate_sync_request()


class TestSyncAuth(BaseTest, BaseTestWithHTTPMethodsMixin):
    def test_auth(self):
        resp = self.post(url=endpoint, data=valid_payload)
        self.assertEqual(403, resp.status_code)


@patch(db_facade_path, autospec=True)
class TestSync(BaseTest, BaseTestWithHTTPMethodsMixin, NoAuthenticationMarkerMixin):

    def test_normal_usage(self, mocked_db):
        mocked_db.sync.return_value = {
            'to_remove': ['some uuid'],
            'to_add': [SINGLE_EXPENSE],
            'to_update': [sample_expenses[1]]
        }

        raw_resp = self.post(url=endpoint, data=valid_payload)
        self.assertEqual(200, raw_resp.status_code)
        json = loads(raw_resp.get_data(as_text=True))

        self.assertTrue(type(json) == dict)
        self.assertTrue(all([Validator.validate_expense_simple(exp) for exp in json['to_add']]))
        self.assertTrue(all([Validator.validate_expense_simple(exp) for exp in json['to_update']]))
        self.assertTrue(all([type(e) == str for e in json['to_remove']]))

    def test_fails_on_invalid_payload(self, _):
        invalid_payloads = [
            [{"timestamp_utc_updated": 'invalid ts', 'id': 'valid id'}],
            [{"timestamp_utc_updated": utc_now_str(), 'id': None}],  # valid ts invalid id
            [{"timestamp_utc_updated": utc_now_str()}],  # valid ts but missing id
            [{'id': 'valid id but missing ts'}]
        ]
        for payload in invalid_payloads:
            raw_resp = self.post(url=endpoint, data=payload)
            self.assertEqual(raw_resp.status_code, 400)

    def test_correct_resp_code_on_facade_failing(self, mocked_db):
        requests = [
            (RuntimeError(), 500),
            (DynamodbThroughputExhausted(), 413)
        ]
        for (err, expected_code) in requests:
            mocked_db.sync.side_effect = err
            raw_resp = self.post(url=endpoint, data=valid_payload)
            self.assertEqual(expected_code, raw_resp.status_code)
