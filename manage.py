#!/usr/bin/env python
import os
import sys
from os.path import dirname, join
from dotenv import load_dotenv

from app.helpers.time import ensure_ts_str_ends_with_z

if os.environ.get("ENV_DOT_FILE"):
    dotenv_path = join(dirname(__file__), os.environ.get("ENV_DOT_FILE"))  # will fail silently if file is missing
    load_dotenv(dotenv_path, verbose=True)
else:
    print("Not using .env file to load env vars")

from app import create_app
from config import EnvironmentName

app_mode = None
try:
    app_mode = os.environ['APP_STAGE']
except KeyError:
    print("Set the APP_STAGE environmental variable: %s" % ",".join(EnvironmentName.all_names()))
    exit(1)

app = create_app(app_mode)


@app.cli.command()
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    sys.exit(not result.wasSuccessful())


@app.cli.command()
def create_expenses_table():
    from app.db_facade import db_facade

    table_name = db_facade.EXPENSES_TABLE_NAME
    from app.db_facade.dynamodb.dynamo import create_table_sync
    from app.db_facade.table_schema import dynamodb_users_table_init_information
    print("creating dynamodb table [%s]" % table_name)
    create_table_sync(dynamodb_resource=db_facade.raw_db,
                      table_name=table_name,
                      **dynamodb_users_table_init_information)
    print("ok")


@app.cli.command()
def delete_expenses_table():
    from app.db_facade import db_facade
    table_name = db_facade.EXPENSES_TABLE_NAME
    print("deleting dynamodb table [%s]" % table_name)

    from app.db_facade.dynamodb.dynamo import DELETE_table_sync
    DELETE_table_sync(dynamodb_resource=db_facade.raw_db, table_name=table_name)
    print('ok')


@app.cli.command(with_appcontext=True)
def seed_data():
    import uuid, datetime
    from app.db_facade.facade import db_facade
    from flask import current_app
    seed = {
        "id": "",
        "name": "",
        "amount": 95,
        "currency": "EUR",
        "tags": [
            "vacation",
            "vacation",
            "work"
        ],
        "timestamp_utc": "",
        "timestamp_utc_created": "",
        "timestamp_utc_updated": ""
    }
    now = datetime.datetime.now(datetime.timezone.utc)
    expenses = []
    print("seeding dynamodb table [%s]" % db_facade.EXPENSES_TABLE_NAME)

    for i in range(1, 26):
        temp = seed.copy()
        temp['user_uid'] = current_app.config['TEST_FIREBASE_UID']
        temp['id'] = str(uuid.uuid4())
        temp['name'] = 'server id ' + str(i)
        temp['timestamp_utc'] = temp['timestamp_utc_created'] = temp[
            'timestamp_utc_updated'] = ensure_ts_str_ends_with_z((now + datetime.timedelta(seconds=i)).isoformat())
        expenses.append(temp)

    items = [{"PutRequest": {'Item': expense}} for expense in expenses]
    unprocessed_items = None

    while unprocessed_items == None or len(unprocessed_items) > 0:
        resp = db_facade.raw_db.batch_write_item(
            RequestItems={
                db_facade.EXPENSES_TABLE_NAME: items
            }
        )
        if resp['UnprocessedItems']:
            unprocessed_items = resp['UnprocessedItems'][db_facade.EXPENSES_TABLE_NAME]
        else:
            break  # no unprocessed items -> done
    print('ok')


@app.cli.command(with_appcontext=False)
def boom():
    app = create_app('staging')
    with app.app_context():
        from app.db_facade import db_facade
        print(db_facade.EXPENSES_TABLE_NAME)
