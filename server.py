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

def calldb(query):
    database = sqlite3.connect(app.config['DATABASE'])
    cursor = database.cursor()
    result = cursor.execute(query).fetchone()
    database.commit()
    database.close()
    return result

def writetodb(originalfilename, newfilename, checksum):
    query = 'INSERT INTO files (originalfilename, newfilename, checksum) VALUES ("{}", "{}", "{}")'.format(originalfilename, newfilename, checksum)
    calldb(query)

def checkduplicate(checksum):
    query = 'SELECT * FROM files WHERE checksum="{}"'.format(checksum)
    result = calldb(query)
    if result is None:
        return False #file unique
    return True #duplicate

def getfilebychecksum(checksum):
    query = 'SELECT * FROM files WHERE checksum="{}"'.format(checksum)
    filename = calldb(query)[2]
    return filename

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file_up']
    secret = request.form['secret']
    if check_password_hash(app.config['AUTH_SECRET'], secret):
        md5s = md5(file.read()).hexdigest()
        file.seek(0)
        if  checkduplicate(md5s):
            newfilename = getfilebychecksum(md5s)
        else:
            ext = os.path.splitext(file.filename)[1]
            newfilename = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8)) + ext
            filepath = os.path.join(app.config['UPLOAD_DIR'], newfilename)
            file.save(filepath)
            writetodb(file.filename, newfilename, md5s)
        if 'json' in request.args:
            return jsonify(response='ok', file=file.filename, url='{}{}'.format(request.url_root, newfilename))
        return '<title>Upload complete</title><i>%s</i> => <i><a href="/%s">%s</a></i>' % (file.filename, newfilename, newfilename)
    else:
        return jsonify(response='wrong_password')

@app.route('/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_DIR'], filename)

if __name__ == "__main__":
    app.run(host='0.0.0.0')