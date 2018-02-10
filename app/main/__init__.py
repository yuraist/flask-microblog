from flask import Blueprint

# Initialize a blueprint for the 'main' module
main = Blueprint('main', __name__)

from . import views, errors
from ..models import Permission


@main.app_context_processor
def inject_permissions():
    """Import the Permission class into all view templates of the main module"""
    return dict(Permission=Permission)