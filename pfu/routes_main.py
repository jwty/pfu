from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from markupsafe import Markup
from werkzeug.wrappers import Response
from pfu.db import get_file_by_filename, update_file
from pfu.jobs import add_expire_job
from pfu.pagination import PaginationHelper
from pfu.scheduler import next_midnight, scheduler
from pfu.utils import get_stats, parse_expire_datetime, recalculate_file, remove_file, save_file

main = Blueprint('main', __name__)


@main.get('/')
def index() -> str | Response:
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    return render_template('index.html')


@main.get('/home')
@login_required
def home() -> str:
    stats = get_stats()
    return render_template('home.html', stats=stats)


@main.get('/upload')
@login_required
def upload() -> str:
    return render_template('upload.html')


@main.post('/upload')
@login_required
def upload_post() -> Response:
    file = request.files.get('file_up')
    keep_filename = 'keep' in request.form
    description = request.form.get('description', '')
    expire_date = request.form.get('expire-date')
    expire_time = request.form.get('expire-time') or '00:00'
    if not file:
        flash('No file provided', 'error')
        return redirect(url_for('main.upload'))
    expire_timestamp = parse_expire_datetime(expire_date, expire_time)
    result = save_file(file, keep_filename, expire_timestamp, description)
    if result.is_error:
        flash(f'Something went wrong while uploading the file: {result.error_message or "Unknown error"}', 'error')
        return redirect(url_for('main.upload'))
    if not isinstance(result.data, dict):
        flash('Something went wrong: Invalid data format returned.', 'error')
        return redirect(url_for('main.upload'))
    if result.is_file_exists:
        flash(Markup(f'File already exists: <a href="{result.data.get("file_url")}">{result.data.get("filename")}</a>'), 'warning')
        return redirect(url_for('main.upload'))
    if result.is_success:
        if expire_timestamp and expire_timestamp <= next_midnight() and isinstance(filename := result.data.get('filename'), str):
            add_expire_job(filename, expire_timestamp)
        flash(Markup(f'File uploaded successfully: <a href="{result.data.get("file_url")}">{result.data.get("filename")}</a>'), 'success')
    # Redirect instead of returning template to keep the nav item highlighted
    return redirect(url_for('main.upload'))


@main.get('/files')
@login_required
def files() -> str:
    page = PaginationHelper.from_request(request)
    files, current_page, total_pages = page.get_files()
    return render_template('files.html', files=files, current_page=current_page, possible_pages=total_pages, sort_by=page.sort_by, search_query=page.query)


@main.get('/search')
@login_required
def search() -> str:
    return render_template('search.html')


@main.post('/search')
@login_required
def search_post() -> Response:
    search_query = request.form.get('query-filename')
    if not search_query:
        flash('Please enter a search query', 'error')
        return redirect(url_for('main.search'))
    return redirect(url_for('main.files', q=search_query))


@main.get('/delete/<filename_list>')
@login_required
def delete_files(filename_list: str) -> str:
    filenames = filename_list.split(',')
    files = []
    for filename in filenames:
        file = get_file_by_filename(filename)
        if file:
            files.append(file)
    next_view = request.args.get('next')
    return render_template('delete.html', files=files, next_view=next_view)


@main.post('/delete/<filename_list>')
@login_required
def delete_files_post(filename_list: str) -> Response:
    filenames = filename_list.split(',')
    errors = []
    for filename in filenames:
        if scheduler.get_job(filename):
            scheduler.remove_job(filename)
        result = remove_file(filename)
        if result.is_error:
            errors.append(result.error_message or "Unknown error")
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
def edit_file(filename: str) -> str | Response:
    file = get_file_by_filename(filename)
    if not file:
        flash('File not found', 'error')
        return redirect(url_for('main.files'))
    next_view = request.args.get('next')
    expire_date, expire_time = '', ''
    file_expire_date = file.get('expire_date') if file else None
    # Explicit 'is not None' is required by Mypy because 0 is a valid falsy int
    if file_expire_date is not None:
        dt = datetime.fromtimestamp(file_expire_date)
        expire_date = dt.strftime('%Y-%m-%d')
        expire_time = dt.strftime('%H:%M')
    return render_template('edit.html', file=file, next_view=next_view, expire_date=expire_date, expire_time=expire_time)


@main.post('/edit/<filename>')
@login_required
def edit_file_post(filename: str) -> Response:
    description = request.form.get('description', '')
    expire_date = request.form.get('expire-date')
    expire_time = request.form.get('expire-time') or '00:00'
    expire_timestamp = parse_expire_datetime(expire_date, expire_time)
    result = update_file(filename, description, expire_timestamp)
    if result.is_error:
        flash(result.error_message or "Unknown error", 'error')
        return redirect(url_for('main.files'))
    has_expire_job = scheduler.get_job(filename)
    if expire_timestamp and expire_timestamp <= next_midnight() and not has_expire_job:
        add_expire_job(filename, expire_timestamp)
    if expire_timestamp is None and has_expire_job:
        scheduler.remove_job(filename)
    flash('File updated successfully', 'success')
    next_view = request.args.get('next')
    return redirect(next_view or url_for('main.files'))


@main.post('/recalculate/<filename>')
@login_required
def recalculate_file_post(filename: str) -> Response:
    result = recalculate_file(filename)
    if result.is_error:
        flash(result.error_message or "Unknown error", 'error')
    else:
        flash('File checksum and size recalculated successfully', 'success')
    return redirect(url_for('main.edit_file', filename=filename))
