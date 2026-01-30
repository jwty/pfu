from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from markupsafe import Markup
from pfu.db import get_file_by_filename, update_file
from pfu.jobs import add_expire_job
from pfu.pagination import PaginationHelper
from pfu.scheduler import scheduler, next_midnight
from pfu.utils import get_stats, parse_expire_datetime, remove_file, save_file

main = Blueprint('main', __name__)


@main.get('/')
def index():
    return render_template('index.html')


@main.get('/home')
@login_required
def home():
    stats = get_stats()
    return render_template('home.html', stats=stats)


@main.get('/upload')
@login_required
def upload():
    return render_template('upload.html')


@main.post('/upload')
@login_required
def upload_post():
    file = request.files.get('file_up')
    keep_filename = 'keep' in request.form
    description = request.form.get('description')
    expire_date = request.form.get('expire-date')
    expire_time = request.form.get('expire-time') or '00:00'
    expire_timestamp = parse_expire_datetime(expire_date, expire_time)
    result = save_file(file, keep_filename, expire_timestamp, description)
    if result.is_success:
        if expire_timestamp and expire_timestamp <= next_midnight():
            add_expire_job(result.data.get('filename'), expire_timestamp)
        flash(Markup(f'File uploaded successfully: <a href="{result.data.get('file_url')}">{result.data.get('filename')}</a>'), 'success')
    elif result.is_file_exists:
        flash(Markup(f'File already exists: <a href="{result.data.get('file_url')}">{result.data.get('filename')}</a>'), 'warning')
    else:
        flash(f'Something went wrong while uploading the file: {result.error}', 'error')
    # Redirect instead of returning template to keep the nav item highlighted
    return redirect(url_for('main.upload'))


@main.get('/files')
@login_required
def files():
    page = PaginationHelper.from_request(request)
    files, current_page, total_pages = page.get_files()
    return render_template('files.html', files=files, current_page=current_page, possible_pages=total_pages, sort_by=page.sort_by, search_query=page.query)


@main.get('/search')
@login_required
def search():
    return render_template('search.html')


@main.post('/search')
@login_required
def search_post():
    search_query = request.form.get('query-filename')
    if not search_query:
        flash('Please enter a search query', 'error')
        return redirect(url_for('main.search'))
    return redirect(url_for('main.files', q=search_query))


@main.get('/delete/<filename_list>')
@login_required
def delete_files(filename_list):
    filename_list = filename_list.split(',')
    files = []
    for filename in filename_list:
        file = get_file_by_filename(filename)
        if file:
            files.append(file)
    next_view = request.args.get('next')
    return render_template('delete.html', files=files, next_view=next_view)


@main.post('/delete/<filename_list>')
@login_required
def delete_files_post(filename_list):
    filename_list = filename_list.split(',')
    errors = []
    for filename in filename_list:
        if scheduler.get_job(filename):
            scheduler.remove_job(filename)
        result = remove_file(filename)
        if result.is_error:
            errors.append(result.error)
    if errors:
        flash('Something went wrong while deleting files', 'warning')
        for error in errors:
            flash(error, 'error')
    else:
        flash('Files deleted successfully', 'success')
    next_view = request.args.get('next')
    return redirect(next_view or url_for('main.files'))


@main.get('/edit/<filename>')
@login_required
def edit_file(filename):
    file = get_file_by_filename(filename)
    if not file:
        flash('File not found', 'error')
        return redirect(url_for('main.files'))
    next_view = request.args.get('next')
    expire_date = datetime.fromtimestamp(file.get('expire_date')).strftime('%Y-%m-%d') if file.get('expire_date') else ''
    expire_time = datetime.fromtimestamp(file.get('expire_date')).strftime('%H:%M') if file.get('expire_date') else ''
    return render_template('edit.html', file=file, next_view=next_view, expire_date=expire_date, expire_time=expire_time)


@main.post('/edit/<filename>')
@login_required
def edit_file_post(filename):
    description = request.form.get('description')
    expire_date = request.form.get('expire-date')
    expire_time = request.form.get('expire-time') or '00:00'
    expire_timestamp = parse_expire_datetime(expire_date, expire_time)
    result = update_file(filename, description, expire_timestamp)
    if result.is_error:
        flash(result.error, 'error')
        return redirect(url_for('main.files'))
    has_expire_job = scheduler.get_job(filename)
    if expire_timestamp and expire_timestamp <= next_midnight() and not has_expire_job:
        add_expire_job(filename, expire_timestamp)
    if expire_timestamp is None and has_expire_job:
        scheduler.remove_job(filename)
    flash('File updated successfully', 'success')
    next_view = request.args.get('next')
    return redirect(next_view or url_for('main.files'))
