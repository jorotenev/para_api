import uuid

from app.helpers.time import utc_now_str
from app.models.sample_expenses import sample_expenses
from tests.test_db_facade.test_db_base import DbTestBase

seed_data = DbTestBase.withSeedDataDecorator


def delete(table, exp_to_delete, user_uid):
    exp_to_delete = sample_expenses[1]
    return table.delete_item(
        Key={
            'timestamp_utc': exp_to_delete,
            'user_uid': user_uid
        },
        ReturnValues="ALL_OLD"
    )


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
        exp_to_delete = sample_expenses[1]
        resp = delete(table=self.expenses_table, exp_to_delete=exp_to_delete, user_uid=self.firebase_uid)
        self.assertIn("Attributes", resp.keys(), "If missing, the delete operation didn't delete the specified entry")
        deleted_exp = resp['Attributes']
        self.assertEqual(deleted_exp['amount'], exp_to_delete['amount'])

        # add an item
        new_expense = sample_expenses[-1].copy()
        new_expense['id'] = uuid.uuid4()
        new_expense['timestamp_utc'] = utc_now_str()
        new_expense['timestamp_utc_created'] = utc_now_str()
        new_expense['timestamp_utc_updated'] = utc_now_str()
        new_expense['user_uid'] = self.firebase_uid
        self.expenses_table.put_item(Item=new_expense)

        # now verify that sync() returns correct result
        sync_result = self.facade.sync(sample_expenses, self.firebase_uid)
        self.assertIn("to_add", sync_result.keys())
        self.assertIn("to_delete", sync_result.keys())
        self.assertIn("to_update", sync_result.keys())

        self.assertEqual(len(sync_result['to_add']), 1)
        self.assertEqual(new_expense['id'], sync_result['to_add'][0]['id'])

        self.assertEqual(len(sync_result['to_update']), 1)
        self.assertEqual(to_update['id'], sync_result['to_update'][0]['id'])

        self.assertEqual(len(sync_result['to_remove']), 1)
        self.assertEqual(exp_to_delete['id'], sync_result['to_remove'][0]['id'])
