from app.models.sample_expenses import sample_expenses
from tests.test_db_facade.test_db_base import DbTestBase

seed_data = DbTestBase.withSeedDataDecorator


class SanityChecking(DbTestBase):

    @seed_data
    def test_seed_data_loads(self):
        print('testing')
        self.assertEqual(len(sample_expenses), self.expenses_table.item_count)

    def test_tests_use_fresh_table(self):
        self.assertEqual(0, self.expenses_table.item_count)


class TestGetList(DbTestBase):

    @seed_data
    def test_returns_correct_items(self):
        batch_size = 5
        expenses = self.facade.get_list(10, self.firebase_uid, batch_size)

        self.assertEqual(len(expenses), batch_size)
        ids = [e['id'] for e in expenses]
        self.assertTrue(ids[0] > ids[1], "Expenses must be ordered from larger ID to smaller")

        expected_expenses = list(reversed(sample_expenses))[0:batch_size]
        for i, expected_exp in enumerate(expected_expenses):
            self.assertDictEqual(expected_exp, expenses[i])

    def test_empty_list_if_no_data(self):
        self.assertEqual([], self.facade.get_list(10, self.firebase_uid, 5))

        self.seedData()
        self.assertEqual([], self.facade.get_list(10, 'this is some other uid', 5),
                         "Shouldn't return expenses for another user")
