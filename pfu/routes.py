import os
import secrets
from datetime import datetime
from time import time
from flask import Blueprint, current_app, render_template, request, jsonify, url_for, flash, redirect
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from pfu import db, utils


main = Blueprint('main', __name__)


def generate_response(json_requested, status, data, redirect_url=None, include_flash=True):
    if json_requested:
        return jsonify(status=status, data=data)
    if include_flash:
        default_msg = 'Operation completed successfully.' if status == 'success' else 'An error occurred during the operation.'
        flash(data.get('message', default_msg), status)
    # If we have detailed data (new upload or file details), show the generic_response page
    if (status == 'success' and 'new_filename' in data) or status == 'details':
        return render_template('generic_response.html', status=status, data=data)
    return redirect(redirect_url or url_for('main.index'))


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
        new_filename = f'{filename_root}-{new_filename_root}{filename_ext}'
    else:
        new_filename = f'{new_filename_root}{filename_ext}'
    file_path = os.path.join(current_app.config['UPLOAD_DIR'], new_filename)
    try:
        file_up.save(file_path)
    except Exception as e:
        return generate_response(json_requested, 'error', {'message': f'Unable to save file: {e}'})
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
        return generate_response(json_requested, 'error', {'message': 'Unauthorised'}, redirect_url=request.url)
    if not db.get_file_by_filename(filename):
        return generate_response(json_requested, 'error', {'message': f'File {filename} not found.'})
    try:
        db.delete_by_filename(filename)
    except Exception as e:
        return generate_response(json_requested, 'error', {'message': f'Unable to delete file: {e}'})
    return generate_response(json_requested, 'success', {'message': 'File deleted successfully'})


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
        return generate_response(json_requested, 'error', {'message': 'Unauthorised'}, redirect_url=request.url)
    file_data = db.get_file_by_filename(filename)
    if not file_data:
        return generate_response(json_requested, 'error', {'message': f'File {filename} not found.'})
    # No flash message for file details
    return generate_response(json_requested, 'details', prepare_file_details(file_data), include_flash=False)
