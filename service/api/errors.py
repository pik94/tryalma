from collections.abc import Hashable
from dataclasses import dataclass


@dataclass
class HttpPnlServiceException(Exception):
    status_code: int
    message: str
    error_items: list[Hashable] | None = None
