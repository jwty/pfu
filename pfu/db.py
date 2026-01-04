import os
from hashlib import md5
from peewee import *
from playhouse.shortcuts import model_to_dict
from pfu.config import Config

database = SqliteDatabase(Config.DATABASE)

def initialize_db():
    database.connect()
    database.create_tables([Files])
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
    checksum = TextField(null=True, unique=True)
    description = TextField(null=True)
    expire_date = IntegerField(null=True)
    new_filename = TextField(null=True)
    original_filename = TextField(null=True)
    upload_date = IntegerField(null=True)

    class Meta:
        table_name = 'files'


def add_file_to_db(original_filename, description, new_filename, upload_date, expire_date, checksum):
    Files.create(original_filename=original_filename, description=description, new_filename=new_filename, upload_date=upload_date, expire_date=expire_date, checksum=checksum)


def delete_by_filename(filename):
    Files.delete().where(Files.new_filename == filename).execute()
    os.remove(os.path.join(Config.UPLOAD_DIR, filename))


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
    chunk_size = Config.CHUNK_SIZE
    file_buffer = file_up.read(chunk_size)
    while file_buffer:
        md5_obj.update(file_buffer)
        file_buffer = file_up.read(chunk_size)
    file_up.seek(0)
    return md5_obj.hexdigest()
