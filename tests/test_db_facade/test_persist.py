from app.db_facade.facade import PersistFailed
from tests.common_methods import SINGLE_EXPENSE
from tests.test_db_facade.test_db_base import DbTestBase

seed_data = DbTestBase.withSeedDataDecorator


class TestPersist(DbTestBase):

    def test_normal_usage(self):
        expense_to_persist = SINGLE_EXPENSE.copy()
        expense_to_persist['id'] = None

        persisted = self.facade.persist(expense_to_persist, user_uid=self.firebase_uid)

        self.assertEqual(1, persisted['id'])
        self.assertDictEqual(SINGLE_EXPENSE, persisted)

    def test_invalid_expense(self):
        expense_to_persist = SINGLE_EXPENSE.copy()
        del expense_to_persist['id']

        func_kwargs = {
            "expense": expense_to_persist,
            "user_uid": self.firebase_uid
        }
        should_boom = self.facade.persist

        self.assertRaises(PersistFailed, should_boom, **func_kwargs)
