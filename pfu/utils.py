import os
import json
from datetime import datetime
from hashlib import md5
from secrets import token_urlsafe
from flask import current_app, request
from werkzeug.utils import secure_filename
from pfu.db import add_file_to_db, get_file_by_checksum, get_file_by_filename, get_files_count, get_files_expiring_count, get_files_size
from pfu.scheduler import next_midnight
from pfu.jobs import add_expire_job


def calc_md5(file_up):
    md5_obj = md5()
    chunk_size = current_app.config['CHUNK_SIZE']
    file_buffer = file_up.read(chunk_size)
    while file_buffer:
        md5_obj.update(file_buffer)
        file_buffer = file_up.read(chunk_size)
    file_up.seek(0)
    return md5_obj.hexdigest()


def format_datetime(timestamp):
    if not isinstance(timestamp, int):
        return timestamp
    dt = datetime.fromtimestamp(timestamp).astimezone()
    return dt.strftime('%Y-%m-%d %H:%M:%S %Z')


def prepare_file_details(current_app, request, file_data):
    base_url = request.url_root
    file_prefix = current_app.config['FILE_URL_PREFIX']
    file_url = f'{base_url}{file_prefix}{file_data['filename']}'
    file_details_dict = {
        'filename': file_data['filename'],
        'original_filename': file_data['original_filename'],
        'size': file_data['size'],
        'description': file_data['description'],
        'file_url': file_url,
        'checksum': file_data['checksum'],
        'upload_date': file_data['upload_date'],
        'expire_date': file_data['expire_date']
    }
    return file_details_dict


def save_file(file, keep_filename=False, expire_timestamp=None, description=None):
    md5_sum = calc_md5(file)
    # Simple duplicate avoidance - if the file already exists, do not duplicate and instead return it
    if existing_file := get_file_by_checksum(md5_sum):
        return 'file_exists', prepare_file_details(current_app, request, existing_file)
    filename = secure_filename(file.filename)
    filename_root, filename_ext = os.path.splitext(filename)
    new_filename_root = token_urlsafe(current_app.config['FILENAME_LENGTH'])
    if keep_filename:
        # Amend original filename to random token to avoid conflicts when uploading different files with same filenames
        new_filename = f'{filename_root}-{new_filename_root}{filename_ext}'
    else:
        new_filename = f'{new_filename_root}{filename_ext}'
    file_path = os.path.join(current_app.config['UPLOAD_DIR'], new_filename)
    try:
        file.save(file_path)
    except Exception as e:
        return 'error', str(e)
    file_size = os.stat(file_path).st_size
    add_file_to_db(new_filename, file.filename, description, md5_sum, int(datetime.now().timestamp()), expire_timestamp, file_size)
    if expire_timestamp and expire_timestamp <= next_midnight():
        add_expire_job(new_filename, expire_timestamp)
    file_data = get_file_by_filename(new_filename)
    return 'success', prepare_file_details(current_app, request, file_data)


def get_stats():
    stats_file = os.path.join(current_app.config['DATA_DIR'], 'stats.json')
    with open(stats_file, 'r') as f:
        stats = json.load(f)
    stats['last_updated'] = datetime.fromtimestamp(stats['last_updated']).astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')
    return stats


def update_stats():
    stats_file = os.path.join(current_app.config['DATA_DIR'], 'stats.json')
    stats = {
        'files_count': get_files_count(),
        'files_expiring_count': get_files_expiring_count(),
        'files_size': get_files_size(),
        'last_updated': int(datetime.now().timestamp())
    }
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=4)
