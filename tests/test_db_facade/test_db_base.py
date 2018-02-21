from tests.base_test import BaseTest

from app.db_facade import db_facade, dynamodb_users_table_init_information
from app.db_facade.dynamodb.dynamo import create_table_sync, DELETE_table_sync, EMPTY_table_contents


class DbTestBase(BaseTest):

    @classmethod
    def setUpClass(cls):
        super(DbTestBase, cls).setUpClass()

        cls.raw_db = db_facade.raw_db
        cls.facade = db_facade
        assert db_facade.EXPENSES_TABLE_NAME != db_facade.EXPENSES_TABLE_NAME_PREFIX, 'db facade hasnt been initialised'
        create_table_sync(cls.raw_db, table_name=db_facade.EXPENSES_TABLE_NAME,
                          **dynamodb_users_table_init_information)
        cls.expenses_table = cls.raw_db.Table(db_facade.EXPENSES_TABLE_NAME)

    @classmethod
    def tearDownClass(cls):
        super(DbTestBase, cls).tearDownClass()
        DELETE_table_sync(cls.raw_db, table_name=db_facade.EXPENSES_TABLE_NAME)

    def setUp(self):
        super(DbTestBase, self).setUp()
        EMPTY_table_contents(self.raw_db, table_name=db_facade.EXPENSES_TABLE_NAME, hash_key=db_facade.HASH_KEY,
                             range_key=db_facade.RANGE_KEY)
        self.expenses_table.reload()

    def tearDown(self):
        super(DbTestBase, self).tearDown()
        EMPTY_table_contents(self.raw_db, table_name=db_facade.EXPENSES_TABLE_NAME, hash_key=db_facade.HASH_KEY,
                             range_key=db_facade.RANGE_KEY)
        self.expenses_table.reload()

    @staticmethod
    def withSeedDataDecorator(f):

        def wrapper(*args, **kwargs):
            self = args[0]
            self.seedData()
            print("\n***seeded***\n")
            return f(*args, **kwargs)

        return wrapper

    def seedData(self, firebase_uid=None):
        from app.models.sample_expenses import sample_expenses
        valid_items = [exp.copy() for exp in sample_expenses]
        firebase_uid = firebase_uid or self.firebase_uid

        for exp in valid_items:
            exp['user_uid'] = firebase_uid

        prepared = map(db_facade.converter.convertToDbFormat, valid_items)

        with self.expenses_table.batch_writer() as batch:
            for exp in prepared:
                batch.put_item(Item=exp)

        self.seeded_expenses = valid_items
        self.expenses_table.reload()
