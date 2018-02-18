from app.models.sample_expenses import sample_expenses
from tests.test_db_facade.test_db_base import DbTestBase
from app.db_facade.misc import OrderingDirection

seed_data = DbTestBase.withSeedDataDecorator


class SanityChecking(DbTestBase):

    @seed_data
    def test_seed_data_loads(self):
        self.assertEqual(len(sample_expenses), self.expenses_table.item_count)

    def test_tests_use_fresh_table(self):
        self.assertEqual(0, self.expenses_table.item_count)


class TestGetList(DbTestBase):

    @seed_data
    def test_returns_correct_items(self):
        batch_size = 5
        expenses = self.facade.get_list(
            None,
            user_uid=self.firebase_uid,
            property_name='timestamp_utc',
            ordering_direction=OrderingDirection.desc,
            batch_size=batch_size)

        self.assertEqual(len(expenses), batch_size)
        timestamps = [e['timestamp_utc'] for e in expenses]
        self.assertTrue(timestamps[0] > timestamps[1], "Expenses must be ordered from larger timestamp_utc to smaller")

        expected_expenses = list(reversed(sample_expenses))[0:batch_size]
        for i, expected_exp in enumerate(expected_expenses):
            self.assertDictEqual(expected_exp, expenses[i])

    def test_empty_list_if_no_data(self):
        assert 0 == self.expenses_table.item_count

        expenses = self.facade.get_list(
            None,
            self.firebase_uid,
            property_name='timestamp_utc',
            ordering_direction=OrderingDirection.desc,
            batch_size=5)

        self.assertEqual([], expenses)

    def test_doesnt_return_other_users_data(self):
        self.seedData(firebase_uid='one')
        assert self.expenses_table.item_count == len(sample_expenses)
        self.seedData(firebase_uid='two')
        assert self.expenses_table.item_count == len(sample_expenses) * 2

        batch_of_one = self.facade.get_list(
            property_name='timestamp_utc',
            property_value=None,
            user_uid='one',
        )

        batch_of_two = self.facade.get_list(
            property_name='timestamp_utc',
            property_value=None,
            user_uid='two',
        )
        self.assertEqual(len(sample_expenses), len(batch_of_one))
        self.assertEqual(len(sample_expenses), len(batch_of_two))
