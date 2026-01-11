import datetime as dt


def get_utc_now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)
