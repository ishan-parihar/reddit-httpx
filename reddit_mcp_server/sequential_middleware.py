import asyncio

_lock = asyncio.Lock()

async def sequential_guard():
    """Acquire the global tool lock. Use as: async with sequential_guard(): ..."""
    return _lock

class SequentialToolMiddleware:
    def __init__(self):
        self._lock = asyncio.Lock()

    async def __aenter__(self):
        await self._lock.acquire()
        return self

    async def __aexit__(self, *args):
        self._lock.release()

middleware = SequentialToolMiddleware()
