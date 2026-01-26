import os
from datetime import datetime
from secrets import token_urlsafe
from time import time
from flask import current_app, request
from werkzeug.utils import secure_filename
from pfu.db import add_file_to_db, calc_md5, get_file_by_checksum, get_file_by_filename


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
    add_file_to_db(new_filename, file.filename, description, md5_sum, int(time()), expire_timestamp, file_size)
    file_data = get_file_by_filename(new_filename)
    return 'success', prepare_file_details(current_app, request, file_data)
