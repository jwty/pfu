from datetime import datetime
from pfu.utils import remove_file
from pfu.scheduler import scheduler


def add_expire_job(filename, expire_date):
    # Just to make sure
    if not scheduler.get_job(filename):
        scheduler.add_job(
            id=filename,
            name=f'Expire {filename}',
            func=remove_file,
            args=[filename],
            trigger='date',
            run_date=datetime.fromtimestamp(expire_date),
            misfire_grace_time=None
        )
