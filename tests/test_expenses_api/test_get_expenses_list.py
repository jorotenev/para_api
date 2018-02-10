from tests.base_test import BaseTestWithHTTPMethods
from flask import current_app
from json import dumps, loads


class TestGETExpensesList(BaseTestWithHTTPMethods):

    def test_valid_request_returns_valid_response(self):
        batch_size = 10
        raw_resp = self.get('expenses_api.get_expenses_list', url_args={"start_id": 10, 'batch_size': batch_size})
        json_resp = loads(raw_resp)

        self.assertEqual(batch_size, len(json_resp), "The result should be of size %i" % batch_size)

        ids = [exp['id'] for exp in json_resp]
        self.assertEqual(ids, list(sorted(ids, reverse=True)), "Result should be sorted descendigly")
        self.assertLess(ids[1], ids[0], 'The first result should be with the highest id')
