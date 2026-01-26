from datetime import datetime
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required
from markupsafe import Markup
from pfu.db import delete_by_filename, get_file_by_filename, get_files_count, get_files_expiring_count, get_files_page, get_files_size, update_file
from pfu.utils import save_file


main = Blueprint('main', __name__)


@main.get('/')
def index():
    # TODO: Display a message of some kind here
    return render_template('index.html')


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
    expire_timestamp = None
    if expire_date:
        expire_timestamp = datetime.combine(datetime.strptime(expire_date, '%Y-%m-%d'), datetime.strptime(expire_time, '%H:%M').time()).timestamp()
    status, response = save_file(file, keep_filename, expire_timestamp, description)
    file_url = f'{request.url_root}{current_app.config['FILE_URL_PREFIX']}{response.get('filename')}'
    if status == 'success':
        flash(Markup(f'File uploaded successfully: <a href="{file_url}">{response.get('filename')}</a>'), 'success')
    elif status == 'file_exists':
        flash(Markup(f'File already exists: <a href="{file_url}">{response.get('filename')}</a>'), 'warning')
    else:
        flash(f'Something went wrong while uploading the file: {response}', 'error')
    # Redirect instead of returning template to keep the nav item highlighted
    return redirect(url_for('main.upload'))


@main.get('/home')
@login_required
def home():
    # TODO: Cache these
    files_count = get_files_count()
    files_expiring_count = get_files_expiring_count()
    files_size = get_files_size()
    return render_template('home.html', files_count=files_count, files_expiring_count=files_expiring_count, files_size=files_size)


@main.get('/settings')
@login_required
def settings():
    return render_template('settings.html')


@main.get('/files')
@login_required
def files():
    page_number = int(request.args.get('page', 1, int))
    if page_number < 1:
        page_number = 1
    sort_by = request.args.get('sort', 'date')
    files_per_page = request.args.get('c', 10, int)
    search_query = request.args.get('q')
    files, current_page, possible_pages = get_files_page(files_per_page, page_number, sort_by, query=search_query)
    # Re-fetch if page number is out of bounds (for example, on file deletion)
    if page_number > possible_pages and possible_pages > 0:
        files, current_page, possible_pages = get_files_page(files_per_page, possible_pages, sort_by, query=search_query)
    return render_template('files.html', files=files, current_page=current_page, possible_pages=possible_pages, sort_by=sort_by, search_query=search_query)


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
    expire_timestamp = None
    if expire_date:
        expire_timestamp = datetime.combine(datetime.strptime(expire_date, '%Y-%m-%d'), datetime.strptime(expire_time, '%H:%M').time()).timestamp()
    try:
        update_file(filename, description, expire_timestamp)
        flash('File updated successfully', 'success')
    except Exception as e:
        flash(f'Error updating file {filename}: {e}', 'error')
    next_view = request.args.get('next')
    return redirect(next_view or url_for('main.files'))
