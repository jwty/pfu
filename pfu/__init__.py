from flask import Flask
from flask_bootstrap import Bootstrap5

app = Flask(__name__)
bootstrap = Bootstrap5(app)

app.config.from_prefixed_env(prefix="PFU")
app.secret_key = app.config["SECRET_KEY"]

from pfu import routes, db

db.initialize_db()

# import subprocess
# __version__ = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).strip().decode()
# @app.context_processor
# def default_data():
#     return dict(version=__version__)
