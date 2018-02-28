from app.helpers.time import utc_now_str
from tests.test_db_facade.test_db_base import DbTestBase

from app.db_facade.facade import NoExpenseWithThisId, sanitize_expense
from app.models.expense_validation import Validator
from app.models.sample_expenses import sample_expenses

seed_data = DbTestBase.withSeedDataDecorator


class TestUpdate(DbTestBase):

    @seed_data
    def test_normal_usage(self):
        self.assertEqual(len(sample_expenses), self.expenses_table.item_count)

        old_expense = sample_expenses[0].copy()

        to_update = old_expense.copy()
        new_amount = old_expense['amount'] + 10
        to_update['amount'] = new_amount

        updated = self.facade.update(to_update, old_expense, self.firebase_uid)
        self.assertTrue(Validator.validate_expense_simple(updated))

        # check the item in the database now
        exp_from_db = self.expenses_table.get_item(
            Key={
                'user_uid': self.firebase_uid,
                'timestamp_utc': old_expense['timestamp_utc']
            },
            ConsistentRead=True)['Item']

        exp_from_db = self.facade.converter.convertFromDbFormat(sanitize_expense(exp_from_db))
        self.assertTrue(Validator.validate_expense_simple(exp_from_db))

        self.assertEqual(exp_from_db['id'], old_expense['id'])
        self.assertTrue(to_update['id'] == updated['id'] == old_expense['id'])
        self.assertEqual(exp_from_db['amount'], new_amount)

    @seed_data
    def test_on_range_attr_updated(self):
        old_exp = sample_expenses[0].copy()
        to_update = old_exp.copy()
        assert 'timestamp_utc' == self.facade.RANGE_KEY
        to_update['timestamp_utc'] = utc_now_str()
        assert to_update['timestamp_utc'] != old_exp['timestamp_utc']

        updated = self.facade.update(to_update, old_exp, user_uid=self.firebase_uid)
        self.assertTrue(updated['id'] == to_update['id'] == old_exp['id'])
        # check the item in the database now
        exp_from_db = self.expenses_table.get_item(
            Key={
                'user_uid': self.firebase_uid,
                'timestamp_utc': updated['timestamp_utc']
            },
            ConsistentRead=True)['Item']
        self.assertTrue(exp_from_db['id'] == old_exp['id'])

    @seed_data
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

    def test_ids_must_be_matching(self):
        old_exp = sample_expenses[0].copy()
        updated = old_exp.copy()
        old_exp['id'] = 'booom'

        should_boom = self.facade.update
        self.assertRaises(ValueError, should_boom, updated, old_exp, self.firebase_uid)

    def test_raises_exc_if_no_such_expense(self):
        assert self.expenses_table.item_count == 0

        should_boom = self.facade.update
        exp = sample_expenses[0].copy()
        self.assertRaises(NoExpenseWithThisId, should_boom, exp, exp, self.firebase_uid)

    @seed_data
    def test_raises_exc_if_id_at_rest_dont_matc(self):
        """
        if we have persisted some items, and we update one of them, but the updated expense has a different
        id, update() should fail
        """
        persisted = self.seeded_expenses[0].copy()
        persisted['id'] = 'something random'
        try:
            self.facade._standard_update(expense=persisted, user_uid=persisted['user_uid'])
            assert False
        except Exception as err:
            self.assertIn("no expense at rest found to update or the id of the expense at rest is not the same",
                          str(err))
