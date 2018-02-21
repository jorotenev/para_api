import uuid

from app.helpers.time import utc_now_str
from app.models.sample_expenses import sample_expenses
from tests.test_db_facade.test_db_base import DbTestBase

seed_data = DbTestBase.withSeedDataDecorator


def delete_exp(table, exp_to_delete, user_uid):
    return table.delete_item(
        Key={
            'timestamp_utc': exp_to_delete['timestamp_utc'],
            'user_uid': user_uid
        },
        ReturnValues="ALL_OLD"
    )


def generate_sync_request():
    ts_key = 'timestamp_utc_updated'
    return {exp['id']: {ts_key: exp[ts_key]} for exp in sample_expenses}


class TestSync(DbTestBase):

    @seed_data
    def test_normal_usage(self):
        # update the ts_updated of an item
        to_update = sample_expenses[0]
        self.expenses_table.update_item(
            Key={
                'timestamp_utc': to_update['timestamp_utc'],
                'user_uid': self.firebase_uid
            },
            AttributeUpdates={
                'timestamp_utc_updated': {
                    'Value': utc_now_str(),
                    'Action': 'PUT'
                },
            })
        # delete an item
        expense_to_delete = sample_expenses[1]
        resp = delete_exp(table=self.expenses_table, exp_to_delete=expense_to_delete, user_uid=self.firebase_uid)

        self.assertIn("Attributes", resp.keys(), "If missing, the delete operation didn't delete the specified entry")
        deleted_exp = self.facade.converter.convertFromDbFormat(resp['Attributes'])

        self.assertEqual(deleted_exp['amount'], expense_to_delete['amount'])

        # add an item
        new_expense = sample_expenses[-1].copy()
        new_expense['id'] = str(uuid.uuid4())
        new_expense['timestamp_utc'] = utc_now_str()
        new_expense['timestamp_utc_created'] = utc_now_str()
        new_expense['timestamp_utc_updated'] = utc_now_str()
        new_expense['user_uid'] = self.firebase_uid
        self.expenses_table.put_item(Item=self.facade.converter.convertToDbFormat(new_expense))

        # now verify that sync() returns correct result
        request = generate_sync_request()
        sync_result = self.facade.sync(request, self.firebase_uid)
        self.assertIn("to_add", sync_result.keys())
        self.assertIn("to_remove", sync_result.keys())
        self.assertIn("to_update", sync_result.keys())

        self.assertEqual(len(sync_result['to_add']), 1)
        self.assertEqual(new_expense['id'], sync_result['to_add'][0]['id'])

        self.assertEqual(len(sync_result['to_update']), 1)
        self.assertEqual(to_update['id'], sync_result['to_update'][0]['id'])

        self.assertEqual(len(sync_result['to_remove']), 1)
        self.assertEqual(expense_to_delete['id'], sync_result['to_remove'][0])
