from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth
from . import api
from .errors import forbidden, unauthorized
from ..models import User

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(email_or_token, password):

    # If an empty string has been passed return False (anonymous user)
    if email_or_token == '':
        return False

    # Try to verify user using token if password is empty
    if password == '':
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used = True
        return g.current_user is not None

    # Try to verify user by password if email_or_token and password is not empty
    user = User.query.filter_by(email=email_or_token).first()
    if not user:
        return False
    g.current_user = user
    g.token_used = False
    return user.verify_password(password)


@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


@api.before_request
@auth.login_required
def before_request():
    if g.current_user.is_anonymous:
        return forbidden('Unconfirmed account')


@api.route('/tokens/', methods=['POST'])
def get_token():
    """Create a new auth token for confirmed user"""
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('Invalid credentials')

    return jsonify({
        'token': g.current_user.generate_auth_token(expiration=3600),
        'expiration': 3600
    })
