import os
import secrets
from datetime import datetime
from time import time
from flask import Blueprint, current_app, render_template, request, jsonify, url_for
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from pfu import db, utils


main = Blueprint('main', __name__)


def generate_response(json_requested, status, data):
    data = format_dates(data)
    if json_requested:
        return jsonify(status=status, data=data)
    else:
        return render_template('generic_response.html', status=status, data=data)


def format_dates(data):
    for key in ['upload_date', 'expire_date']:
        if key in data and isinstance(data[key], int):
            dt = datetime.fromtimestamp(data[key]).astimezone()
            data[key] = dt.strftime('%Y-%m-%d %H:%M:%S %Z')
    return data


def prepare_file_details(file_data):
    base_url = request.url_root
    file_prefix = current_app.config['FILE_URL_PREFIX']
    new_filename = file_data['new_filename']
    file_url = f'{base_url}{file_prefix}{new_filename}'
    delete_url = f'{base_url}delete/{new_filename}'
    details_url = f'{base_url}details/{new_filename}'
    file_details_dict = {
        'original_filename': file_data['original_filename'],
        'new_filename': new_filename,
        'file_size': file_data['size'],
        'description': file_data['description'],
        'file_url': file_url,
        'delete_url': delete_url,
        'details_url': details_url,
        'checksum': file_data['checksum'],
        'upload_date': file_data['upload_date'],
        'expire_date': file_data['expire_date']
    }
    return file_details_dict


@main.route('/')
def index():
    date_now = datetime.now().strftime("%Y-%m-%d")
    time_now = datetime.now().strftime("%H:%M")
    return render_template('index.html', default_date=date_now, default_time=time_now)


@main.route('/upload', methods=['POST'])
def upload_file():
    json_requested = 'json' in request.args
    file_up = request.files.get('file_up')
    secret = request.form.get('secret')
    description = request.form.get('description')
    if not secret or not check_password_hash(current_app.config['AUTH_SECRET'], secret):
        return generate_response(json_requested, 'error', {'message': 'unauthorised'}), 401
    if not file_up:
        return generate_response(json_requested, 'error', {'message': 'no file selected'}), 400
    md5_sum = db.calc_md5(file_up)
    # Simple duplicate avoidance - if the file already exists, do not duplicate it and instead return details for it
    if existing_file := db.get_file_by_checksum(md5_sum):
        return generate_response(json_requested, 'success', prepare_file_details(existing_file))
    expire_timestamp = None
    if 'expire' in request.form:
        expire_date = request.form.get('expire_date')
        expire_time = request.form.get('expire_time')
        if not expire_date or not expire_time:
            return generate_response(json_requested, 'error', {'message': 'expiration enabled but date/time missing'}), 400
        try:
            dt = datetime.strptime(f'{expire_date}{expire_time}', '%Y-%m-%d%H:%M')
            expire_timestamp = int(dt.timestamp())
        except ValueError:
            return generate_response(json_requested, 'error', {'message': 'invalid expiration date/time'}), 400
    filename = secure_filename(file_up.filename)
    filename_root, filename_ext = os.path.splitext(filename)
    new_filename_root = secrets.token_urlsafe(current_app.config['FILENAME_LENGTH'])
    if 'keep' in request.form:
        # Amend original filename to random token to avoid conflicts when uploading different files with same filenames
        new_filename = f'{filename_root}-{new_filename_root}{filename_ext}'
    else:
        new_filename = f'{new_filename_root}{filename_ext}'
    file_path = os.path.join(current_app.config['UPLOAD_DIR'], new_filename)
    try:
        file_up.save(file_path)
    except Exception as e:
        return generate_response(json_requested, 'error', {'message': f'unable to save file: {e}'}), 500
    file_size = os.stat(file_path).st_size
    db.add_file_to_db(new_filename, file_up.filename, description, md5_sum, int(time()), expire_timestamp, file_size)
    file_data = db.get_file_by_filename(new_filename)
    return generate_response(json_requested, 'success', prepare_file_details(file_data))


@main.route('/delete/<filename>', methods=['GET', 'POST'])
def delete_file(filename):
    json_requested = 'json' in request.args
    if request.method == 'GET':
        file_url = f'{request.url_root}{current_app.config['FILE_URL_PREFIX']}{filename}'
        details_url = url_for('main.file_details', filename=filename)
        message = utils.Messages.DELETE_CONFIRM.format(file_url=file_url, filename=filename, details_url=details_url)
        return render_template('prompt_secret.html',
                                title=f'Delete {filename}',
                                message=message,
                                action_url=url_for('main.delete_file', filename=filename),
                                button_text='Delete',
                                button_class='btn-danger')
    secret = request.form.get('secret')
    if not secret or not check_password_hash(current_app.config['AUTH_SECRET'], secret):
        return generate_response(json_requested, 'error', {'message': 'unauthorised'}), 401
    if not db.get_file_by_filename(filename):
        return generate_response(json_requested, 'error', {'message': 'no such file in db'}), 404
    try:
        db.delete_by_filename(filename)
    except Exception as e:
        return generate_response(json_requested, 'error', {'message': f'unable to delete file: {e}'}), 500
    return generate_response(json_requested, 'success', {'message': 'file deleted'})


@main.route('/details/<filename>', methods=['GET', 'POST'])
def file_details(filename):
    json_requested = 'json' in request.args
    if request.method == 'GET':
        file_url = f'{request.url_root}{current_app.config['FILE_URL_PREFIX']}{filename}'
        message = utils.Messages.DETAILS_PROMPT.format(file_url=file_url, filename=filename)
        return render_template('prompt_secret.html',
                                title='Secret required',
                                message=message,
                                action_url=url_for('main.file_details', filename=filename))
    secret = request.form.get('secret')
    if not secret or not check_password_hash(current_app.config['AUTH_SECRET'], secret):
        return generate_response(json_requested, 'error', {'message': 'unauthorised'}), 401
    file_data = db.get_file_by_filename(filename)
    if not file_data:
        return generate_response(json_requested, 'error', {'message': 'no such file in db'}), 404
    return generate_response(json_requested, 'details', prepare_file_details(file_data))
