import os

from flask import flash, redirect, url_for, Blueprint, abort, request
from flask_login import login_user, current_user

from albumy.extensions import db, oauth
from albumy.models import User
import requests

oauth_bp = Blueprint('oauth', __name__)

oauth.register(
    name='github',
    client_id=os.getenv('GITHUB_CLIENT_ID'),
    client_secret=os.getenv('GITHUB_CLIENT_SECRET'),
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    api_base_url='https://api.github.com/',
    client_kwargs="profile"
)

github = oauth.github

@oauth_bp.route('/login/github')
def oauth_login():
    redirect_url = url_for('.oauth_callback', _external=True)
    return github.authorize_redirect(request, redirect_url)

@oauth_bp.route('/callback/github')
def oauth_callback():
    token = oauth.github.authorize_access_token(request)
    print(token)
    resp = oauth.github.get('profile')
    profile = resp.json()
    print(profile)
    return profile
