from flask import Blueprint

auth = Blueprint('auth', __name__)

from . import views
from ..models import Permission


@auth.app_context_processor
def inject_permissions():
    """Import the Permission class into all views of the 'auth' module"""
    return dict(Permission=Permission)
