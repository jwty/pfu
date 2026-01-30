from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required
from markupsafe import Markup
from os import listdir
from pfu.db import delete_secret, get_files_list, get_secrets, new_secret
from pfu.utils import update_stats

admin = Blueprint('admin', __name__)


@admin.get('/update-stats')
@login_required
def update_stats_route():
    update_stats()
    return redirect(url_for('main.home'))


@admin.get('/check-for-orphans')
@login_required
def check_for_orphans():
    files_in_db = set(get_files_list())
    files_in_dir = set(listdir(current_app.config['UPLOAD_DIR']))
    orphaned_files = list(files_in_dir - files_in_db)
    orphaned_db_entries = list(files_in_db - files_in_dir)
    if orphaned_files or orphaned_db_entries:
        flash(Markup(render_template('_orphans_message_template.html', orphaned_files=orphaned_files, orphaned_db_entries=orphaned_db_entries)), 'warning')
    else:
        flash('No orphaned files found', 'success')
    return redirect(url_for('main.home'))


@admin.get('/api_secrets')
@login_required
def api_secrets():
    secrets = get_secrets()
    return render_template('api_secrets.html', secrets=secrets)


@admin.post('/create_secret')
@login_required
def create_secret():
    name = request.form.get('name')
    description = request.form.get('description')
    perm_read = 'perm_read' in request.form
    perm_write = 'perm_write' in request.form
    perm_delete = 'perm_delete' in request.form
    result = new_secret(name, description, perm_read, perm_write, perm_delete)
    if result.is_success:
        flash(Markup(f'Secret created successfully: <code>{result.data}</code>'), 'success')
    else:
        flash(f'Something went wrong: {result.error}', 'error')
    return redirect(url_for('admin.api_secrets'))


@admin.post('/delete_secret/<secret_id>')
@login_required
def delete_secret_post(secret_id):
    result = delete_secret(secret_id)
    if result.is_success:
        flash('Secret deleted successfully', 'success')
    else:
        flash(f'Something went wrong: {result.error}', 'error')
    return redirect(url_for('admin.api_secrets'))
