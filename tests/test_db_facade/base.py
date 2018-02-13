from tests.base_test import BaseTest


class DbTestBase(BaseTest):
    @classmethod
    def setUpClass(cls):
        super(DbTestBase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(DbTestBase, cls).tearDownClass()

    def setUp(self):
        super(DbTestBase, self).setUp()

    def tearDown(self):
        super(DbTestBase, self).tearDown()



class DbTestMethodsMixin(object):
    pass
