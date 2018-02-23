from tests.base_test import BaseTestWithHTTPMethodsMixin, BaseTest

from flask import current_app


class ExampleTest(BaseTest, BaseTestWithHTTPMethodsMixin):

    def test_sample(self):
        config = current_app.config
        response = self.get('api.ping', raw_response=False)
        self.assertIn('pong', response, "The HTML of the index page doesn't contain expected text")
