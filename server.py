#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import random
import string
import sqlite3
from hashlib import md5
from flask import Flask, render_template, request, send_from_directory, jsonify
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.config.from_pyfile('config.cfg')

def call_db(query):
    database = sqlite3.connect(app.config['DATABASE'])
    cursor = database.cursor()
    result = cursor.execute(query).fetchone()
    database.commit()
    database.close()
    return result

def write_to_db(original_filename, new_filename, checksum):
    query = 'INSERT INTO files (original_filename, new_filename, checksum) VALUES ("{}", "{}", "{}")'.format(original_filename, new_filename, checksum)
    call_db(query)

def calc_md5(file_up):
    md5_obj = md5()
    chunk_size = app.config['CHUNK_SIZE']
    file_buffer = file_up.read(chunk_size)
    while len(file_buffer) > 0:
        md5_obj.update(file_buffer)
        file_buffer = file_up.read(chunk_size)
    file_up.seek(0)
    return md5_obj.hexdigest()

def check_duplicate(checksum):
    query = 'SELECT * FROM files WHERE checksum="{}"'.format(checksum)
    result = call_db(query)
    return result

def get_file_by_checksum(checksum):
    query = 'SELECT * FROM files WHERE checksum="{}"'.format(checksum)
    filename = call_db(query)[2]
    return filename

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file_up = request.files['file_up']
    secret = request.form['secret']
    if check_password_hash(app.config['AUTH_SECRET'], secret):
        md5_sum = calc_md5(file_up)
        if check_duplicate(md5_sum):
            new_filename = get_file_by_checksum(md5_sum)
        else:
            ext = os.path.splitext(file_up.filename)[1]
            new_filename = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8)) + ext
            file_path = os.path.join(app.config['UPLOAD_DIR'], new_filename)
            file_up.save(file_path)
            write_to_db(file_up.filename, new_filename, md5_sum)
        if 'json' in request.args:
            return jsonify(response='ok', file=file_up.filename, url='{}{}'.format(request.url_root, new_filename))
        return '<title>Upload complete</title><i>%s</i> => <i><a href="/%s">%s</a></i>' % (file_up.filename, new_filename, new_filename)
    else:
        return jsonify(response='wrong_password')

@app.route('/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_DIR'], filename)

if __name__ == "__main__":
    app.run(host='0.0.0.0')