import os
import secrets
from datetime import datetime
from time import time
from flask import Blueprint, current_app, render_template, request, jsonify, url_for
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from werkzeug import exceptions as werkzeug_exceptions
from pfu import db, utils


# TODO: Organize views into blueprints
bp = Blueprint('main', __name__)


def generate_response(json_requested, status, data):
    if json_requested:
        return jsonify(status=status, data=data)
    else:
        return render_template('generic_response.html', status=status, data=data)


def prepare_file_details(file_data):
    base_url = request.url_root
    file_prefix = current_app.config['FILE_URL_PREFIX']
    new_filename = file_data['new_filename']
    file_url = f'{base_url}{file_prefix}{new_filename}'
    delete_url = f'{base_url}delete/{new_filename}'
    details_url = f'{base_url}details/{new_filename}'
    file_details = {
        'original_filename': file_data['original_filename'],
        'new_filename': new_filename,
        'file_url': file_url,
        'delete_url': delete_url,
        'details_url': details_url,
        'checksum': file_data['checksum'],
        # TODO: Handle multi-line descriptions
        'description': file_data['description'],
        'upload_date': file_data['upload_date'],
        'expire_date': file_data['expire_date']
    }
    return file_details


@bp.route('/')
def index():
    date_now = datetime.now().strftime("%Y-%m-%d")
    time_now = datetime.now().strftime("%H:%M")
    return render_template('index.html', default_date=date_now, default_time=time_now)


@bp.route('/upload', methods=['POST'])
def upload_file():
    json_requested = True if 'json' in request.args else False
    # TODO: Maximum length of description field
    description = request.form['description'] if 'description' in request.form else None
    try:
        file_up = request.files['file_up']
        secret = request.form['secret']
    except werkzeug_exceptions.BadRequestKeyError:
        return generate_response(json_requested, 'error', {'message': 'empty form'}), 400
    if not check_password_hash(current_app.config['AUTH_SECRET'], secret):
        return generate_response(json_requested, 'error', {'message': 'wrong secret'}), 401
    md5_sum = db.calc_md5(current_app, file_up)
    # TODO: Handle Bad Request error when submitting a form with 'expire' enabled and empty 'expire_date', 'expire_time'
    if 'expire' in request.form:
        expire_date = request.form['expire_date']
        expire_time = request.form['expire_time']
        expire_date = int(datetime.strptime(expire_date + expire_time, '%Y-%m-%d%H:%M').strftime('%s'))
    else:
        expire_date = None
    if existing_file := db.get_file_by_checksum(md5_sum):
        # If the file already exists, do not duplicate it and instead return URLs for already existing file
        new_filename = existing_file['new_filename']
    else:
        filename = secure_filename(file_up.filename)
        filename_root = os.path.splitext(filename)[0]
        filename_ext = os.path.splitext(filename)[1]
        random_string = secrets.token_urlsafe(5)
        if 'keep' in request.form:
            new_filename = f'{filename_root}-{random_string}{filename_ext}'
        else:
            new_filename = random_string + filename_ext
        file_path = os.path.join(current_app.config['UPLOAD_DIR'], new_filename)
        file_up.save(file_path)
        db.add_file_to_db(file_up.filename, description, new_filename, int(time()), expire_date, md5_sum)
    # If the file already exists, reuse the already fetched data
    file_data = existing_file or db.get_file_by_filename(new_filename)
    return generate_response(json_requested, 'success', prepare_file_details(file_data))


@bp.route('/delete/<filename>', methods=['GET', 'POST'])
def delete_file(filename):
    json_requested = True if 'json' in request.args else False
    if db.get_file_by_filename(filename):
        if request.method == 'POST':
            try:
                secret = request.form['secret']
            except werkzeug_exceptions.BadRequestKeyError:
                return generate_response(json_requested, 'error', {'message': 'empty form'}), 400
            if not check_password_hash(current_app.config['AUTH_SECRET'], secret):
                return generate_response(json_requested, 'error', {'message': 'wrong secret'}), 401
            try:
                db.delete_by_filename(current_app, filename)
            except Exception as e:
                return generate_response(json_requested, 'error', {'message': f'couldnt delete file - {e}'}), 500
            return generate_response(json_requested, 'success', {'message': 'file deleted'})
        else:
            file_url = f'{request.url_root}{current_app.config['FILE_URL_PREFIX']}{filename}'
            details_url = url_for('mail.file_details', filename=filename)
            message = utils.Messages.DELETE_CONFIRM.format(file_url=file_url, filename=filename, details_url=details_url)
            return render_template('prompt_secret.html',
                                    title=f"Delete {filename}",
                                    message=message,
                                    action_url=url_for('main.delete_file', filename=filename),
                                    button_text="Delete",
                                    button_class="btn-danger")
    else:
        return generate_response(json_requested, 'error', {'message': 'no such file in db'}), 500


@bp.route('/details/<filename>', methods=['GET', 'POST'])
def file_details(filename):
    json_requested = True if 'json' in request.args else False
    secret = request.form.get('secret')
    # If no secret provided and no json requested render the entry form
    if not secret and not json_requested:
        file_url = f'{request.url_root}{current_app.config['FILE_URL_PREFIX']}{filename}'
        message = utils.Messages.DETAILS_PROMPT.format(file_url=file_url, filename=filename)
        return render_template('prompt_secret.html',
                                title="Secret required",
                                message=message,
                                action_url=url_for('main.file_details', filename=filename),
                                json_requested=json_requested)
    if not secret or not check_password_hash(current_app.config['AUTH_SECRET'], secret):
        return generate_response(json_requested, 'error', {'message': 'unaothorized (wrong/no secret provided)'}), 401
    file_data = db.get_file_by_filename(filename)
    if not file_data:
        return generate_response(json_requested, 'error', {'message': 'no such file in db'}), 404
    return generate_response(json_requested, 'success', prepare_file_details(file_data))


# TODO: and this
# @bp.route('/admin')
# def admin():
#     return render_template('admin.html')
