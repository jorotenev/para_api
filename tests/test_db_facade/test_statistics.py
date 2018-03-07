from datetime import datetime as dt, timezone as tz, timedelta as td

from tests.test_db_facade.test_db_base import DbTestBase

from app.db_facade.facade import NoExpenseWithThisId
from app.helpers.time import utc_now_str, ensure_ts_str_ends_with_z
from app.models.sample_expenses import sample_expenses
from tests.common_methods import SINGLE_EXPENSE

seed_data = DbTestBase.withSeedDataDecorator

exp1 = sample_expenses[0].copy()
exp2 = sample_expenses[1].copy()
exp3 = sample_expenses[2].copy()
exp4 = sample_expenses[3].copy()

now = dt.now(tz.utc)
exp1_dt = ensure_ts_str_ends_with_z((now - td(hours=2)).isoformat())
exp1['timestamp_utc'] = exp1_dt
exp1['currency'] = "EUR"

exp2_dt = ensure_ts_str_ends_with_z((now - td(minutes=5)).isoformat())
exp2['timestamp_utc'] = exp2_dt
exp2['currency'] = "EUR"

exp3_dt = utc_now_str()
exp3['timestamp_utc'] = ensure_ts_str_ends_with_z((now - td(seconds=30)).isoformat())
exp3['currency'] = 'USD'

exp4_dt = ensure_ts_str_ends_with_z((now - td(seconds=5)).isoformat())
exp4['timestamp_utc'] = exp4_dt
exp4['currency'] = 'USD'


class TestStatistics(DbTestBase):

    def test_normal_usage(self):
        self.seedData(firebase_uid=self.firebase_uid, items=[exp1, exp2, exp3, exp4])
        test = [
            {
                'from': ensure_ts_str_ends_with_z((now - td(seconds=10)).isoformat()),
                'expected': {"USD": exp4['amount']}
            },
            {
                'from': ensure_ts_str_ends_with_z((now - td(seconds=40)).isoformat()),
                'expected': {"USD": exp4['amount'] + exp3['amount']}
            },
            {
                'from': ensure_ts_str_ends_with_z((now - td(minutes=6)).isoformat()),
                'expected': {"USD": exp4['amount'] + exp3['amount'], "EUR": exp2['amount']}
            },
            {
                'from': ensure_ts_str_ends_with_z((now - td(hours=3)).isoformat()),
                'expected': {"USD": exp4['amount'] + exp3['amount'], "EUR": exp2['amount'] + exp1['amount']}
            },
            {
                'from': ensure_ts_str_ends_with_z((now - td(seconds=1)).isoformat()),
                "expected": {}
            },
            {
                "from": ensure_ts_str_ends_with_z((dt.now(tz.utc) - td(hours=1)).isoformat()),
                "to": ensure_ts_str_ends_with_z((dt.now(tz.utc) - td(seconds=10)).isoformat()),
                "expected": {"EUR": exp2['amount'], "USD": exp3['amount']}
            }

        ]

        for i, t in enumerate(test):
            result = self.facade.statistics(
                from_dt=t['from'],
                to_dt=ensure_ts_str_ends_with_z(now.isoformat()),
                user_uid=self.firebase_uid)

            self.assertEqual(t['expected'], result, msg="failed for the %ith test - %s" % (i, str(t['from'])))

    def test_edge(self):
        self.seedData(firebase_uid=self.firebase_uid, items=[exp3, exp4])

        result = self.facade.statistics(
            from_dt=ensure_ts_str_ends_with_z((now - td(seconds=10)).isoformat()),
            to_dt=exp4_dt,
            user_uid=self.firebase_uid
        )

        self.assertEqual({}, result, 'to_dt is an exclusive boundary, from_dt is inclusive')
