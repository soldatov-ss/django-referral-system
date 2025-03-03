import asyncio
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import TypeVar, List, Dict

T = TypeVar('T')


def sync_to_async(method: Callable[..., T]) -> Callable[..., Coroutine]:
    @wraps(method)
    async def async_wrapper(self, *args: List[any], **kwargs: Dict[str, any]) -> Coroutine:
        if not asyncio.iscoroutinefunction(method):
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: method(self, *args, **kwargs))

        return await method(self, *args, **kwargs)

    return async_wrapper
