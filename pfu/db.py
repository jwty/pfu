import os
from peewee import fn, SqliteDatabase, Model, TextField, IntegerField, BooleanField, DoesNotExist, IntegrityError
from playhouse.flask_utils import PaginatedQuery
from playhouse.shortcuts import model_to_dict
from secrets import token_hex
from werkzeug.security import generate_password_hash
from pfu.config import config
from pfu.responses import Result
from pfu.scheduler import next_midnight

database_path = os.path.join(config.DATA_DIR, 'database.db')
database = SqliteDatabase(database_path)


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
    description = TextField()
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


def delete_file_record(filename):
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
    try:
        file = Files.get(Files.filename == filename)
        file.description = description
        file.expire_date = expire_date
        file.save()
    except DoesNotExist:
        return Result.error(f'File {filename} not found')
    except Exception as e:
        # Generic since it should only catch database errors
        return Result.error(f'Failed to update file {filename}: {str(e)}')
    return Result.success()


def update_file_checksum_and_size(filename, new_checksum, new_size):
    try:
        file = Files.get(Files.filename == filename)
        file.checksum = new_checksum
        file.size = new_size
        file.save()
    except DoesNotExist:
        return Result.error(f'File {filename} not found')
    except IntegrityError:
        return Result.error(f'Checksum {new_checksum} already exists in database')
    except Exception as e:
        return Result.error(f'Failed to update checksum for file {filename}: {str(e)}')
    return Result.success()


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


def get_files_list():
    return [file.filename for file in Files.select()]


def get_secrets():
    return [model_to_dict(secret) for secret in Secrets.select()]


def get_secret(prefix=None, secret_id=None):
    try:
        if prefix:
            secret = Secrets.get(Secrets.prefix == prefix)
        elif secret_id:
            secret = Secrets.get(Secrets.id == secret_id)
    except DoesNotExist:
        return None
    return model_to_dict(secret)


def new_secret(name, description, perm_read, perm_write, perm_delete):
    secret_prefix = token_hex(4)
    secret_token = token_hex(16)
    secret_key = f'{secret_prefix}-{secret_token}'
    secret_hash = generate_password_hash(secret_token)
    try:
        Secrets.create(name=name, description=description, perm_read=perm_read, perm_write=perm_write, perm_delete=perm_delete, prefix=secret_prefix, hash=secret_hash)
    except IntegrityError:
        return Result.error(f'Secret "{name}" already exists')
    return Result.success(data=secret_key)


def delete_secret(secret_id):
    try:
        secret = Secrets.get(Secrets.id == secret_id)
        secret.delete_instance()
    except DoesNotExist:
        return Result.error('Secret not found')
    return Result.success()


def get_today_expiring_files():
    expiring_files_query = Files.select(Files.filename, Files.expire_date).where(Files.expire_date <= next_midnight())
    return [model_to_dict(expiring_file, only=[Files.filename, Files.expire_date]) for expiring_file in expiring_files_query]
