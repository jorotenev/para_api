import unittest, os
from app import create_app
from flask import url_for, Response
# usually, continuous integration providers set the CI env variable
from config import EnvironmentName
from tests.common_methods import TESTER_USER_FIREBASE_UID


class BaseTest(unittest.TestCase):
    # on class creation
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(config_name=EnvironmentName.testing)
        print("Running tests in environment")

        # this is needed to make url_for work
        cls.app.config['SERVER_NAME'] = 'localhost'

        cls.app_context = cls.app.app_context()
        cls.app_context.push()

        # the client acts as a client browser - it can make requests to our app as if a client is making them
        cls.client = cls.app.test_client(use_cookies=True)

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    def setUp(self):
        pass

    def tearDown(self):
        pass


class BaseTestWithHTTPMethodsMixin(object):
    """
    Class to be subclassed when doing client testing.
    """
    firebase_uid = TESTER_USER_FIREBASE_UID

    def post(self, url, data, url_args={}, **kwargs):
        return self.full_response(method='POST', data=data, url=url, url_args=url_args, **kwargs)

    def get(self, url, **kwargs):
        return self.full_response(url=url, **kwargs)

    def put(self, **kwargs):
        return self.full_response(method='PUT', **kwargs)

    def delete(self, **kwargs):
        return self.full_response(method='DELETE', **kwargs)

    def full_response(self, method='GET', data={}, url="", url_args={}, url_for_args={}, raw_response=True,
                      headers={}) -> Response:
        """
        :arg method [str] - the name of the http method
        :arg data [dict] - a dict with the payload
        :arg url  [string] - endpoint (NOT a ready url) e.g. main.index and *not* just /
        :arg url_args - these will be passed as url query arguments:
            e.g. in /user&id=1 id=1 would have been made by url_args={'id':1}
        :arg raw_response [boolean] - if false, the return value of this method will be the text response from the server;
            otherwise the raw response
        :arg url_for_args [dict] - will be passed to url_for when building the url for the endpoint
        :returns the data of the response (e.g. the return of the view function of the server)
        """
        common_args = [url_for(url, **url_for_args, _external=True)]
        common_kwargs = {
            "data": data,
            "follow_redirects": True,
            "query_string": url_args,
            'headers': headers  # [('Content-Type', 'text/html; charset=utf-8'),]
        }
        method_name = method.lower()
        print('calling %s' % method_name)
        method = getattr(self.client, method_name)
        if not method:
            raise Exception("unknown method %s" % method_name)
        res = method(*common_args, **common_kwargs)

        if not raw_response:
            res = res.get_data(as_text=True)
        return res
