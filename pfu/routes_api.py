from flask import Blueprint, current_app, request
from werkzeug.security import check_password_hash
from pfu.db import get_file_by_filename, delete_by_filename
from pfu.utils import prepare_file_details, save_file


api = Blueprint('api', __name__, url_prefix='/api')


@api.before_request
def before_request():
    api_secret = current_app.config['AUTH_SECRET']
    request_secret = request.headers.get('X-Auth-Secret')
    if not request_secret or not check_password_hash(api_secret, request_secret):
        return {'status': 'error', 'message': 'Unauthorized'}, 401


@api.get('/file/<filename>')
def details(filename):
    file = get_file_by_filename(filename)
    if not file:
        return {'status': 'error', 'message': 'Not found'}, 404
    file_details = prepare_file_details(current_app, request, file)
    return {'status': 'success', 'data': file_details}


@api.delete('/file/<filename>')
def delete(filename):
    if not get_file_by_filename(filename):
        return {'status': 'error', 'message': 'Not found'}, 404
    try:
        delete_by_filename(filename)
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500
    return {'status': 'success'}
    

@api.post('/upload')
def upload():
    file = request.files.get('file')
    if not file:
        return {'status': 'error', 'message': 'No file provided'}, 400
    keep_filename = 'keep_filename' in request.form
    expire_timestamp = request.form.get('expire', None, int)
    description = request.form.get('description')
    status, file_data = save_file(file, keep_filename, expire_timestamp, description)
    return {'status': status, 'data': file_data}
