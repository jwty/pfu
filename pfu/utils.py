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


def truncate_filename(filename, length=20):
    if len(filename) <= length:
        return filename
    end = '(...)'
    filename_root, filename_ext = os.path.splitext(filename)
    truncate_to = length - len(filename_ext) - len(end)
    # If the extension is longer than length, or no space for root, truncate whole string (should be rare)
    if truncate_to <= 0 or len(filename_ext) >= length:
        return filename[:length-len(end)] + end
    return filename_root[:truncate_to] + end + filename_ext
