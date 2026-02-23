import os
from secrets import token_hex
from typing import Optional, TypedDict, cast
from peewee import BooleanField, DoesNotExist, IntegerField, IntegrityError, Model, SqliteDatabase, TextField, fn
from playhouse.flask_utils import PaginatedQuery  # type: ignore
from werkzeug.security import generate_password_hash
from pfu.config import config
from pfu.responses import Result
from pfu.scheduler import next_midnight

database_path = os.path.join(config.DATA_DIR, 'database.db')
database = SqliteDatabase(database_path)


def initialize_db() -> SqliteDatabase:
    database.connect()
    database.create_tables([Files, Secrets])
    database.close()
    return database


def configure_db(app) -> None:
    database = initialize_db()

    @app.teardown_request
    def teardown_request(exception: Optional[BaseException] = None) -> None:
        if not database.is_closed():
            database.close()


class BaseModel(Model):
    class Meta:
        database = database


class FileDict(TypedDict):
    id: int
    filename: str
    original_filename: str
    description: str
    checksum: str
    upload_date: int
    expire_date: Optional[int]
    size: int
    file_url: str


class SecretDict(TypedDict):
    id: int
    name: str
    description: Optional[str]
    perm_read: bool
    perm_write: bool
    perm_delete: bool
    prefix: str
    hash: str


class FileSizeDict(TypedDict):
    filename: str
    size: int


class FileExpireDict(TypedDict):
    filename: str
    expire_date: int


class Files(BaseModel):
    filename = TextField(index=True)
    original_filename = TextField()
    description = TextField()
    checksum = TextField(unique=True)
    upload_date = IntegerField()
    expire_date = IntegerField(null=True)
    size = IntegerField()

    @property
    def file_url(self) -> str:
        return f"{config.FILE_URL_PREFIX}{self.filename}"

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


def _file_to_dict(file: Files) -> FileDict:
    return FileDict(
        id=cast(int, file.get_id()),
        filename=cast(str, file.filename),
        original_filename=cast(str, file.original_filename),
        description=cast(str, file.description),
        checksum=cast(str, file.checksum),
        upload_date=cast(int, file.upload_date),
        expire_date=cast(Optional[int], file.expire_date),
        size=cast(int, file.size),
        file_url=cast(str, file.file_url)
    )


def _secret_to_dict(secret: Secrets) -> SecretDict:
    return SecretDict(
        id=cast(int, secret.get_id()),
        name=cast(str, secret.name),
        description=cast(Optional[str], secret.description),
        perm_read=cast(bool, secret.perm_read),
        perm_write=cast(bool, secret.perm_write),
        perm_delete=cast(bool, secret.perm_delete),
        prefix=cast(str, secret.prefix),
        hash=cast(str, secret.hash)
    )


def add_file_to_db(filename: str, original_filename: str, description: str, checksum: str, upload_date: int, expire_date: Optional[int], size: int) -> None:
    Files.create(filename=filename, original_filename=original_filename, description=description, checksum=checksum, upload_date=upload_date, expire_date=expire_date, size=size)


def delete_file_record(filename: str) -> None:
    Files.delete().where(Files.filename == filename).execute()


def get_file_by_checksum(checksum: str) -> Optional[FileDict]:
    try:
        file = Files.get(Files.checksum == checksum)
    except DoesNotExist:
        return None
    return _file_to_dict(file)


def get_file_by_filename(filename: str) -> Optional[FileDict]:
    try:
        file = Files.get(Files.filename == filename)
    except DoesNotExist:
        return None
    return _file_to_dict(file)


def update_file(filename: str, description: str, expire_date: Optional[int] = None) -> Result:
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


def update_file_checksum_and_size(filename: str, new_checksum: str, new_size: int) -> Result:
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


def get_files_count() -> int:
    return Files.select().count()


def get_files_expiring_count() -> int:
    return Files.select().where(Files.expire_date.is_null(False)).count()


def get_files_size() -> int:
    return Files.select(fn.SUM(Files.size)).scalar() or 0


def get_files_page(per_page: int, page: int, sort_by: str, query: Optional[str] = None) -> tuple[list[Files], int, int]:
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


def get_files_list() -> list[str]:
    return [file.filename for file in Files.select()]


def get_all_file_sizes() -> list[FileSizeDict]:
    return [FileSizeDict(filename=file.filename, size=file.size) for file in Files.select(Files.filename, Files.size)]


def get_secrets() -> list[SecretDict]:
    return [_secret_to_dict(secret) for secret in Secrets.select()]


def get_secret(prefix: Optional[str] = None, secret_id: Optional[int] = None) -> Optional[SecretDict]:
    try:
        if prefix:
            secret = Secrets.get(Secrets.prefix == prefix)
        elif secret_id:
            secret = Secrets.get_by_id(secret_id)
    except DoesNotExist:
        return None
    return _secret_to_dict(secret)


def new_secret(name: str, description: Optional[str], perm_read: bool, perm_write: bool, perm_delete: bool) -> Result:
    secret_prefix = token_hex(4)
    secret_token = token_hex(16)
    secret_key = f'{secret_prefix}-{secret_token}'
    secret_hash = generate_password_hash(secret_token)
    try:
        Secrets.create(name=name, description=description, perm_read=perm_read, perm_write=perm_write, perm_delete=perm_delete, prefix=secret_prefix, hash=secret_hash)
    except IntegrityError:
        return Result.error(f'Secret "{name}" already exists')
    return Result.success(data=secret_key)


def delete_secret(secret_id: int) -> Result:
    try:
        secret = Secrets.get_by_id(secret_id)
        secret.delete_instance()
    except DoesNotExist:
        return Result.error('Secret not found')
    return Result.success()


def get_today_expiring_files() -> list[FileExpireDict]:
    expiring_files_query = Files.select(Files.filename, Files.expire_date).where(Files.expire_date <= next_midnight())
    return [FileExpireDict(filename=expiring_file.filename, expire_date=expiring_file.expire_date) for expiring_file in expiring_files_query]
