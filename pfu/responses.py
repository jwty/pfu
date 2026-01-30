from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any


class Status(Enum):
    SUCCESS = 'success'
    ERROR = 'error'
    FILE_EXISTS = 'file_exists'


@dataclass
class Result:
    status: Status
    data: Optional[Any] = None
    error: Optional[str] = None

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
    def success(cls, data=None):
        return cls(status=Status.SUCCESS, data=data)

    @classmethod
    def error(cls, error_msg: str):
        return cls(status=Status.ERROR, error=error_msg)

    @classmethod
    def file_exists(cls, data):
        return cls(status=Status.FILE_EXISTS, data=data)
