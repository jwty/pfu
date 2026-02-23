import logging
import os
import json
from datetime import datetime
from hashlib import md5
from secrets import token_urlsafe
from werkzeug.utils import secure_filename
from pfu.db import add_file_to_db, delete_file_record, get_all_file_sizes, get_file_by_checksum, get_file_by_filename, get_files_count, get_files_expiring_count, get_files_size, update_file_checksum_and_size
from pfu.config import config
from pfu.responses import Result

logger = logging.getLogger(__name__)


def clear_anomaly(filename):
    anomalies_file = os.path.join(config.DATA_DIR, 'anomalies.json')
    if not os.path.exists(anomalies_file):
        return
    try:
        with open(anomalies_file, 'r') as f:
            anomalies = json.load(f)
        if filename in anomalies:
            del anomalies[filename]
            with open(anomalies_file, 'w') as f:
                json.dump(anomalies, f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to clear anomaly for {filename}: {e}")


def calc_md5(file_up):
    md5_obj = md5()
    chunk_size = config.CHUNK_SIZE
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


def parse_expire_datetime(expire_date, expire_time='00:00'):
    if not expire_date:
        return None
    return datetime.combine(datetime.strptime(expire_date, '%Y-%m-%d'), datetime.strptime(expire_time, '%H:%M').time()).timestamp()


def file_details_with_url(file_data):
    return {**file_data, 'file_url': f"{config.FILE_URL_PREFIX}{file_data['filename']}"}


def save_file(file, keep_filename=False, expire_timestamp=None, description=None):
    md5_sum = calc_md5(file)
    # Simple duplicate avoidance if the file already exists, do not duplicate and instead return it
    if existing_file := get_file_by_checksum(md5_sum):
        return Result.file_exists(data=file_details_with_url(existing_file))
    filename = secure_filename(file.filename)
    filename_root, filename_ext = os.path.splitext(filename)
    new_filename_root = token_urlsafe(config.FILENAME_LENGTH)
    if keep_filename:
        # Amend original filename to random token to avoid conflicts when uploading different files with same filenames
        new_filename = f'{filename_root}-{new_filename_root}{filename_ext}'
    else:
        new_filename = f'{new_filename_root}{filename_ext}'
    file_path = os.path.join(config.UPLOAD_DIR, new_filename)
    try:
        file.save(file_path)
    except (IOError, OSError, PermissionError) as e:
        logger.error(f'Failed to save file {new_filename}: {str(e)}')
        return Result.error(f'Failed to save file {new_filename}: {str(e)}')
    file_size = os.stat(file_path).st_size
    add_file_to_db(new_filename, file.filename, description, md5_sum, int(datetime.now().timestamp()), expire_timestamp, file_size)
    file_data = get_file_by_filename(new_filename)
    logger.info(f'File saved: {new_filename} ({file_size} bytes)')
    return Result.success(file_details_with_url(file_data))


def recalculate_file(filename):
    file_path = os.path.join(config.UPLOAD_DIR, filename)
    try:
        file_size = os.stat(file_path).st_size
        with open(file_path, 'rb') as f:
            md5_sum = calc_md5(f)
    except FileNotFoundError:
        return Result.error(f'File {filename} not found on disk')
    except (IOError, OSError, PermissionError) as e:
        logger.error(f'Failed to read file {filename}: {str(e)}')
        return Result.error(f'Failed to read file {filename}: {str(e)}')
    result = update_file_checksum_and_size(filename, md5_sum, file_size)
    if result.is_success:
        logger.info(f'File recalculated: {filename} ({file_size} bytes, {md5_sum})')
        clear_anomaly(filename)
    return result


def remove_file(filename):
    file_path = os.path.join(config.UPLOAD_DIR, filename)
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass  # File already deleted, that's fine
    except (IOError, OSError, PermissionError) as e:
        logger.error(f'Failed to remove file {filename}: {str(e)}')
        return Result.error(f'Failed to remove file {filename}: {str(e)}')
    try:
        delete_file_record(filename)
    except Exception as e:
        # Generic since it should only catch database errors
        logger.error(f'Failed to delete database record for {filename}: {str(e)}')
        return Result.error(f'Failed to delete database record for file {filename}: {str(e)}')
    logger.info(f'File removed: {filename}')
    clear_anomaly(filename)
    return Result.success()


def get_stats():
    stats_file = os.path.join(config.DATA_DIR, 'stats.json')
    # Create stats file if it doesn't exist
    if not os.path.exists(stats_file):
        update_stats()
    with open(stats_file, 'r') as f:
        stats = json.load(f)
    stats['last_updated'] = datetime.fromtimestamp(stats['last_updated']).astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')
    return stats


def update_stats():
    stats_file = os.path.join(config.DATA_DIR, 'stats.json')
    stats = {
        'files_count': get_files_count(),
        'files_expiring_count': get_files_expiring_count(),
        'files_size': get_files_size(),
        'last_updated': int(datetime.now().timestamp())
    }
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=4)


def integrity_check():
    logger.info("Starting integrity check...")
    anomalies = {}
    files = get_all_file_sizes()
    for file in files:
        filename = file['filename']
        expected_size = file['size']
        file_path = os.path.join(config.UPLOAD_DIR, filename)
        try:
            actual_size = os.stat(file_path).st_size
            if actual_size != expected_size:
                logger.warning(f"INTEGRITY ANOMALY: {filename} expected {expected_size} bytes, found {actual_size} bytes on disk.")
                anomalies[filename] = {'type': 'size', 'expected': expected_size, 'actual': actual_size}
        except FileNotFoundError:
            logger.warning(f"INTEGRITY ANOMALY: {filename} exists in database but is completely missing from disk.")
            anomalies[filename] = {'type': 'missing'}
        except OSError as e:
            logger.error(f"Failed to stat file {filename} during integrity check: {e}")
    anomalies_file = os.path.join(config.DATA_DIR, 'anomalies.json')
    try:
        with open(anomalies_file, 'w') as f:
            json.dump(anomalies, f)
    except OSError as e:
        logger.error(f"Failed to write anomalies file: {e}")
    logger.info(f"Integrity check complete. Found {len(anomalies)} anomalies.")
