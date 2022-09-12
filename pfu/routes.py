from pfu import app, db
from flask import render_template, request, jsonify
from datetime import datetime
from time import time
import secrets
import os
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from werkzeug import exceptions as werkzeug_exceptions


def generate_response(json_requested, status, data):
    if json_requested:
        return jsonify(status=status, data=data)
    else:
        return render_template('generic_response.html', status=status, data=data)


@app.route('/')
def index():
    date_now = datetime.now().strftime("%Y-%m-%d")
    time_now = datetime.now().strftime("%H:%M")
    return render_template('index.html', default_date=date_now, default_time=time_now)


@app.route('/upload', methods=['POST'])
def upload_file():
    json_requested = True if 'json' in request.args else False
    # TODO: Maximum length of description field
    description = request.form['description'] if 'description' in request.form else None
    try:
        file_up = request.files['file_up']
        secret = request.form['secret']
    except werkzeug_exceptions.BadRequestKeyError:
        return generate_response(json_requested, 'error', {'message': 'empty form'}), 400
    if not check_password_hash(app.config['AUTH_SECRET'], secret):
        return generate_response(json_requested, 'error', {'message': 'wrong secret'}), 401
    md5_sum = db.calc_md5(file_up)
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
            new_filename = '{}-{}{}'.format(filename_root, random_string, filename_ext)
        else:
            new_filename = random_string + filename_ext
        file_path = os.path.join(app.config['UPLOAD_DIR'], new_filename)
        file_up.save(file_path)
        db.add_file_to_db(file_up.filename, description, new_filename, int(time()), expire_date, md5_sum)
    file_url = '{}{}{}'.format(request.url_root, app.config['FILE_URL_PREFIX'], new_filename)
    delete_url = '{}delete/{}'.format(request.url_root, new_filename)
    message = {'file': file_up.filename, 'file_url': file_url, 'delete_url': delete_url, 'description': description}
    return generate_response(json_requested, 'success', message)


@app.route('/delete/<filename>', methods=['GET', 'POST'])
def delete_file(filename):
    json_requested = True if 'json' in request.args else False
    if db.get_file_by_filename(filename):
        if request.method == 'POST':
            try:
                secret = request.form['secret']
            except werkzeug_exceptions.BadRequestKeyError:
                return generate_response(json_requested, 'error', {'message': 'empty form'}), 400
            if not check_password_hash(app.config['AUTH_SECRET'], secret):
                return generate_response(json_requested, 'error', {'message': 'wrong secret'}), 401
            try:
                db.delete_by_filename(filename)
            except Exception as e:
                return generate_response(json_requested, 'error', {'message': 'couldnt delete file - {}'.format(e)}), 500
            return generate_response(json_requested, 'success', {'message': 'file deleted'})
        else:
            return render_template('delete.html', filename=filename)
    else:
        return generate_response(json_requested, 'error', {'message': 'no such file in db'}), 500


# TODO: this
# @app.route('/details/<filename>')
# def file_details(filename):
#     return


# TODO: and this
# @app.route('/admin')
# def admin():
#     return render_template('admin.html')
