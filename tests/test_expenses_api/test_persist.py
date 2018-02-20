from json import loads
from unittest.mock import patch

from app.expenses_api.views import ApiError
from tests.base_test import  BaseTest, BaseTestWithHTTPMethodsMixin
from tests.common_methods import SINGLE_EXPENSE, Validator
from tests.test_expenses_api import db_facade_path

endpoint = 'expenses_api.persist'


@patch(db_facade_path, autospec=True)
class TestPersist(BaseTest, BaseTestWithHTTPMethodsMixin):

    def test_normal_usage(self, mocked_db):
        mocked_db.persist.return_value = SINGLE_EXPENSE

        to_persist = SINGLE_EXPENSE.copy()
        to_persist['id'] = None
        raw_resp = self.post(url=endpoint, data=to_persist)
        self.assertEqual(200, raw_resp.status_code)

        json = loads(raw_resp.get_data(as_text=True))
        self.assertTrue(Validator.validate_expense_simple(json))

        to_persist['id'] = json['id']  # put it lipstick...
        self.assertDictEqual(to_persist, json, "The returned expense must be the same ")

    def test_fails_if_expense_is_with_id(self, mocked_db):
        raw_resp = self.post(url=endpoint, data=SINGLE_EXPENSE)

        self.assertEqual(400, raw_resp.status_code)
        self.assertIn(ApiError.ID_PROPERTY_FORBIDDEN, raw_resp.get_data(as_text=True))

    def test_fail_on_invalid_expense(self, _):
        raw_resp = self.post(url=endpoint, data={id: None})

        self.assertEqual(400, raw_resp.status_code)
        self.assertIn(ApiError.INVALID_EXPENSE, raw_resp.get_data(as_text=True))


@patch(db_facade_path, autospec=True)
class TestPersistUsesDbFacadeCorrectly(BaseTest, BaseTestWithHTTPMethodsMixin):
    def test_normal_usage(self, mocked_db):
        mocked_db.persist.return_value = SINGLE_EXPENSE
        to_persist = SINGLE_EXPENSE.copy()
        to_persist['id'] = None
        raw_resp = self.post(url=endpoint, data=to_persist)
        self.assertEqual(200, raw_resp.status_code)

        self.assertTrue(mocked_db.persist.called, "persist should have been called")
        args, _ = mocked_db.persist.call_args
        self.assertEqual(args, [SINGLE_EXPENSE, self.firebase_uid])
