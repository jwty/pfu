from flask import Blueprint, current_app, request
from werkzeug.security import check_password_hash
from pfu.db import get_file_by_filename, delete_by_filename
from pfu.utils import prepare_file_details


api = Blueprint('api', __name__, url_prefix='/api')
error_404 = {'status': 'error', 'message': 'Not found'}
error_401 = {'status': 'error', 'message': 'Unauthorized'}
error_405 = {'status': 'error', 'message': 'Method not allowed'}


# TODO: These are a mess; serve different error when prefix is /api
@api.errorhandler(404)
def not_found(error):
    return error_404, 404


@api.errorhandler(405)
def method_not_allowed(error):
    return error_405, 405


@api.before_request
def before_request():
    api_secret = current_app.config['AUTH_SECRET']
    request_secret = request.headers.get('X-Auth-Secret')
    if not request_secret or not check_password_hash(api_secret, request_secret):
        return error_401, 401


@api.get('/file/<filename>')
def details(filename):
    file = get_file_by_filename(filename)
    if not file:
        return error_404, 404
    file_details = prepare_file_details(current_app, request, file)
    return {'status': 'success', 'data': file_details}


@api.delete('/file/<filename>')
def delete(filename):
    if not get_file_by_filename(filename):
        return error_404, 404
    try:
        delete_by_filename(filename)
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500
    return {'status': 'success', 'message': 'File deleted successfully'}
