from datetime import datetime

class Messages:
    DELETE_CONFIRM = 'File <a href="{file_url}">{filename}</a> <a href="{details_url}">(details)</a> will be deleted. This action cannot be undone. Type in your secret key to confirm:'
    DETAILS_PROMPT = 'You need to provide the secret key to view details for file <a href="{file_url}">{filename}</a>.'


def format_datetime(timestamp):
    if not isinstance(timestamp, int):
        return timestamp
    dt = datetime.fromtimestamp(timestamp).astimezone()
    return dt.strftime('%Y-%m-%d %H:%M:%S %Z')