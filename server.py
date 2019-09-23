#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import random
import string
import sqlite3
from datetime import datetime
from time import time
from hashlib import md5
from flask import Flask, render_template, request, send_from_directory, jsonify
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.config.from_pyfile('config.cfg')

def write_to_db(cursor, original_filename, new_filename, upload_date, expire_date, checksum):
    query = 'INSERT INTO files (original_filename, new_filename, upload_date, expire_date, checksum) VALUES (?, ?, ?, ?, ?)'
    cursor.execute(query, [original_filename, new_filename, upload_date, expire_date, checksum])

def get_file_by_checksum(cursor, checksum):
    query = 'SELECT * FROM files WHERE checksum=?'
    result = cursor.execute(query, [checksum]).fetchone()
    return result

def calc_md5(file_up):
    md5_obj = md5()
    chunk_size = app.config['CHUNK_SIZE']
    file_buffer = file_up.read(chunk_size)
    while file_buffer:
        md5_obj.update(file_buffer)
        file_buffer = file_up.read(chunk_size)
    file_up.seek(0)
    return md5_obj.hexdigest()

@app.route('/')
def index():
    default_date = datetime.now().strftime("%Y-%m-%d")
    default_time = datetime.now().strftime("%H:%M")
    return render_template('index.html', default_date=default_date, default_time=default_time)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        file_up = request.files['file_up']
        secret = request.form['secret']
    except:
        return jsonify(response='empty_form')
    if not check_password_hash(app.config['AUTH_SECRET'], secret):
        return jsonify(response='wrong_password')
    md5_sum = calc_md5(file_up)
    database = sqlite3.connect(app.config['DATABASE'])
    cursor = database.cursor()
    keep = 'keep' in request.form
    expire = 'expire' in request.form
    if expire:
        expire_date = request.form['expire_date']
        expire_time = request.form['expire_time']
        expire_date = int(datetime.strptime(expire_date+expire_time, '%Y-%m-%d%H:%M').strftime('%s'))
    else:
        expire_date = None
    if get_file_by_checksum(cursor, md5_sum):
        new_filename = get_file_by_checksum(cursor, md5_sum)[2]
    else:
        ext = os.path.splitext(file_up.filename)[1]
        random_string = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
        new_filename = '{}-{}{}'.format(os.path.splitext(file_up.filename)[0], random_string, ext) if keep else random_string + ext
        file_path = os.path.join(app.config['UPLOAD_DIR'], new_filename)
        file_up.save(file_path)
        write_to_db(cursor, file_up.filename, new_filename, int(time()), expire_date, md5_sum)
    database.commit()
    database.close()
    if 'json' in request.args:
        return jsonify(response='ok', file=file_up.filename, url='{}{}'.format(request.url_root, new_filename))
    return '<title>Upload complete</title><i>%s</i> => <i><a href="/%s">%s</a></i>' % (file_up.filename, new_filename, new_filename)

@app.route('/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_DIR'], filename)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
