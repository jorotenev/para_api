import json
from dateutil.relativedelta import relativedelta
from app.helpers.time import utc_now_str, ensure_ts_str_ends_with_z
from tests.base_test import BaseTest, BaseTestWithHTTPMethodsMixin, NoAuthenticationMarkerMixin
from tests.test_expenses_api import db_facade_path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from app.expenses_api.views import db_facade
from app.expenses_api.api_error_msgs import ApiError

endpoint = 'expenses_api.statistics'
valid_url_args = {"from_dt": (datetime.now(timezone.utc) - timedelta(minutes=60)).isoformat(), "to_dt": utc_now_str()}


class TestStatisticsAuth(BaseTest, BaseTestWithHTTPMethodsMixin):
    def test_auth(self):
        resp = self.get(url=endpoint, url_for_args=valid_url_args)
        self.assertEqual(403, resp.status_code)


@patch(db_facade_path, autospec=True)
class TestStatistics(BaseTest, BaseTestWithHTTPMethodsMixin, NoAuthenticationMarkerMixin):

    def test_normal_usage(self, mocked_db):
        mocked_result = {"BGN": 100}
        mocked_db.statistics.return_value = mocked_result

        raw_resp = self.get(url=endpoint, url_for_args=valid_url_args)

        self.assertTrue(mocked_db.statistics.called)
        self.assertEqual(200, raw_resp.status_code)

        self.assertDictEqual(mocked_result, json.loads(raw_resp.get_data(as_text=True)))

    def test_invalid_time_span(self, mocked_db):
        invalid_args = valid_url_args.copy()
        invalid_args["from_dt"] = (
                datetime.now(timezone.utc) - timedelta(days=60, minutes=1)).isoformat()

        raw_resp = self.get(url=endpoint, url_for_args=invalid_args)

        self.assertEqual(raw_resp.status_code, 400)
        self.assertIn(ApiError.MAXIMUM_TIME_WINDOW_EXCEEDED, raw_resp.get_data(as_text=True))
        self.assertFalse(mocked_db.statistics.called)
