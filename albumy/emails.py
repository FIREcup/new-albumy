from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from .extensions import mail
from .extensions import celery


@celery.task
def _send_async_mail(app, message):
    with app.app_context():
        mail.send(message)


def send_mail(to, subject, template, **kwargs):
    message = Message(current_app.config['ALBUMY_MAIL_SUBJECT_PREFIX'] + subject, recipients=[to])
    message.body = render_template(template + '.txt', **kwargs)
    message.html = render_template(template + '.html', **kwargs)
    app = current_app._get_current_object()
    _send_async_mail(app, message)


def send_confirm_email(user, token, to=None):
    send_mail(subject='Albumy confirm', to=to or user.email, template='emails/confirm', user=user, token=token)


def send_reset_password_email(user, token):
    send_mail(subject='password reset', to=user.email, template='emails/reset_password', user=user, token=token)
