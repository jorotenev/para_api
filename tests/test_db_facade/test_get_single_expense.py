from app.db_facade.facade import NoExpenseWithThisId
from tests.common_methods import SINGLE_EXPENSE
from tests.test_db_facade.test_db_base import DbTestBase

seed_data = DbTestBase.withSeedDataDecorator


class TestGetSingle(DbTestBase):
    @seed_data
    def test_normal_usage(self):
        exp = SINGLE_EXPENSE
        returned = self.facade.get_single(expense_id=exp['id'], user_id=self.firebase_uid)
        self.assertDictEqual(returned, exp)

    def test_on_no_such_expense(self):
        should_explode = self.facade.get_single
        func_kwargs = {
            "expense_id": 1,
            "user_id": self.firebase_uid
        }

        self.assertRaises(NoExpenseWithThisId, should_explode, **func_kwargs)
