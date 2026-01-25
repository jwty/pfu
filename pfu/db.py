import os
from hashlib import md5
from peewee import *
from playhouse.shortcuts import model_to_dict
from playhouse.flask_utils import PaginatedQuery
from pfu.config import config

database_path = os.path.join(config['DATA_DIR'], 'database.db')
database = SqliteDatabase(database_path, pragmas={'foreign_keys': 1})

def initialize_db():
    database.connect()
    database.create_tables([Files, ExpiringFiles, Secrets])
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
    # TODO: "new" is redundant
    new_filename = TextField(index=True)
    original_filename = TextField()
    description = TextField(null=True)
    checksum = TextField(unique=True)
    upload_date = IntegerField()
    expire_date = IntegerField(null=True)
    size = IntegerField()

    class Meta:
        table_name = 'files'


class ExpiringFiles(BaseModel):
    file = ForeignKeyField(Files, on_delete='CASCADE')
    expire_date = IntegerField(null=True)


class Secrets(BaseModel):
    name = TextField()
    description = TextField(null=True)
    perm_read = BooleanField(default=False)
    perm_write = BooleanField(default=False)
    perm_delete = BooleanField(default=False)
    hash = TextField(index=True)



def add_file_to_db(new_filename, original_filename, description, checksum, upload_date, expire_date, size):
    file = Files.create(**locals())
    if expire_date:
        ExpiringFiles.create(file=file, expire_date=expire_date)


def delete_by_filename(filename):
    Files.delete().where(Files.new_filename == filename).execute()
    os.remove(os.path.join(config['UPLOAD_DIR'], filename))


def get_file_by_checksum(checksum):
    try:
        file = Files.get(Files.checksum == checksum)
    except DoesNotExist:
        return None
    return model_to_dict(file)


def get_file_by_filename(filename):
    try:
        file = Files.get(Files.new_filename == filename)
    except DoesNotExist:
        return None
    return model_to_dict(file)


def calc_md5(file_up):
    md5_obj = md5()
    chunk_size = config['CHUNK_SIZE']
    file_buffer = file_up.read(chunk_size)
    while file_buffer:
        md5_obj.update(file_buffer)
        file_buffer = file_up.read(chunk_size)
    file_up.seek(0)
    return md5_obj.hexdigest()


def get_files_count():
    return Files.select().count()


def get_files_expiring_count():
    return ExpiringFiles.select().count()


def get_files_size():
    return Files.select(fn.SUM(Files.size)).scalar() or 0


def get_files_page(per_page, page, sort_by, query=None):
    base_query = Files.select()
    if query:
        base_query = base_query.where(Files.new_filename.contains(query) | Files.original_filename.contains(query))
    if sort_by == 'size':
        page_query = PaginatedQuery(base_query.order_by(Files.size.desc()), per_page, page=page, check_bounds=True)
    elif sort_by == 'expire_date':
        page_query = PaginatedQuery(base_query.order_by(Files.expire_date.desc()), per_page, page=page, check_bounds=True)
    else:
        page_query = PaginatedQuery(base_query.order_by(Files.upload_date.desc()), per_page, page=page, check_bounds=True)
    files = page_query.get_object_list()
    current_page = page_query.get_page()
    possible_pages = page_query.get_page_count()
    return files, current_page, possible_pages
