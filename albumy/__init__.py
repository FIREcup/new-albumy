from __future__ import absolute_import
import os
import click
from flask import Flask, render_template

from .blueprints.main import main_bp
from .blueprints.auth import auth_bp
from .blueprints.user import user_bp
from .blueprints.ajax import ajax_bp
from .blueprints.oauth import oauth_bp
from .blueprints.admin import admin_bp
from .extensions import bootstrap, db, mail, moment, login_manager, dropzone, csrf, avatars
from .extensions import whooshee, migrate, oauth
from .settings import config
from .models import User, Role, Notification
from flask_login import current_user


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')

    app = Flask('albumy')

    app.config.from_object(config[config_name])
    app.app_context().push()

    register_extensions(app)
    register_blueprints(app)
    register_commands(app)
    register_errorhandler(app)
    register_shell_context(app)
    register_template_context(app)

    return app



def register_extensions(app):
    bootstrap.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    dropzone.init_app(app)
    csrf.init_app(app)
    avatars.init_app(app)
    whooshee.init_app(app)
    migrate.init_app(app)
    oauth.init_app(app)


def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(ajax_bp, url_prefix='/ajax')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(oauth_bp)


def register_shell_context(app):
    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db, User=User)


def register_template_context(app):
    @app.context_processor
    def make_template_context():
        if current_user.is_authenticated:
            notification_count = Notification.query.with_parent(current_user).filter_by(is_read=False).count()
        else:
            notification_count = None
        return dict(notification_count=notification_count)


def register_errorhandler(app):
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return render_template('error/413.html'), 413

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500


def register_commands(app):
    @app.cli.command()
    @click.option('--drop', is_flag=True, help='Create after drop')
    def initdb(drop):
        """Initialize Database"""
        if drop:
            click.confirm('This operation will delete the database, continue?', abort=True)
            db.drop_all()
            click.echo('Drop tables.')
        db.create_all()
        click.echo('Initialized databases.')

    @app.cli.command()
    def init():
        """Initialize Albumy"""
        click.echo('Initializing the database...')
        db.create_all()

        click.echo('Initializing the roles and permissions...')
        Role.init_role()

        click.echo('Done.')

    @app.cli.command()
    def forge():
        """Generate fake data"""
        pass
