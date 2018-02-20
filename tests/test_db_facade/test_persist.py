from app.db_facade.facade import PersistFailed
from app.models.expense_validation import Validator
from tests.common_methods import SINGLE_EXPENSE
from tests.test_db_facade.test_db_base import DbTestBase

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

    def test_invalid_expense(self):
        invalid_expenses = []

        invalid_expense_1 = SINGLE_EXPENSE.copy()
        del invalid_expense_1['timestamp_utc']
        invalid_expenses.append(invalid_expense_1)
        invalid_expense_2 = SINGLE_EXPENSE.copy()
        del invalid_expense_1['id']  # the id key should be present, but set to None for the exp to be valid
        invalid_expenses.append(invalid_expense_2)

        for invalid_expense in invalid_expenses:
            func_kwargs = {
                "expense": invalid_expense,
                "user_uid": self.firebase_uid
            }
            should_boom = self.facade.persist

            self.assertRaises(PersistFailed, should_boom, **func_kwargs)
