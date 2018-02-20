from tests.base_test import BaseTestWithHTTPMethodsMixin, BaseTest
from flask import current_app
from unittest.mock import patch, MagicMock

from tests.common_methods import SINGLE_EXPENSE


class ExampleTest(BaseTest, BaseTestWithHTTPMethodsMixin):
    def test_sample(self):
        config = current_app.config
        response = self.get('api.ping', raw_response=False)
        self.assertIn('pong', response, "The HTML of the index page doesn't contain expected text")

    @patch('app.api.views.db_facade', autospec=True)
    def test_mock(self, mocked_facade):
        mocked_facade.ping_db.return_value = 'booom :)'
        raw_resp = self.get('api.test')
        assert raw_resp.status_code == 200
        self.assertTrue(mocked_facade.ping_db.called, 'the mock wasn\'t called')
        self.assertEqual('booom :)', raw_resp.get_data(as_text=True))


@patch('app.api.views.db_facade', autospec=True)
class DemoTestPatched(BaseTest, BaseTestWithHTTPMethodsMixin):
    """
    mocked is reset for each test_
    """

    def test_some(self, mocked_db_facade):
        mocked_db_facade.ping_db.return_value = 'ping_db'
        self.get('api.test')

        self.assertEqual(1, mocked_db_facade.ping_db.call_count)

    def test_some_more(self, mocked_db_facade):
        mocked_db_facade.ping_db.return_value = 'boo'
        resp = self.get('api.test')

        self.assertEqual('boo', resp.get_data(as_text=True))
        self.assertEqual(1, mocked_db_facade.ping_db.call_count)

    def test_type(self, mocked_db_facade):
        from app.api.views import db_facade
        self.assertEqual(str(MagicMock), str(type(db_facade.ping_db)))


class DeepEquality(BaseTest, BaseTestWithHTTPMethodsMixin):
    def test_deep_equal(self):
        copy = SINGLE_EXPENSE.copy()
        copy['id'] = 1000
        copy2 = SINGLE_EXPENSE.copy()
        copy2['id'] = 1000
        self.assertEqual([copy, 'asd'], [copy2, 'asd'])


@patch('app.api.views.db_facade', autospec=True)
class TestRaises(BaseTest, BaseTestWithHTTPMethodsMixin):
    def test_raises(self, mocked_db):
        mocked_db.get_list.side_effect = KeyError('booom')
        start_id = 1
        batch_size = 1
        self.assertRaises(KeyError, mocked_db.get_list, start_id, batch_size, 'uid')
