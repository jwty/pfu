from datetime import datetime, time, timedelta
from flask_apscheduler import APScheduler

scheduler = APScheduler()


def next_midnight() -> int:
    return int((datetime.combine(datetime.now().date(), time(0, 0)) + timedelta(1)).timestamp())
