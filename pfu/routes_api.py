import logging
from flask import Blueprint, request
from functools import wraps
from typing import Callable, Optional, TypedDict
from werkzeug.security import check_password_hash
from pfu.db import SecretDict, get_file_by_filename, get_secret, next_midnight
from pfu.responses import Status
from pfu.scheduler import add_expire_job, scheduler
from pfu.utils import recalculate_file, remove_file, save_file

api = Blueprint('api', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)


class ApiResponse(TypedDict, total=False):
    status: str
    message: str
    data: dict[str, object] | str


def permission_required(permission: str) -> Callable:
    def decorator(function: Callable) -> Callable:
        @wraps(function)
        def wrapper(*args, **kwargs):
            client_ip = request.remote_addr
            endpoint = f'{request.method} {request.path}'
            request_secret = request.headers.get('X-Auth-Secret')
            secret = validate_secret(request_secret)
            if not secret:
                logger.warning(f'Unauthorized, IP: {client_ip}, endpoint: {endpoint}')
                return {'status': Status.ERROR.value, 'message': 'Unauthorized'}, 401
            secret_name = secret.get('name')
            if not secret.get(f'perm_{permission}'):
                logger.info(f'Insufficient permissions, secret: {secret_name}, IP: {client_ip}, endpoint: {endpoint}')
                return {'status': Status.ERROR.value, 'message': 'Forbidden'}, 403
            logger.info(f'API access, secret: {secret_name}, IP: {client_ip}, endpoint: {endpoint}')
            return function(*args, **kwargs)
        return wrapper
    return decorator


def validate_secret(request_secret: Optional[str]) -> Optional[SecretDict]:
    if not request_secret:
        return None
    try:
        prefix, token = request_secret.split('-')
    except ValueError:
        return None
    secret = get_secret(prefix=prefix)
    if not secret or not check_password_hash(secret['hash'], token):
        return None
    return secret


@api.get('/file/<filename>')
@permission_required('read')
def details(filename: str) -> tuple[ApiResponse, int] | ApiResponse:
    file = get_file_by_filename(filename)
    if not file:
        return {'status': Status.ERROR.value, 'message': 'Not found'}, 404
    return {'status': Status.SUCCESS.value, 'data': dict(file)}


@api.delete('/file/<filename>')
@permission_required('delete')
def delete(filename: str) -> tuple[ApiResponse, int] | ApiResponse:
    if not get_file_by_filename(filename):
        return {'status': Status.ERROR.value, 'message': 'Not found'}, 404
    result = remove_file(filename)
    if result.is_error:
        return {'status': result.status.value, 'message': result.error_message or "Unknown error"}, 500
    if scheduler.get_job(filename):
        scheduler.remove_job(filename)
    return {'status': result.status.value, 'message': 'File deleted'}


@api.post('/upload')
@permission_required('write')
def upload() -> tuple[ApiResponse, int] | ApiResponse:
    file = request.files.get('file')
    if not file:
        return {'status': Status.ERROR.value, 'message': 'No file provided'}, 400
    keep_filename = 'keep_filename' in request.form
    expire_timestamp = request.form.get('expire', None, int)
    description = request.form.get('description', '')
    result = save_file(file, keep_filename, expire_timestamp, description)
    if result.is_error:
        return {'status': result.status.value, 'message': result.error_message or "Unknown error"}, 500
    if not isinstance(result.data, dict):
        return {'status': result.status.value, 'message': 'Unknown error'}, 500
    if result.is_success and expire_timestamp and expire_timestamp <= next_midnight() and isinstance(filename := result.data.get('filename'), str):
        add_expire_job(filename, expire_timestamp)
    return {'status': result.status.value, 'data': result.data}


@api.post('/recalculate/<filename>')
@permission_required('write')
def recalculate(filename: str) -> tuple[ApiResponse, int] | ApiResponse:
    if not get_file_by_filename(filename):
        return {'status': Status.ERROR.value, 'message': 'Not found'}, 404
    result = recalculate_file(filename)
    if result.is_error:
        return {'status': result.status.value, 'message': result.error_message or "Unknown error"}, 500
    file = get_file_by_filename(filename)
    if not file:
        return {'status': Status.ERROR.value, 'message': 'Not found after recalculating'}, 404
    return {'status': result.status.value, 'data': dict(file)}
