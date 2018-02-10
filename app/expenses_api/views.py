import json
from flask import request

from app.api_utils.response import make_json_response
from . import expenses_api
from datetime import datetime as dt, timezone as tz

# {
#     "id": 10,
#     "name": "server id 10",
#     "amount": 95,
#     "currency": "EUR,
#     "tags": [
#         "vacation",
#         "vacation",
#         "work"
#     ],
#     "timestamp_utc": "2018-02-10T18:55:40.561052+00:00"
# }
MAX_ID = 50


@expenses_api.route("/get_expenses_list")
def get_expenses_list():
    start_id = request.args.get('start_id', type=int, default=MAX_ID)
    start_id = min(start_id, MAX_ID)
    batch_size = request.args.get('batch_size', type=int, default=10)

    response = []
    last_id = max(1, start_id - batch_size + 1)

    for i in range(last_id, start_id + 1):
        response.append({
            "id": i,
            "name": "server id %s" % str(i),
            "amount": i * 10 + 1,
            "currency": "EUR",
            "tags": [] if i % 2 == 0 else ['vacation', 'work'],
            'timestamp_utc': dt.now(tz.utc).isoformat(),
            'timestamp_utc_created': dt.now(tz.utc).isoformat(),
            'timestamp_utc_updated': dt.now(tz.utc).isoformat(),
        })

    response.sort(key=lambda expense: expense['id'], reverse=True)
    return make_json_response(response)
