from json import loads, dumps
from unittest.mock import patch
from tests.base_test import BaseTestWithHTTPMethodsMixin, BaseTest
from app.models.sample_expenses import sample_expenses
from tests.common_methods import is_valid_expense, is_number, SINGLE_EXPENSE
from tests.test_expenses_api import db_facade_path

endpoint = 'expenses_api.sync'


@patch(db_facade_path, autospec=True)
class TestSync(BaseTest, BaseTestWithHTTPMethodsMixin):

    def test_normal_usage(self, mocked_db):
        mocked_db.sync.return_value = dumps({
            'to_remove': ['some uuid'],
            'to_add': [SINGLE_EXPENSE],
            'to_update': [sample_expenses[1]]
        })

        payload = dumps(sample_expenses)
        raw_resp = self.get(url=endpoint, data=payload)
        json = loads(raw_resp.get_data(as_text=True))

        self.assertTrue(type(json) == list)
        self.assertTrue(all([is_valid_expense(exp) for exp in json['to_add']]))
        self.assertTrue(all([is_valid_expense(exp) for exp in json['to_update']]))
        self.assertTrue(all([type(e) == str for e in json['to_remove']]))

    def test_fails_on_invalid_payload(self, _):
        payload = '[{"something":1}]'
        raw_resp = self.get(url=endpoint, data=payload)
        self.assertEqual(raw_resp.status_code, 400)
