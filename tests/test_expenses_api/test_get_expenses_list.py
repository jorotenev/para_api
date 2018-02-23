from tests.base_test import BaseTest, BaseTestWithHTTPMethodsMixin

from json import loads

from unittest.mock import patch

from app.db_facade.misc import OrderingDirection
from app.helpers.time import utc_now_str
from app.models.expense_validation import Validator

from tests.common_methods import sample_expenses
from tests.test_expenses_api import db_facade_path

from app.expenses_api.views import MAX_BATCH_SIZE, db_facade
from app.expenses_api.api_error_msgs import ApiError

endpoint = 'expenses_api.get_expenses_list'
reversed_expenses = list(reversed(sample_expenses))


@patch(db_facade_path, autospec=True)
class TestGETExpensesList(BaseTest, BaseTestWithHTTPMethodsMixin):
    def setUp(self):
        super(TestGETExpensesList, self).setUp()

        self.start_from_property = 'timestamp_utc'
        self.start_from_property_value = utc_now_str()
        self.valid_request_args = {
            "start_from_id": 'some id',
            "start_from_property": 'timestamp_utc',
            "start_from_property_value": utc_now_str(),
            "batch_size": 10,
            "ordering_direction": 'desc'
        }

    def test_valid_request_returns_valid_response(self, mocked_db):
        mocked_db.get_list.return_value = reversed_expenses[1:]
        batch_size = len(reversed_expenses) - 1

        request_params = self.valid_request_args.copy()
        request_params['start_from_property'] = self.start_from_property
        request_params['start_from_property_value'] = self.start_from_property_value
        request_params['start_from_id'] = reversed_expenses[0]['id']
        request_params['batch_size'] = batch_size
        request_params['ordering_direction'] = 'desc'

        raw_resp = self.get(endpoint, url_args=request_params,
                            raw_response=True)

        self.assertEqual(200, raw_resp.status_code)

        json_resp = loads(raw_resp.get_data(as_text=True))

        self.assertTrue(all([Validator.validate_expense_simple(exp) for exp in json_resp]),
                        "All returned objects must be valid expenses")

        self.assertEqual(batch_size, len(json_resp), "The result should be of size %i" % batch_size)

        property_values = [exp[self.start_from_property] for exp in json_resp]
        self.assertEqual(property_values, list(sorted(property_values, reverse=True)),
                         "Result should be sorted by the selected property descendigly")
        self.assertTrue(property_values[0] > property_values[1],
                        'The first result should be with the highest property value')

        self.assertLess(json_resp[0][self.start_from_property], reversed_expenses[0][self.start_from_property],
                        "The start_from must be `larger` than the first result when ordered in desc order")

    def test_with_invalid_params(self, mocked_db):
        batch_size = -1
        start_from = 1
        invalid_args = [
            {
                'start_from_property_value': 'boom',

                'start_from_id': sample_expenses[0]['id'],
                'start_from_property': 'timestamp_utc',
                'batch_size': 1,
                'ordering_direction': 'asc'
            },
            {
                'start_from_id': 1,

                'start_from_property': 'timestamp_utc',
                'start_from_property_value': utc_now_str(),
            },
            {
                'start_from_property_value': utc_now_str().replace('Z', '+00:00'),  # invalid for a ts to end in +00:00
                'start_from_property': 'timestamp_utc',
                'start_from_id': 'some str',
            }
        ]
        for args in invalid_args:
            mocked_db.get_list.return_value = []
            raw_resp = self.get(url=endpoint, url_args={'start_id': start_from, 'batch_size': batch_size})

            self.assertEqual(raw_resp.status_code, 400, "args should have been rejected" + str(args))
            json_resp = loads(raw_resp.get_data(as_text=True))
            self.assertIn("error", json_resp,
                          "error key missing from non-200 response")
            self.assertIn(ApiError.INVALID_QUERY_PARAMS, json_resp['error'])
            self.assertFalse(mocked_db.get_list.called, "Shouldn't have been called")
            mocked_db.get_list.reset_mock()

    def test_with_too_big_batch_size(self, mocked_db):
        batch_size = 100 + MAX_BATCH_SIZE
        url_args = self.valid_request_args.copy()
        url_args['batch_size'] = batch_size

        raw_resp = self.get(url=endpoint, url_args=url_args)
        self.assertEqual(413, raw_resp.status_code)

        response_text = raw_resp.get_data(as_text=True)
        response_json = loads(response_text)
        self.assertIn("error", response_json, "error key missing from response")
        self.assertIn(ApiError.BATCH_SIZE_EXCEEDED, response_json['error'])

        self.assertFalse(mocked_db.get_list.called)


@patch(db_facade_path, autospec=True)
class TestGetExpensesListInteractionWithDbFacade(BaseTest, BaseTestWithHTTPMethodsMixin):
    def test_call_on_good_request(self, mocked_db: type(db_facade)):
        mocked_db.get_list.return_value = []
        property_value = utc_now_str()
        property_name = 'timestamp_utc'
        id = 'asd'
        batch_size = 10
        request_args = {
            'start_from_id': id,
            'start_from_property_value': property_value,
            'start_from_property': property_name,
            'batch_size': batch_size,
        }
        resp = self.get(url=endpoint, url_args=request_args)

        self.assertEqual(1, mocked_db.get_list.call_count, 'The get list should have been called once')

        call_args, actual_kwargs = mocked_db.get_list.call_args
        self.assertEqual(0, len(call_args))
        expected_kwargs = {
            'property_value': property_value,
            'property_name': property_name,
            "ordering_direction": OrderingDirection.desc,
            'batch_size': batch_size,
            'user_uid': self.firebase_uid
        }
        self.assertEqual(len(expected_kwargs), len(actual_kwargs))

        self.assertDictEqual(expected_kwargs, actual_kwargs,
                             "get_list wasn't called with the expected kwargs")

        self.assertEqual(200, resp.status_code)
        self.assertEqual('[]', resp.get_data(as_text=True))
