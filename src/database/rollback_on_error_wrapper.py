import functools
from typing import Any, Callable


def rollback_on_error(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return await func(self, *args, **kwargs)
        except Exception:
            await self.session.rollback()
            raise

    return wrapper
