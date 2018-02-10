from flask import Blueprint

api = Blueprint('api', __name__)

from . import authentication, comments, decorators, errors, posts, users
from ..models import Permission


@api.app_context_processor
def inject_permissions():
    """Import the Permission class into each view of the 'api' module"""
    return dict(Permission=Permission)
