from tests.base_test import BaseTest, BaseTestWithHTTPMethodsMixin
from flask import current_app


class TestAuthHeader(BaseTest, BaseTestWithHTTPMethodsMixin):

    def test_request_to_protected_resources_requires_auth_token(self):
        default_args = {}
        forcedEmptyHeaders = []

        raw_resp = self.get('expenses_api.honeypot', url_args=default_args, headers=forcedEmptyHeaders)
        self.assertEqual(403, raw_resp.status_code,
                         'making a request to a protected resource should require a valid auth token')
