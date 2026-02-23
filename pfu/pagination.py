from dataclasses import dataclass
from typing import Optional
from werkzeug.wrappers import Request
from pfu.db import Files, get_files_page


@dataclass
class PaginationHelper:
    # Class defaults for convenient instance creation
    page: int = 1
    per_page: int = 10
    sort_by: str = 'date'
    query: Optional[str] = None

    @classmethod
    def from_request(cls, request_obj: Request) -> 'PaginationHelper':
        # request_obj.args.defaults to avoid None values
        page = max(1, request_obj.args.get('page', 1, int))
        per_page = request_obj.args.get('c', 10, int)
        sort_by = request_obj.args.get('sort', 'date')
        query = request_obj.args.get('q')
        return cls(page=page, per_page=per_page, sort_by=sort_by, query=query)

    def get_files(self) -> tuple[list[Files], int, int]:
        files, current_page, total_pages = get_files_page(self.per_page, self.page, self.sort_by, query=self.query)
        # Re-fetch if out of bounds
        if self.page > total_pages > 0:
            files, current_page, total_pages = get_files_page(self.per_page, total_pages, self.sort_by, query=self.query)
        return files, current_page, total_pages
