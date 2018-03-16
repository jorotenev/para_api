from flask import current_app

from app.models.expense_validation import Validator
from tests.common_methods import SINGLE_EXPENSE
from tests.test_db_facade.test_db_base import DbTestBase
from datetime import datetime as dt, timedelta as td, timezone
import uuid
from app.helpers.time import utc_now_str, ensure_ts_str_ends_with_z
from app.models.sample_expenses import sample_expenses

seed_data = DbTestBase.withSeedDataDecorator


def generate_sync_request(expenses):
    ts_key = 'timestamp_utc_updated'
    return {exp['id']: {
        'timestamp_utc_updated': exp['timestamp_utc_updated'],
        'timestamp_utc': exp['timestamp_utc']
    } for exp in expenses}


def generate_expenses(size):
    items = []
    now = dt.now(timezone.utc)
    exp = SINGLE_EXPENSE.copy()
    for i in range(size):
        temp = exp.copy()
        temp['id'] = str(i)
        temp['timestamp_utc'] = temp['timestamp_utc_updated'] = ensure_ts_str_ends_with_z(
            (now - td(seconds=i)).isoformat())
        items.append(temp)
    return items


class TestSync(DbTestBase):

    @seed_data
    def test_normal_usage(self):
        assert current_app.config['MAX_SYNC_REQUEST_SIZE'] == self.facade.max_sync_request_size
        items = self.seeded_expenses
        self._test_sync(items)

    def test_with_more_expenses(self):
        from flask import current_app
        max_sync_request_size = current_app.config['MAX_SYNC_REQUEST_SIZE']
        items = generate_expenses(max_sync_request_size + 10)

        self.seedData(firebase_uid=self.firebase_uid, items=items)

        # self._test_sync(items)
        oldest = items[-1]
        self._touch_expense_in_db(item=oldest)
        request = generate_sync_request(items[:max_sync_request_size])
        response = self.facade.sync(sync_request_objs=request, user_uid=self.firebase_uid)
        self._valid_sync_response(response)
        msg = "Should be empty because the updated expense outside the query limit"
        self.assertEqual(0, len(response['to_update']), msg)
        self.assertEqual(0, len(response['to_add']), msg)

    def _test_sync(self, items):
        """
        sanity checking for performing the sync operation.
        updates, removes and adds an item to the underlying db.
        then calls sync() and checks its result
        :param items: the items that have been persisted in the database
        """
        # update the ts_updated of an item
        to_update = items[0]
        self._touch_expense_in_db(to_update)
        # delete an item
        expense_to_delete = items[1]
        resp = self._delete_exp(table=self.expenses_table, exp_to_delete=expense_to_delete, user_uid=self.firebase_uid)
        self.assertIn("Attributes", resp.keys(), "If missing, the delete operation didn't delete the specified entry")
        deleted_exp = self.facade.converter.convertFromDbFormat(resp['Attributes'])
        self.assertEqual(deleted_exp['amount'], expense_to_delete['amount'])
        # add an item
        new_expense = self._make_expense()
        # now verify that sync() returns correct result
        request = generate_sync_request(items)
        sync_result = self.facade.sync(request, self.firebase_uid)
        self._valid_sync_response(sync_result)
        self.assertEqual(len(sync_result['to_add']), 1)
        self.assertEqual(new_expense['id'], sync_result['to_add'][0]['id'])
        self.assertEqual(len(sync_result['to_update']), 1)
        self.assertEqual(to_update['id'], sync_result['to_update'][0]['id'])
        self.assertEqual(len(sync_result['to_remove']), 1)
        self.assertEqual(expense_to_delete['id'], sync_result['to_remove'][0])

    def _valid_sync_response(self, sync_result):
        self.assertIn("to_add", sync_result.keys())
        self.assertIn("to_remove", sync_result.keys())
        self.assertIn("to_update", sync_result.keys())
        self.assertTrue(all(Validator.validate_expense_simple(e) for e in sync_result['to_add']))
        self.assertTrue(all(Validator.validate_expense_simple(e) for e in sync_result['to_update']))
        self.assertTrue(all(Validator.validate_property(exp_id, 'id') for exp_id in sync_result['to_remove']))

    def _make_expense(self):
        new_expense = sample_expenses[-1].copy()
        new_expense['id'] = str(uuid.uuid4())
        now = utc_now_str()
        new_expense['timestamp_utc'] = now
        new_expense['timestamp_utc_created'] = now
        new_expense['timestamp_utc_updated'] = now
        new_expense['user_uid'] = self.firebase_uid
        self.expenses_table.put_item(Item=self.facade.converter.convertToDbFormat(new_expense))
        return new_expense

    def _touch_expense_in_db(self, item, others=[]):
        """

        :param item:
        :param others: list of dicts. each dict has "attr" and "value" keys
        :return:
        """
        other_updates = {}
        for other in others:
            other_updates[other['attr']] = {"Value": other['value'], 'Action': "PUT"}

        self.expenses_table.update_item(
            Key={
                'timestamp_utc': item['timestamp_utc'],
                'user_uid': self.firebase_uid
            },
            AttributeUpdates={
                'timestamp_utc_updated': {
                    'Value': utc_now_str(),
                    'Action': 'PUT'
                },
                **other_updates
            })

    def _delete_exp(self, table, exp_to_delete, user_uid):
        return table.delete_item(
            Key={
                'timestamp_utc': exp_to_delete['timestamp_utc'],
                'user_uid': user_uid
            },
            ReturnValues="ALL_OLD"
        )
