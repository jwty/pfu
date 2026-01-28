import os
import secrets
from flask_login import LoginManager, UserMixin
from pfu.config import config_class


login_manager = LoginManager()
token_path = os.path.join(config_class.DATA_DIR, '.session_token')


def load_session_token():
    try:
        with open(token_path, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return new_session_token()


def new_session_token():
    token = secrets.token_urlsafe(32)
    with open(token_path, 'w') as f:
        f.write(token)
    return token


class User(UserMixin):
    username = config_class.ADMIN_USERNAME
    password = config_class.ADMIN_PASSWORD
    def get_id(self):
        # Include session token in user ID so changing it invalidates all sessions
        session_token = load_session_token()
        return f"{self.username}:{session_token}"


@login_manager.user_loader
def load_user(user_id):
    try:
        username, token = user_id.split(':', 1)
        current_token = load_session_token()
        if token == current_token and username == config_class.ADMIN_USERNAME:
            return User()
    except ValueError:
        pass
    return None
