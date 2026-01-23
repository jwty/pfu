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


def truncate_filename(filename, length=20, from_start=False):
    if len(filename) <= length:
        return filename
    end = '...'
    truncate_to = length - len(end)
    if from_start:
        return end + filename[-truncate_to:]
    else:
        return filename[:truncate_to] + end
