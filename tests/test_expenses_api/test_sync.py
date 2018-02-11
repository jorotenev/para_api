from json import loads, dumps

from tests.base_test import BaseTestWithHTTPMethods
from app.models.sample_expenses import sample_expenses
from tests.common_methods import is_valid_expense, is_number


class TestSync(BaseTestWithHTTPMethods):
    endpoint = 'expenses_api.sync'

    def test_normal_usage(self):
        payload = dumps(sample_expenses)
        raw_resp = self.get(url=self.endpoint, data=payload)
        json = loads(raw_resp.get_data(as_text=True))
        self.assertTrue(type(json) == list)
        self.assertTrue(all([is_valid_expense(exp) for exp in json['to_add']]))
        self.assertTrue(all([is_valid_expense(exp) for exp in json['to_update']]))
        self.assertTrue(all(map(is_number, json['to_remove'])))
