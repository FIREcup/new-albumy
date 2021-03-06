import os
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_login import AnonymousUserMixin
from flask_dropzone import Dropzone
from flask_wtf import CSRFProtect
from flask_avatars import Avatars
from flask_whooshee import Whooshee
from flask_migrate import Migrate
from flask_oauthlib.client import OAuth


bootstrap = Bootstrap()
db = SQLAlchemy()
mail = Mail()
moment = Moment()
login_manager = LoginManager()
dropzone = Dropzone()
csrf = CSRFProtect()
avatars = Avatars()
whooshee = Whooshee()
migrate = Migrate(db)
oauth = OAuth()


@login_manager.user_loader
def load_user(user_id):
    from .models import User
    user = User.query.get(int(user_id))
    return user


login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'


class Guest(AnonymousUserMixin):

    def can(self, permission_name):
        return False

    @property
    def is_admin(self):
        return False


login_manager.anonymous_user = Guest
