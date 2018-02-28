from time import sleep
from app.helpers.utils import deadline
from flask import current_app

"""
http://boto3.readthedocs.io/en/latest/reference/services/dynamodb.html
"""


@deadline(100)
def create_table_sync(dynamodb_resource, table_name, silent_if_existing=True, **kwargs):
    try:
        table = dynamodb_resource.create_table(
            TableName=table_name,
            **kwargs
        )
        print("waiting for table [%s] to be created" % table_name)
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        # dynamodb_resource.meta.client.tag_resource(ResourceArn=table.table_arn,
        #                                            Tags=[
        #                                                {
        #                                                    "Key": "project",
        #                                                    "Value": "val"
        #                                                }
        #                                            ])

        print("table [%s] created" % table_name)

    except Exception as err:
        if "Cannot create preexisting table" in str(err) and silent_if_existing:
            print("Table exists. Skipping")
        else:
            raise err


@deadline(2, "Deletion hasn't completed in 2 seconds")
def DELETE_table_sync(dynamodb_resource, table_name):
    """

    :param dynamodb_resource:
    :param table_name:
    :return: boolean - true if the table was delete; False if no such table exists
    :raise TimedOutExc - if the table has been deleted after 5 seconds
    :raise Exception - whatever the call to the underlying boto3 method raised
    """
    try:
        _ = dynamodb_resource.meta.client.delete_table(TableName=table_name)
    except Exception as err:
        if "ResourceNotFoundException" in str(err):
            print('trying to delete non-existing table ' + table_name)
            return False
        else:
            raise err

    # await deletion
    sleep_time = 0.1
    while True:
        sleep(sleep_time)
        if table_name not in [table.table_name for table in dynamodb_resource.tables.all()]:
            return True
        else:
            continue


@deadline(2)
def EMPTY_table_contents(dynamodb_resource, table_name, hash_key, range_key):
    table = dynamodb_resource.Table(table_name)
    with table.batch_writer() as batch:
        items = table.scan()['Items']
        for item in items:
            batch.delete_item(Key={
                hash_key: item[hash_key],
                range_key: item[range_key]
            })
    table.reload()
    while True:
        if table.item_count == 0:
            return
        sleep(0.01)


def item_count(table):
    pass
