from flask_login import LoginManager, UserMixin
from pfu.config import config_class


login_manager = LoginManager()


class User(UserMixin):
    username = config_class.ADMIN_USERNAME
    password = config_class.ADMIN_PASSWORD
    def get_id(self):
        return self.username


@login_manager.user_loader
def load_user(user_id):
    return User()
