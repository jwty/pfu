import logging
from datetime import datetime
from pfu.config import config_class
from pfu.db import get_today_expiring_files, add_expire_job
from pfu.utils import update_stats
from pfu.scheduler import scheduler


# TODO: Consider using own logs instead of apscheduler logs
# logger = logging.getLogger(__name__)
logging.getLogger('apscheduler').setLevel(logging.INFO)


@scheduler.task('interval', hours=config_class.UPDATE_STATS_INTERVAL, name='Update stats')
def update_stats_task():
    update_stats()


@scheduler.task('cron', hour=0, next_run_time=datetime.now(), name='Prepare expire tasks')
def prepare_expire_tasks_task():
    expiring_files = get_today_expiring_files()
    for expiring_file in expiring_files:
        add_expire_job(expiring_file['filename'], expiring_file['expire_date'])
