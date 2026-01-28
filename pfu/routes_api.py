from flask import Blueprint, current_app, request
from functools import wraps
from werkzeug.security import check_password_hash
from pfu.db import add_expire_job,get_file_by_filename, get_secret, delete_by_filename
from pfu.utils import prepare_file_details, save_file
from pfu.scheduler import next_midnight


api = Blueprint('api', __name__, url_prefix='/api')


def permission_required(permission):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            request_secret = request.headers.get('X-Auth-Secret')
            if not request_secret:
                return {'status': 'error', 'message': 'Unauthorized'}, 401
            try:
                prefix, token = request_secret.split('-')
            except ValueError:
                return {'status': 'error', 'message': 'Unauthorized'}, 401
            secret = get_secret(prefix)
            if not secret or not check_password_hash(secret['hash'], token):
                return {'status': 'error', 'message': 'Unauthorized'}, 401
            if not secret.get(f'perm_{permission}'):
                return {'status': 'error', 'message': 'Forbidden'}, 403
            return function(*args, **kwargs)
        return wrapper
    return decorator


@api.get('/file/<filename>')
@permission_required('read')
def details(filename):
    file = get_file_by_filename(filename)
    if not file:
        return {'status': 'error', 'message': 'Not found'}, 404
    file_details = prepare_file_details(current_app, request, file)
    return {'status': 'success', 'data': file_details}


@api.delete('/file/<filename>')
@permission_required('delete')
def delete(filename):
    if not get_file_by_filename(filename):
        return {'status': 'error', 'message': 'Not found'}, 404
    try:
        delete_by_filename(filename)
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500
    return {'status': 'success'}


@api.post('/upload')
@permission_required('write')
def upload():
    file = request.files.get('file')
    if not file:
        return {'status': 'error', 'message': 'No file provided'}, 400
    keep_filename = 'keep_filename' in request.form
    expire_timestamp = request.form.get('expire', None, int)
    description = request.form.get('description')
    status, response = save_file(file, keep_filename, expire_timestamp, description)
    return {'status': status, 'data': response}
