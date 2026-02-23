import logging
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash
from werkzeug.wrappers import Response
from pfu.auth import User, new_session_token
from pfu.config import security_warnings

auth = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)


@auth.get('/login')
def login() -> str | Response:
    if current_user.is_authenticated:
        flash('Already logged in', 'info')
        return redirect(url_for('main.index'))
    return render_template('login.html')


@auth.post('/login')
def login_post() -> str | Response:
    username = request.form.get('username')
    password = request.form.get('password') or ''
    remember_user = True if request.form.get('remember_user') else False
    user = User()
    if username != user.username or not check_password_hash(user.password, password):
        logger.warning(f'Failed login attempt from IP {request.remote_addr}')
        flash('Invalid credentials', 'error')
        return render_template('login.html')
    login_user(user, remember=remember_user)
    logger.info(f'Admin logged in from IP {request.remote_addr}')
    flash('Logged in successfully', 'success')
    # Flash security warnings if any exist
    for warning in security_warnings:
        flash(warning, 'warning')
    next_page = request.args.get('next')
    if not next_page or not next_page.startswith('/'):
        next_page = url_for('main.home')
    return redirect(next_page)


@auth.get('/logout')
@login_required
def logout() -> Response:
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('main.index'))


@auth.get('/logout-all-sessions')
@login_required
def logout_all_sessions() -> Response:
    new_session_token()
    logout_user()
    logger.debug('All sessions invalidated')
    flash('Logged out from all sessions successfully', 'success')
    return redirect(url_for('main.index'))
