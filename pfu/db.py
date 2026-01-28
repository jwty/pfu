import os
from datetime import datetime
from peewee import *
from playhouse.flask_utils import PaginatedQuery
from playhouse.shortcuts import model_to_dict
from secrets import token_hex
from werkzeug.security import generate_password_hash
from pfu.config import config
from pfu.scheduler import scheduler, next_midnight

database_path = os.path.join(config['DATA_DIR'], 'database.db')
database = SqliteDatabase(database_path, pragmas={'foreign_keys': 1})

def initialize_db():
    database.connect()
    database.create_tables([Files, Secrets])
    database.close()
    return database


def configure_db(app):
    database = initialize_db()
    @app.teardown_request
    def teardown_request(exception):
        if not database.is_closed():
            database.close()


class BaseModel(Model):
    class Meta:
        database = database


class Files(BaseModel):
    filename = TextField(index=True)
    original_filename = TextField()
    description = TextField(null=True)
    checksum = TextField(unique=True)
    upload_date = IntegerField()
    expire_date = IntegerField(null=True)
    size = IntegerField()

    class Meta:
        table_name = 'files'


class Secrets(BaseModel):
    name = TextField(unique=True)
    description = TextField(null=True)
    perm_read = BooleanField(default=False)
    perm_write = BooleanField(default=False)
    perm_delete = BooleanField(default=False)
    prefix = TextField(index=True)
    hash = TextField()



def add_file_to_db(filename, original_filename, description, checksum, upload_date, expire_date, size):
    Files.create(filename=filename, original_filename=original_filename, description=description, checksum=checksum, upload_date=upload_date, expire_date=expire_date, size=size)


def delete_by_filename(filename):
    try:
        os.remove(os.path.join(config['UPLOAD_DIR'], filename))
    except FileNotFoundError:
        pass
    Files.delete().where(Files.filename == filename).execute()


def get_file_by_checksum(checksum):
    try:
        file = Files.get(Files.checksum == checksum)
    except DoesNotExist:
        return None
    return model_to_dict(file)


def get_file_by_filename(filename):
    try:
        file = Files.get(Files.filename == filename)
    except DoesNotExist:
        return None
    return model_to_dict(file)


def update_file(filename, description, expire_date=None):
    file = Files.get(Files.filename == filename)
    file.description = description
    file.expire_date = expire_date
    file.save()
    has_expire_job = scheduler.get_job(filename)
    if expire_date and expire_date <= next_midnight() and not has_expire_job:
        add_expire_job(filename, expire_date)
    if expire_date == None and has_expire_job:
        scheduler.remove_job(filename)


def get_files_count():
    return Files.select().count()


def get_files_expiring_count():
    return Files.select().where(Files.expire_date.is_null(False)).count()


def get_files_size():
    return Files.select(fn.SUM(Files.size)).scalar() or 0


def get_files_page(per_page, page, sort_by, query=None):
    base_query = Files.select()
    if query:
        base_query = base_query.where(Files.filename.contains(query) | Files.original_filename.contains(query))
    if sort_by == 'size':
        page_query = PaginatedQuery(base_query.order_by(Files.size.desc()), per_page, page=page, check_bounds=False)
    elif sort_by == 'expire_date':
        page_query = PaginatedQuery(base_query.order_by(Files.expire_date.desc()), per_page, page=page, check_bounds=False)
    else:
        page_query = PaginatedQuery(base_query.order_by(Files.upload_date.desc()), per_page, page=page, check_bounds=False)
    files = page_query.get_object_list()
    current_page = page_query.get_page()
    possible_pages = page_query.get_page_count()
    return files, current_page, possible_pages


def get_secrets():
    return [model_to_dict(secret) for secret in Secrets.select()]


def get_secret(prefix):
    try:
        secret = Secrets.get(Secrets.prefix == prefix)
    except DoesNotExist:
        return None
    return model_to_dict(secret)


def new_secret(name, description, perm_read, perm_write, perm_delete):
    secret_prefix = token_hex(4)
    secret_token = token_hex(16)
    secret_key = f'{secret_prefix}-{secret_token}'
    hash = generate_password_hash(secret_token)
    try:
        Secrets.create(name=name, description=description, perm_read=perm_read, perm_write=perm_write, perm_delete=perm_delete, prefix=secret_prefix, hash=hash)
    except IntegrityError:
        return 'error', f'Secret "{name}" already exists'
    return 'success', secret_key


def delete_secret(secret_id):
    try:
        secret = Secrets.get(Secrets.id == secret_id)
        secret.delete_instance()
    except DoesNotExist:
        return 'error', 'Secret not found'
    return 'success', 'Secret deleted successfully'


def get_today_expiring_files():
    expiring_files_query = Files.select(Files.filename, Files.expire_date).where(Files.expire_date <= next_midnight())
    return [model_to_dict(expiring_file, only=[Files.filename, Files.expire_date]) for expiring_file in expiring_files_query]


# It has to sit here to avoid circular import lol
def add_expire_job(filename, expire_date):
    scheduler.add_job(
            id=filename,
            name=f'Expire {filename}',
            func=delete_by_filename,
            args=[filename],
            trigger='date',
            run_date=datetime.fromtimestamp(expire_date),
            misfire_grace_time=None
        )