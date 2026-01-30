from flask import Blueprint, request
from functools import wraps
from werkzeug.security import check_password_hash
from pfu.db import get_file_by_filename, get_secret
from pfu.responses import Status
from pfu.jobs import add_expire_job
from pfu.scheduler import scheduler, next_midnight
from pfu.utils import file_details_with_url, remove_file, save_file

api = Blueprint('api', __name__, url_prefix='/api')


def permission_required(permission):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            request_secret = request.headers.get('X-Auth-Secret')
            if not request_secret:
                return {'status': Status.ERROR.value, 'message': 'Unauthorized'}, 401
            try:
                prefix, token = request_secret.split('-')
            except ValueError:
                return {'status': Status.ERROR.value, 'message': 'Unauthorized'}, 401
            secret = get_secret(prefix)
            if not secret or not check_password_hash(secret['hash'], token):
                return {'status': Status.ERROR.value, 'message': 'Unauthorized'}, 401
            if not secret.get(f'perm_{permission}'):
                return {'status': Status.ERROR.value, 'message': 'Forbidden'}, 403
            return function(*args, **kwargs)
        return wrapper
    return decorator


@api.get('/file/<filename>')
@permission_required('read')
def details(filename):
    file = get_file_by_filename(filename)
    if not file:
        return {'status': Status.ERROR.value, 'message': 'Not found'}, 404
    file_details = file_details_with_url(file)
    return {'status': Status.SUCCESS.value, 'data': file_details}


@api.delete('/file/<filename>')
@permission_required('delete')
def delete(filename):
    if not get_file_by_filename(filename):
        return {'status': Status.ERROR.value, 'message': 'Not found'}, 404
    result = remove_file(filename)
    if result.is_error:
        return {'status': result.status.value, 'message': result.error}, 500
    if scheduler.get_job(filename):
        scheduler.remove_job(filename)
    return {'status': result.status.value, 'message': 'File deleted'}


@api.post('/upload')
@permission_required('write')
def upload():
    file = request.files.get('file')
    if not file:
        return {'status': Status.ERROR.value, 'message': 'No file provided'}, 400
    keep_filename = 'keep_filename' in request.form
    expire_timestamp = request.form.get('expire', None, int)
    description = request.form.get('description', '')
    result = save_file(file, keep_filename, expire_timestamp, description)
    if result.is_success and expire_timestamp and expire_timestamp <= next_midnight():
        add_expire_job(result.data.get('filename'), expire_timestamp)
    if result.is_error:
        return {'status': result.status.value, 'message': result.error}, 500
    return {'status': result.status.value, 'data': result.data}
