from flask import Blueprint, render_template, request, url_for, redirect, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from pfu.auth import User
from pfu.db import get_files_count, get_files_expiring_count, get_files_size, get_files_page


auth = Blueprint('auth', __name__)


@auth.route('/login')
def login():
    if current_user.is_authenticated:
        flash('Already logged in', 'info')
        return redirect(url_for('main.index'))
    return render_template('login.html')


@auth.route('/login', methods=['POST'])
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
        next_page = url_for('main.index')
    return redirect(next_page)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('main.index'))


@auth.route('/settings')
@login_required
def settings():
    # TODO: Cache these
    files_count = get_files_count()
    files_expiring_count = get_files_expiring_count()
    files_size = get_files_size()
    return render_template('settings.html', files_count=files_count, files_expiring_count=files_expiring_count, files_size=files_size)


@auth.route('/files')
@login_required
def files():
    try:
        page_number = int(request.args.get('page', 1))
    except ValueError:
        flash('Invalid page number', 'error')
        page_number = 1
    if page_number < 1:
        flash('Invalid page number', 'error')
        page_number = 1
    sort_by = request.args.get('sort', 'date')
    files, current_page, possible_pages = get_files_page(10, page_number, sort_by)
    return render_template('files.html', files=files, current_page=current_page, possible_pages=possible_pages, sort_by=sort_by)
