import asyncio
from typing import Any, Callable, Dict, List, Set, Optional

try:
    from lunarphase._lunarphase_rs import BatchAggregator as RustBatchAggregator
    HAS_RUST_BATCHER = True
except ImportError:
    HAS_RUST_BATCHER = False

class DeferredAutoBatcher:
    """
    Deferred Auto-Batcher resolving N+1 Query Problem via event loop micro-task flushing.
    """
    def __init__(self, batch_fetch_fn: Callable[[List[Any]], Any]):
        self.batch_fetch_fn = batch_fetch_fn
        self.pending_keys: Set[Any] = set()
        self.futures: Dict[Any, asyncio.Future] = {}
        self._scheduled: bool = False

    async def load(self, key: Any) -> Any:
        if key in self.futures:
            return await self.futures[key]

        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self.futures[key] = fut
        self.pending_keys.add(key)

        if not self._scheduled:
            self._scheduled = True
            loop.call_soon(self._flush_batch)

        return await fut

    def _flush_batch(self):
        keys_to_fetch = list(self.pending_keys)
        self.pending_keys.clear()
        self._scheduled = False

        if keys_to_fetch:
            asyncio.create_task(self._execute_batch(keys_to_fetch))

    async def _execute_batch(self, keys: List[Any]):
        try:
            results: Dict[Any, Any] = await self.batch_fetch_fn(keys)
            for key in keys:
                res = results.get(key, [])
                if key in self.futures and not self.futures[key].done():
                    self.futures[key].set_result(res)
        except Exception as exc:
            for key in keys:
                if key in self.futures and not self.futures[key].done():
                    self.futures[key].set_exception(exc)
