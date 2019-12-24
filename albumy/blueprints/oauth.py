import os

from flask import flash, redirect, url_for, Blueprint, abort, request
from flask_login import login_user, current_user

from albumy.extensions import db, oauth
from albumy.models import User
import requests

oauth_bp = Blueprint('oauth', __name__)

github = oauth.remote_app(
    name='github',
    consumer_key=os.getenv('GITHUB_CLIENT_ID'),
    consumer_secret=os.getenv('GITHUB_CLIENT_SECRET'),
    request_token_params={'scope': 'user'},
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
)

providers = {'github': github}

def get_social_profile(provider, access_token):
    response = provider.get('user', token=access_token)

    username = response.data.get('name')
    website = response.data.get('blog')
    github = response.data.get('html_url')
    email = response.data.get('email')
    bio = response.data.get('bio')
    return username,  website, github, email, bio


@oauth_bp.route('/login/<provider_name>')
def oauth_login(provider_name):
    callback = url_for('.oauth_callback', provider_name=provider_name, _external=True)
    return providers[provider_name].authorize(callback=callback)


@oauth_bp.route('/callback/<provider_name>')
def oauth_callback(provider_name):
    provider  = providers[provider_name]
    response = provider.authorized_response()

    if response is not None:
        access_token = response.get('access_token')
    else:
        access_token = None

    if access_token is None:
        flash('Access denied, please try again.')
        return redirect(url_for('auth.login'))

    username, website, github, email, bio = get_social_profile(provider, access_token)

    user = User.query.filter_by(email=email).first()

    if user is None:
        user = User(email=email, nickname=username, github=github)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('main.index'))
    login_user(user, remember=True)
    return redirect(url_for('main.index'))
