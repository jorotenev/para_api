from app.models.sample_expenses import sample_expenses
from tests.test_db_facade.test_db_base import DbTestBase

seed_data = DbTestBase.withSeedDataDecorator


class TestRemove(DbTestBase):

    @seed_data
    def test_normal_usage(self):
        to_delete = sample_expenses[0]
        self.facade.remove(expense=to_delete, user_uid=self.firebase_uid)

        search_deleted = self.expenses_table.get_item(
            Key={
                'timestamp_utc': to_delete['timestamp_utc'],
                'user_uid': self.firebase_uid
            },
            ConsistentRead=True)
        self.assertNotIn("Item", search_deleted)  # flaky. not sure what the empty response looks like atm

    def test_delete_expense_of_correct_user(self):
        self.seedData(firebase_uid='one')
        self.seedData(firebase_uid='two')

        assert self.expenses_table.item_count == len(sample_expenses) * 2

        def get_expenses_of(user): return self.facade.get_list(property_value=None,
                                                               property_name='timestamp_utc',
                                                               user_uid=user)

        before_deleting = get_expenses_of('one')

        to_delete = before_deleting[0]
        self.facade.remove(to_delete, 'one')

        after_deleting = get_expenses_of('one')
        ids_after_deleting = [exp['ids'] for exp in after_deleting]
        self.assertEqual(len(sample_expenses) - 1, len(after_deleting))
        self.assertNotIn(to_delete['id'], ids_after_deleting)

        expenses_of_two = self.facade.get_list(property_name='timestamp_utc',
                                               property_value=None,
                                               user_uid='two')
        self.assertEqual(len(sample_expenses), len(expenses_of_two))
