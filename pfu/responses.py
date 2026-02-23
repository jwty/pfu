from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Status(Enum):
    SUCCESS = 'success'
    ERROR = 'error'
    FILE_EXISTS = 'file_exists'


@dataclass
class Result:
    status: Status
    data: Optional[dict[str, object] | str | bool] = None
    error_message: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return self.status == Status.SUCCESS

    @property
    def is_error(self) -> bool:
        return self.status == Status.ERROR

    @property
    def is_file_exists(self) -> bool:
        return self.status == Status.FILE_EXISTS

    @classmethod
    def success(cls, data: dict[str, object] | str | bool | None = None) -> 'Result':
        return cls(status=Status.SUCCESS, data=data)

    @classmethod
    def error(cls, error_msg: str) -> 'Result':
        return cls(status=Status.ERROR, error_message=error_msg)

    @classmethod
    def file_exists(cls, data: dict[str, object] | str | bool | None) -> 'Result':
        return cls(status=Status.FILE_EXISTS, data=data)
