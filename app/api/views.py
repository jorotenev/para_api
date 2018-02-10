from app.api_utils.response import make_json_response
from . import api
from requests import get
import os


@api.route("/ping")
def ping():
    return "pong"


@api.route('/test-500')
def test_500():
    return make_json_response({"error": "error msg"}, 500)


@api.route('/test-200')
def test_200():
    return make_json_response('{"content": "rebra"}')


@api.route('/test-internet')
def internet():
    resp = get("http://api.yomomma.info/")
    print(resp.text.capitalize())
    return resp.text.capitalize()
