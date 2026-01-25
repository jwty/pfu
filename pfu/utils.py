import os
from datetime import datetime

class Messages:
    DELETE_CONFIRM = 'File <a href="{file_url}">{filename}</a> <a href="{details_url}">(details)</a> will be deleted. This action cannot be undone. Type in your secret key to confirm:'
    DETAILS_PROMPT = 'You need to provide the secret key to view details for file <a href="{file_url}">{filename}</a>.'


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
        'original_filename': file_data['original_filename'],
        'size': file_data['size'],
        'description': file_data['description'],
        'file_url': file_url,
        'checksum': file_data['checksum'],
        'upload_date': file_data['upload_date'],
        'expire_date': file_data['expire_date']
    }
    return file_details_dict
