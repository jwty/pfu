from datetime import datetime
from pfu.config import config
from pfu.db import get_today_expiring_files
from pfu.jobs import add_expire_job
from pfu.utils import update_stats
from pfu.scheduler import scheduler


@scheduler.task('interval', hours=config.UPDATE_STATS_INTERVAL, name='Update stats')
def update_stats_task():
    with scheduler.app.app_context():
        update_stats()


# Task runs a bit past midnight to avoid potential race condition:
# - if it runs at midnight it can pick up files which were in the process of being deleted but their db entry was not yet deleted
#   (this worked but warning logs from apscheduler were annoying)
# - offset from midnight allows midnight expire jobs to safely finish and files are not picked up by this task again
# - with X minutes offset from midnight these files are deleted at most X minutes late due to "misfire_grace_time=None" in expire jobs
# Since expire jobs should run very quickly, the offset could probably be as low as couple seconds (and will be tweaked in future),
# for now some files being potentially deleted at most 5 minutes late is acceptable tradeoff for less annoying logs
@scheduler.task('cron', hour='0', minute='5', next_run_time=datetime.now(), name='Prepare expire tasks')
def prepare_expire_tasks_task():
    expiring_files = get_today_expiring_files()
    for expiring_file in expiring_files:
        add_expire_job(expiring_file['filename'], expiring_file['expire_date'])
