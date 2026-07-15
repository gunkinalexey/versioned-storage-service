from typing import Any, Optional


class BaseError(Exception):
    def __init__(self, message: Optional[str] = None, **kwargs: Any) -> None:
        self.message = message or "Internal Server Error"
        self.extra = dict(kwargs)
        super().__init__(self.message)

    @property
    def error_type(self) -> str:
        return self.__class__.__name__
