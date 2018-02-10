from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from .. import db
from .forms import LoginForm, RegistrationForm
from ..models import User, Permission


@auth.before_app_request
def before_request():
    """Ping before each request for updating user's 'last_seen' property"""
    if current_user.is_authenticated:
        current_user.ping()


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """View of the login page"""
    form = LoginForm()
    if form.validate_on_submit():
        # Looking for a user
        user = User.query.filter_by(username=form.username.data).first()

        # Checking password
        if user is not None and user.verify_password(form.password.data):
            # User authorization
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))

        # Returning an error
        flash('Invalid username or password')
    return render_template('auth/login.html', form=form, Permission=Permission)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    """View of the register page"""
    form = RegistrationForm()

    # Validate the form
    if form.validate_on_submit():
        # Create a new user
        user = User(email=form.email.data, username=form.username.data, password=form.password.data)
        # Add the user into the database
        db.session.add(user)
        user.follow(user)
        db.session.commit()
        flash('You can now login.')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form, Permission=Permission)


@auth.route('/logout')
@login_required
def logout():
    """View for logout"""
    logout_user()
    flash('You have been logout')
    return redirect(url_for('main.index'))
