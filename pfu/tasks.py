import json
import logging
from datetime import datetime
from flask import current_app
from os import path
from pfu.db import add_expire_job, get_files_count, get_files_expiring_count, get_files_size, get_today_expiring_files
from pfu.scheduler import scheduler


# TODO: Consider using own logs instead of apscheduler logs
# logger = logging.getLogger(__name__)
logging.getLogger('apscheduler').setLevel(logging.INFO)


@scheduler.task('interval', hours=1, name='Update stats')
def update_stats():
    with scheduler.app.app_context():
        stats_file = path.join(current_app.config['DATA_DIR'], 'stats.json')
        stats = {
            'files_count': get_files_count(),
            'files_expiring_count': get_files_expiring_count(),
            'files_size': get_files_size(),
            'last_updated': int(datetime.now().timestamp())
        }
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=4)


@scheduler.task('cron', hour=0, next_run_time=datetime.now(), name='Prepare expire tasks')
def prepare_expire_tasks():
    expiring_files = get_today_expiring_files()
    for expiring_file in expiring_files:
        add_expire_job(expiring_file['filename'], expiring_file['expire_date'])
