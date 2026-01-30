from dataclasses import dataclass
from typing import Optional
from flask import request
from pfu.db import get_files_page


@dataclass
class PaginationHelper:
    # Class defaults for convenient instance creation
    page: int = 1
    per_page: int = 10
    sort_by: str = 'date'
    query: Optional[str] = None

    @classmethod
    def from_request(cls, request):
        # request.args.defaults to avoid None values
        page = max(1, request.args.get('page', 1, int))
        per_page = request.args.get('c', 10, int)
        sort_by = request.args.get('sort', 'date')
        query = request.args.get('q')
        return cls(page=page, per_page=per_page, sort_by=sort_by, query=query)

    def get_files(self):
        files, current_page, total_pages = get_files_page(self.per_page, self.page, self.sort_by, query=self.query)
        # Re-fetch if out of bounds
        if self.page > total_pages > 0:
            files, current_page, total_pages = get_files_page(self.per_page, total_pages, self.sort_by, query=self.query)
        return files, current_page, total_pages
