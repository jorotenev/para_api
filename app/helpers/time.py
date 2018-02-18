from datetime import datetime, timezone


def utc_now_str():
    return ensure_ts_str_ends_with_z(datetime.now(timezone.utc).isoformat())


def ensure_ts_str_ends_with_z(ts_string: str):
    suffix = '+00:00'
    if ts_string.endswith(suffix):
        return ts_string.replace(suffix, 'Z')
    return ts_string
