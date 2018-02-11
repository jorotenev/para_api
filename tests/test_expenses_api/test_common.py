from tests.base_test import BaseTestWithHTTPMethods
from flask import current_app


class ExampleTest(BaseTestWithHTTPMethods):
    def test_sample(self):
        config = current_app.config
        response = self.get('api.ping', raw_response=False)
        self.assertIn('pong', response, "The HTML of the index page doesn't contain expected text")


class TestAuthHeader(BaseTestWithHTTPMethods):
    auth_header_name = 'x-firebase-auth-token'

    def test_request_to_protected_resources_requires_auth_token(self):
        default_args = {}  # api will use its defaults
        raw_resp = self.get('expenses_api.get_expenses_list', url_args=default_args, headers={})
        self.assertEqual(403, raw_resp.status_code,
                         'making a request to a protected resource should require a valid auth token')
