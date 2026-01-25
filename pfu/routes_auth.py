from flask import Blueprint, render_template, request, url_for, redirect, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from pfu.auth import User
from pfu.db import get_files_count, get_files_expiring_count, get_files_size, get_files_page, get_file_by_filename, delete_by_filename


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


# TODO: These should be moved to main bp when it gets cleaned up
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
    page_number = int(request.args.get('page', 1, int))
    if page_number < 1:
        flash('Invalid page number', 'error')
        page_number = 1
    sort_by = request.args.get('sort', 'date')
    files_per_page = request.args.get('c', 10, int)
    search_query = request.args.get('q')
    files, current_page, possible_pages = get_files_page(files_per_page, page_number, sort_by, query=search_query)
    return render_template('files.html', files=files, current_page=current_page, possible_pages=possible_pages, sort_by=sort_by, search_query=search_query)


@auth.get('/search')
@login_required
def search():
    return render_template('search.html')


@auth.post('/search')
@login_required
def search_post():
    search_query = request.form.get('query-filename')
    if not search_query:
        flash('Please enter a search query', 'error')
        return redirect(url_for('auth.search'))
    return redirect(url_for('auth.files', q=search_query))


@auth.get('/delete/<filename_list>')
@login_required
def delete_files(filename_list):
    filename_list = filename_list.split(',')
    files = []
    for filename in filename_list:
        file = get_file_by_filename(filename)
        if file:
            files.append(file)
    return render_template('delete.html', files=files)


@auth.post('/delete/<filename_list>')
@login_required
def delete_files_post(filename_list):
    filename_list = filename_list.split(',')
    errors = []
    for filename in filename_list:
        try:
            delete_by_filename(filename)
        except Exception as e:
            errors.append(f'Error for file {filename}: {e}')
    if errors:
        flash('Something went wrong while deleting files', 'warning')
        for error in errors:
            flash(error, 'error')
    else:
        flash('Files deleted successfully', 'success')
    return redirect(url_for('auth.files'))
