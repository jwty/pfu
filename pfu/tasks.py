import json
import logging
from datetime import datetime
from flask import current_app
from flask_apscheduler import APScheduler
from os import path
from pfu.db import get_files_count, get_files_expiring_count, get_files_size


scheduler = APScheduler()
# TODO: Consider using own logs instead of apscheduler logs
logging.getLogger('apscheduler').setLevel(logging.INFO)
# logger = logging.getLogger(__name__)


@scheduler.task('interval', hours=1)
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
