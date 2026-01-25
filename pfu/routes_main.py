import os
import secrets
from datetime import datetime
from time import time
from flask import Blueprint, current_app, render_template, request, jsonify, url_for, flash, redirect
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from pfu import db


main = Blueprint('main', __name__)


def generate_response(json_requested, status, data, redirect_url=None, include_flash=True):
    if json_requested:
        return jsonify(status=status, data=data)
    if include_flash:
        default_msg = 'Operation completed successfully.' if status == 'success' else 'An error occurred during the operation.'
        flash(data.get('message', default_msg), status)
    # If we have detailed data (new upload or file details), show the generic_response page
    if (status == 'success' and 'filename' in data) or status == 'details':
        return render_template('generic_response.html', status=status, data=data)
    return redirect(redirect_url or url_for('main.index'))


def prepare_file_details(file_data):
    base_url = request.url_root
    file_prefix = current_app.config['FILE_URL_PREFIX']
    filename = file_data['filename']
    file_url = f'{base_url}{file_prefix}{filename}'
    delete_url = f'{base_url}delete/{filename}'
    details_url = f'{base_url}details/{filename}'
    file_details_dict = {
        'original_filename': file_data['original_filename'],
        'filename': filename,
        'size': file_data['size'],
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
        return generate_response(json_requested, 'error', {'message': 'Unauthorised'})
    if not file_up:
        return generate_response(json_requested, 'error', {'message': 'No file selected'})
    md5_sum = db.calc_md5(file_up)
    # Simple duplicate avoidance - if the file already exists, do not duplicate it and instead return details for it
    if existing_file := db.get_file_by_checksum(md5_sum):
        return generate_response(json_requested, 'success', prepare_file_details(existing_file))
    expire_timestamp = None
    if 'expire' in request.form:
        expire_date = request.form.get('expire_date')
        expire_time = request.form.get('expire_time')
        if not expire_date or not expire_time:
            return generate_response(json_requested, 'error', {'message': 'Expiration enabled but date/time missing'})
        try:
            dt = datetime.strptime(f'{expire_date}{expire_time}', '%Y-%m-%d%H:%M')
            expire_timestamp = int(dt.timestamp())
        except ValueError:
            return generate_response(json_requested, 'error', {'message': 'Invalid expiration date/time'})
    filename = secure_filename(file_up.filename)
    filename_root, filename_ext = os.path.splitext(filename)
    new_filename_root = secrets.token_urlsafe(current_app.config['FILENAME_LENGTH'])
    if 'keep' in request.form:
        # Amend original filename to random token to avoid conflicts when uploading different files with same filenames
        filename = f'{filename_root}-{new_filename_root}{filename_ext}'
    else:
        filename = f'{new_filename_root}{filename_ext}'
    file_path = os.path.join(current_app.config['UPLOAD_DIR'], filename)
    try:
        file_up.save(file_path)
    except Exception as e:
        return generate_response(json_requested, 'error', {'message': f'Unable to save file: {e}'})
    file_size = os.stat(file_path).st_size
    db.add_file_to_db(filename, file_up.filename, description, md5_sum, int(time()), expire_timestamp, file_size)
    file_data = db.get_file_by_filename(filename)
    return generate_response(json_requested, 'success', prepare_file_details(file_data))
