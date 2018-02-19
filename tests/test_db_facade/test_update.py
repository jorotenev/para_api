from tests.common_methods import is_valid_expense
from tests.test_db_facade.test_db_base import DbTestBase
from app.models.sample_expenses import sample_expenses

seed_data = DbTestBase.withSeedDataDecorator


class TestPersist(DbTestBase):

    @seed_data
    def test_normal_usage(self):
        self.assertEqual(len(sample_expenses), self.expenses_table.item_count)

        old_expense = sample_expenses[0].copy()

        to_update = old_expense.copy()
        new_amount = old_expense['amount'] + 10
        to_update['amount'] = new_amount

        updated = self.facade.update(to_update, old_expense, self.firebase_uid)
        self.assertTrue(is_valid_expense(updated))

        # check the item in the database now
        exp_from_db = self.expenses_table.get_item(
            Key={
                'user_uid': self.firebase_uid,
                'timestamp_utc': old_expense['timestamp_utc']
            },
            ConsistentRead=True)['Item']

        self.assertTrue(is_valid_expense(exp_from_db))

        self.assertEqual(exp_from_db['id'], old_expense['id'])
        self.assertEqual(exp_from_db['amount'], new_amount)

    def test_timestamp_is_updated(self):
        old_expense = sample_expenses[0].copy()
        returned = self.facade.update(old_expense, old_expense, self.firebase_uid)
        self.assertTrue(returned['timestamp_utc_updated'] > old_expense['timestamp_utc_updated'])

        raw_expense = self.expenses_table.get_item(
            Key={
                'timestamp_utc': old_expense['timestamp_utc'],
                'user_uid': self.firebase_uid
            },
            ConsistentRead=True)['Item']
        self.assertTrue(raw_expense['timestamp_utc_updated'] > old_expense['timestamp_utc_updated'])
        self.assertEqual(raw_expense['timestamp_utc_updated'], returned['timestamp_utc_updated'])
