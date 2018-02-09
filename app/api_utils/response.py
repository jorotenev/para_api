import json

from flask import Response


def make_json_response(json_str, status_code=200, mimetype='application/json'):
    if type(json_str) != str:
        json_str = json.dumps(json_str)

    return Response(json_str, status=status_code, mimetype=mimetype)
