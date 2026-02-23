import logging
from os import listdir
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required
from markupsafe import Markup
from werkzeug.wrappers import Response
from pfu.db import delete_secret, get_files_list, get_secret, get_secrets, new_secret
from pfu.utils import integrity_check, update_stats

admin = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)


@admin.get('/update-stats')
@login_required
def update_stats_route() -> Response:
    update_stats()
    return redirect(url_for('main.home'))


@admin.get('/run-integrity-check')
@login_required
def run_integrity_check() -> Response:
    integrity_check()
    flash('Integrity check completed successfully', 'success')
    return redirect(url_for('main.home'))


@admin.get('/check-for-orphans')
@login_required
def check_for_orphans() -> Response:
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
def api_secrets() -> str:
    secrets = get_secrets()
    return render_template('api_secrets.html', secrets=secrets)


@admin.post('/create_secret')
@login_required
def create_secret() -> Response:
    name = request.form.get('name') or ''
    description = request.form.get('description')
    perm_read = 'perm_read' in request.form
    perm_write = 'perm_write' in request.form
    perm_delete = 'perm_delete' in request.form
    result = new_secret(name, description, perm_read, perm_write, perm_delete)
    if result.is_success:
        logger.info(f'API secret created: {name}, permissions: read = {perm_read}, write = {perm_write}, delete = {perm_delete}')
        flash(Markup(f'Secret created successfully: <code>{result.data}</code>'), 'success')
    else:
        flash(f'Something went wrong: {result.error_message}', 'error')
    return redirect(url_for('admin.api_secrets'))


@admin.post('/delete_secret/<int:secret_id>')
@login_required
def delete_secret_post(secret_id: int) -> Response:
    secret = get_secret(secret_id=secret_id)
    secret_name = secret.get('name') if secret else None
    result = delete_secret(secret_id)
    if result.is_success:
        logger.info(f'API secret deleted: {secret_name}')
        flash('Secret deleted successfully', 'success')
    else:
        flash(f'Something went wrong: {result.error_message}', 'error')
    return redirect(url_for('admin.api_secrets'))
