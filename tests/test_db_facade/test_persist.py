from app.helpers.time import dt_from_utc_iso_str, utc_now_str
from app.models.sample_expenses import sample_expenses
from tests.test_db_facade.test_db_base import DbTestBase
from dateutil.parser import parse

from app.db_facade.facade import PersistFailed, ItemWithSameRangeKeyExists
from app.models.expense_validation import Validator
from tests.common_methods import SINGLE_EXPENSE

seed_data = DbTestBase.withSeedDataDecorator


class TestPersist(DbTestBase):

    def test_normal_usage(self):
        expense_to_persist = SINGLE_EXPENSE.copy()
        expense_to_persist['id'] = None

        persisted = self.facade.persist(expense_to_persist, user_uid=self.firebase_uid)
        self.assertTrue(Validator.validate_expense_simple(persisted))

        self.assertIsNotNone(persisted['id'])
        self.assertNotEqual(expense_to_persist['timestamp_utc_created'], persisted['timestamp_utc_created'],
                            "When an expense is created, its created_at must be set by the server right before persisting")

        raw_persisted_expense = self.expenses_table.get_item(
            Key={
                'timestamp_utc': persisted['timestamp_utc'],
                'user_uid': self.firebase_uid
            },
            ConsistentRead=True)['Item']

        self.assertEqual(raw_persisted_expense['id'], persisted['id'])

    def test_timestamp(self):
        exp = sample_expenses[0].copy()
        exp['id'] = None

        persisted = self.facade.persist(exp, user_uid=self.firebase_uid)
        now = dt_from_utc_iso_str(utc_now_str())

        persisted_at_dt = dt_from_utc_iso_str(persisted['timestamp_utc_created'])
        updated_at_dt = dt_from_utc_iso_str(persisted['timestamp_utc_created'])
        self.assertEqual(persisted_at_dt, updated_at_dt)

        for ts in [persisted_at_dt, updated_at_dt]:
            diff = int((now - ts).total_seconds())
            self.assertTrue(1 >= diff, "the expense's ts must be less than a second ago from now")

    def test_invalid_expense(self):
        invalid_expenses = []

        invalid_expense_1 = SINGLE_EXPENSE.copy()
        del invalid_expense_1['timestamp_utc']
        invalid_expense_1['id'] = None
        invalid_expenses.append(invalid_expense_1)

        for invalid_expense in invalid_expenses:
            func_kwargs = {
                "expense": invalid_expense,
                "user_uid": self.firebase_uid
            }
            should_boom = self.facade.persist

            self.assertRaises(PersistFailed, should_boom, **func_kwargs)

    @seed_data
    def test_fails_on_duplicate_range_key(self):
        persisted = sample_expenses[0].copy()
        persisted['id'] = None
        self.assertRaises(ItemWithSameRangeKeyExists, self.facade.persist, persisted, self.firebase_uid)

    def test_empty_name(self):
        to_persist = sample_expenses[0].copy()
        to_persist['id'] = None
        to_persist['name'] = ''
        persisted = self.facade.persist(to_persist, self.firebase_uid)

        last = self.facade.get_list(property_value=None, user_uid=self.firebase_uid, batch_size=1)[0]
        assert persisted['id'], last['id']

        self.assertEqual("", last['name'])
