#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sqlite3
from getpass import getpass
from werkzeug.security import generate_password_hash

uploaddir = str(input('Upload dir (default: uploads): ') or 'uploads')
try:
    os.makedirs(uploaddir, exist_ok=True)
except:
    raise

dbname = str(input('Db file name (default: database.db): ') or 'database.db')
if os.path.exists(dbname):
    raise Exception('{} already present'.format(dbname))
database = sqlite3.connect(dbname)
cursor = database.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY, originalfilename TEXT, newfilename TEXT, checksum TEXT)')
database.commit()
database.close()

secrethash = generate_password_hash(str(getpass('Secret key (default: secret): ')) or 'secret')

print('Writing config to config.cfg')
if os.path.exists('config.cfg'):
    raise Exception('config.cfg already present')
with open('config.cfg', 'a') as cfg:
    cfg.write('DATABASE="{}"'.format(dbname))
    cfg.write('\nUPLOAD_DIR="{}"'.format(uploaddir))
    cfg.write('\nAUTH_SECRET="{}"'.format(secrethash))
    cfg.write('\n')