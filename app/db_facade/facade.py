class __DbFacade(object):
    def __init__(self):
        self.db_url = None

    def init_app(self, app):
        self.db_url = app.config.get("DB_URL")
        print("db url set to %s " % self.db_url)

    def get_single(self, expense_id, user_id):
        """

        :param expense_id:
        :param user_id:
        :return: the expense object
        :raises NoExpenseWithThisId
        """

    def get_list(self, start_id, user_uid, batch_size):
        """
        :param start_id: inclusive, from where to start the search
        :param user_uid: the user for which to search
        :param batch_size: how many items (at most)
        :return: a list of expense objects
        :raises NoSuchUser
        """
        batch_size = min(batch_size, MAX_BATCH_SIZE)
        return None

    def persist(self, expense, user_uid):
        """

        :param expense: expense with `id` parameter set to None
        :param user_uid:
        :return: the persisted expense
        """

    def update(self, expense, user_uid):
        """

        :param expense: a valid expense object with an `id`
        :param user_uid:
        :return: upon success, the expense, but with update timestamp_utc_updated
        :raises ValueError - expense doesn't have the `id` set to a non-None value
        :raises NoExpenseWithThisId
        :raises NoSuchUser
        """
        pass

    def remove(self, expense_id, user_uid):
        """

        :param expense_id: int
        :param user_uid:
        :return: boolean True on successful deletion
        :raises NoSuchUser
        :raises NoExpenseWithThisId
        """

    def sync(self, sync_request_objs, user_uid):
        """

        :param sync_request_objs: a list of dicts with `id` and `timestamp_utc_updated`
        :return:
        :raises NoSuchUser
        """

    def expense_exists(self, exp_id, user_uid):
        """
        :param exp_id:
        :param user_uid:
        :return: boolean
        :raises NoSuchUser
        """

    def largest_expense_id(self, user_uid):
        """
        :param user_uid:
        :return: int | None
        :raises  NoSuchUser
        """

    def asd(self):
        return self.db_url


class NoSuchUser(Exception):
    """
    Raised when an operation was performed using an uid, but there's no
    user with such uid
    """

    def __init__(self, *args, **kwargs):
        super(Exception, self).__init__(*args, **kwargs)


class NoExpenseWithThisId(Exception):
    def __init__(self, *args, **kwargs):
        super(Exception, self).__init__(*args, **kwargs)


MAX_BATCH_SIZE = 100
db_facade = __DbFacade()
