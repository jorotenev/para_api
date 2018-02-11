import json

from app.expenses_api.views import MAXIMUM_BATCH_SIZE, ApiError
from tests.base_test import BaseTestWithHTTPMethods
from json import loads

from tests.common_methods import is_valid_expense


class TestGETExpensesList(BaseTestWithHTTPMethods):
    endpoint = 'expenses_api.get_expenses_list'

    def test_valid_request_returns_valid_response(self):
        batch_size = 10
        start_id = 10
        raw_resp = self.get(self.endpoint, url_args={"start_id": start_id, 'batch_size': batch_size},
                            raw_response=False)
        json_resp = loads(raw_resp)

        self.assertEqual(batch_size, len(json_resp), "The result should be of size %i" % batch_size)

        ids = [exp['id'] for exp in json_resp]
        self.assertEqual(ids, list(sorted(ids, reverse=True)), "Result should be sorted by id descendigly")
        self.assertTrue(ids[0] > ids[1], 'The first result should be with the highest id')

        self.assertTrue(all([is_valid_expense(exp) for exp in json_resp]),
                        "All returned objects must be valid expenses")

        self.assertEqual(start_id, ids[0], "The first id is not start_id")

    def test_with_invalid_params(self):
        batch_size = -1
        start_from = 1
        invalid_args = [
            {
                'start_id': 10,
                'batch_size': -1
            },
            {
                'start_id': -1,
                'batch_size': 10
            },
            {
                'start_id': -1,
                'batch_size': -1
            }
        ]
        for args in invalid_args:
            raw_resp = self.get(url=self.endpoint, url_args={'start_id': start_from, 'batch_size': batch_size})

            self.assertEqual(raw_resp.status_code, 400, "args should have been rejected" + str(args))
            json_resp = json.loads(raw_resp.get_data(as_text=True))
            self.assertIn("error", json_resp,
                          "error key missing from non-200 response")
            self.assertIn(ApiError.INVALID_QUERY_PARAMS, json_resp['error'])

    def test_with_too_big_batch_size(self):
        batch_size = 100 + MAXIMUM_BATCH_SIZE
        start_id = batch_size

        raw_resp = self.get(url=self.endpoint, url_args={'start_id': start_id, "batch_size": batch_size})
        self.assertEqual(200, raw_resp.status_code, "batch size is too big - request should have been rejected")
        response_text = raw_resp.get_data(as_text=True)
        response_json = json.loads(response_text)
        self.assertIn("error", response_json, "error key missing from response")
        self.assertIn(ApiError.BATCH_SIZE_EXCEEDED, response_json['error'])

    def test_only_user_expenses_are_returned(self):
        self.assertTrue(False, "Only expenses belonging to the requesting user are send")
