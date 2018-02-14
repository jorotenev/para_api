import signal


def deadline(timeout, msg="Function timed out"):
    """
    https://www.filosophy.org/post/32/python_function_execution_deadlines__in_simple_examples/
    decorates a function; given a deadline period, if the decorated function hasn't returned,
    a TimedOutExc is raised.
    :param timeout: in seconds
    :return:
    """

    def decorate(f):
        def handler(signum, frame):
            raise TimedOutExc(msg)

        def new_f(*args, **kwargs):
            # Set the signal handler and a 5-second alarm
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(timeout)
            # call the function
            res = f(*args, **kwargs)
            # disable the alarm
            signal.alarm(0)
            # return the result from the decorated function
            return res

        new_f.__name__ = f.__name__
        return new_f

    return decorate


class TimedOutExc(Exception):
    pass
