from datetime import datetime, timezone

from dateutil.parser import parse


def utc_now_str():
    """
    https://momentjs.com/docs/#/displaying/as-iso-string/
    "2018-01-04T22:44:30.652Z"
    """
    return ensure_ts_str_ends_with_z(datetime.now(timezone.utc).isoformat())


def ensure_ts_str_ends_with_z(ts_string: str):
    """
    ensure a iso8601 str is in this format https://momentjs.com/docs/#/displaying/as-iso-string/
    :param iso8601 ts_string:
    :return: iso8601 with enforced Z at the end
    """
    suffix = '+00:00'
    if ts_string.endswith(suffix):
        return ts_string.replace(suffix, 'Z')
    return ts_string


def dt_from_utc_iso_str(s):
    return parse(s)