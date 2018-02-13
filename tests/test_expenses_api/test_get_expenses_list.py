import json
from unittest.mock import patch

from app.expenses_api.views import MAXIMUM_BATCH_SIZE, ApiError, db_facade
from tests.base_test import BaseTest, BaseTestWithHTTPMethodsMixin
from json import loads

from tests.common_methods import is_valid_expense, sample_expenses
from tests.test_expenses_api import db_facade_path

endpoint = 'expenses_api.get_expenses_list'
reversed_expenses = list(reversed(sample_expenses))


@patch(db_facade_path, autospec=True)
class TestGETExpensesList(BaseTest, BaseTestWithHTTPMethodsMixin):

    def test_valid_request_returns_valid_response(self, mocked_db):
        mocked_db.get_list.return_value = reversed_expenses

        batch_size = len(reversed_expenses)
        start_id = reversed_expenses[0]['id']
        raw_resp = self.get(endpoint, url_args={"start_id": start_id, 'batch_size': batch_size},
                            raw_response=False)

        json_resp = loads(raw_resp)

        self.assertEqual(batch_size, len(json_resp), "The result should be of size %i" % batch_size)

        ids = [exp['id'] for exp in json_resp]
        self.assertEqual(ids, list(sorted(ids, reverse=True)), "Result should be sorted by id descendigly")
        self.assertTrue(ids[0] > ids[1], 'The first result should be with the highest id')

        self.assertTrue(all([is_valid_expense(exp) for exp in json_resp]),
                        "All returned objects must be valid expenses")

        self.assertEqual(start_id, ids[0], "The first id is not start_id")

    def test_with_invalid_params(self, mocked_db):
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
            raw_resp = self.get(url=endpoint, url_args={'start_id': start_from, 'batch_size': batch_size})

            self.assertEqual(raw_resp.status_code, 400, "args should have been rejected" + str(args))
            json_resp = json.loads(raw_resp.get_data(as_text=True))
            self.assertIn("error", json_resp,
                          "error key missing from non-200 response")
            self.assertIn(ApiError.INVALID_QUERY_PARAMS, json_resp['error'])
            self.assertFalse(mocked_db.get_list.called, "Shouldn't have been called")
            mocked_db.get_list.reset_mock()

    def test_with_too_big_batch_size(self, mocked_db):
        batch_size = 100 + MAXIMUM_BATCH_SIZE
        start_id = batch_size

        raw_resp = self.get(url=endpoint, url_args={'start_id': start_id, "batch_size": batch_size})
        self.assertEqual(413, raw_resp.status_code)

        response_text = raw_resp.get_data(as_text=True)
        response_json = json.loads(response_text)
        self.assertIn("error", response_json, "error key missing from response")
        self.assertIn(ApiError.BATCH_SIZE_EXCEEDED, response_json['error'])

        self.assertFalse(mocked_db.get_list.called)

    def test_only_user_expenses_are_returned(self, _):
        self.assertTrue(False, "Only expenses belonging to the requesting user are send")


@patch(db_facade_path, autospec=True)
class TestGetExpensesListInteractionWithDbFacade(BaseTest, BaseTestWithHTTPMethodsMixin):
    def test_call_on_good_request(self, mocked_db: type(db_facade)):
        mocked_db.get_list.return_value = []

        request_args = {'start_id': 10, 'batch_size': 10}
        resp = self.get(url=endpoint, url_args=request_args)

        self.assertEqual(1, mocked_db.get_list.call_count, 'The get list should have been called once')

        call_args, call_kwargs = mocked_db.get_list.call_args
        self.assertEqual(0, len(call_kwargs))
        self.assertEqual([request_args['start_id'], request_args['batch_size'], self.firebase_uid], call_args,
                         "get_list wasn't called with the expected args")

        self.assertEqual(200, resp.status_code)
        self.assertEqual('[]', resp.get_data(as_text=True))
