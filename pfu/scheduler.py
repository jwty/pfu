from datetime import datetime, time, timedelta
from flask_apscheduler import APScheduler
from pfu.config import config
from pfu.db import get_today_expiring_files
from pfu.utils import integrity_check, remove_file, update_stats

scheduler = APScheduler()


def add_expire_job(filename: str, expire_date: int) -> None:
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


@scheduler.task('interval', hours=config.INTEGRITY_CHECK_INTERVAL, name='Integrity check')
def integrity_check_task() -> None:
    with scheduler.app.app_context():
        integrity_check()


@scheduler.task('interval', hours=config.UPDATE_STATS_INTERVAL, name='Update stats')
def update_stats_task() -> None:
    with scheduler.app.app_context():
        update_stats()


@scheduler.task('cron', hour='0', minute='0', next_run_time=datetime.now(), name='Prepare expire tasks')
def prepare_expire_tasks_task() -> None:
    expiring_files = get_today_expiring_files()
    scheduled_ids = {job.id for job in scheduler.get_jobs()}
    for expiring_file in expiring_files:
        if expiring_file['filename'] not in scheduled_ids:
            add_expire_job(expiring_file['filename'], expiring_file['expire_date'])
