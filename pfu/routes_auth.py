from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash
from pfu.auth import User


auth = Blueprint('auth', __name__)


@auth.get('/login')
def login():
    if current_user.is_authenticated:
        flash('Already logged in', 'info')
        return redirect(url_for('main.index'))
    return render_template('login.html')


@auth.post('/login')
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    remember_user = True if request.form.get('remember_user') else False
    user = User()
    if username != user.username or not check_password_hash(user.password, password):
        flash('Invalid credentials', 'error')
        return render_template('login.html')
    login_user(user, remember=remember_user)
    flash('Logged in successfully', 'success')
    next_page = request.args.get('next')
    if not next_page or not next_page.startswith('/'):
        next_page = url_for('main.home')
    return redirect(next_page)


@auth.get('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('main.index'))
