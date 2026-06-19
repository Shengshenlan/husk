"""Asyncio scheduler — registers + runs all periodic background tasks."""

from __future__ import annotations

import asyncio
import contextlib

from loguru import logger

from husk.core.config import settings
from husk.core.deps import docker_client


class Scheduler:
    def __init__(self) -> None:
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        if settings.auto_stop_enabled:
            self._tasks.append(
                asyncio.create_task(
                    self._loop("auto_stop", self._auto_stop_tick, settings.auto_stop_check_interval)
                )
            )
        self._tasks.append(
            asyncio.create_task(
                self._loop("reaper", self._reaper_tick, settings.reaper_interval)
            )
        )
        logger.info("scheduler started ({} tasks)", len(self._tasks))

    async def stop(self) -> None:
        for t in self._tasks:
            t.cancel()
        for t in self._tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await t
        self._tasks.clear()

    async def _loop(self, name: str, fn, interval: int) -> None:
        while True:
            try:
                await fn()
            except Exception:
                logger.exception("scheduler task {} crashed", name)
            await asyncio.sleep(interval)

    async def _auto_stop_tick(self) -> None:
        from husk.sandbox.auto_stop import tick

        await tick(docker_client())

    async def _reaper_tick(self) -> None:
        from husk.sandbox.reaper import reconcile

        await reconcile(docker_client())


_scheduler: Scheduler | None = None


async def start_scheduler() -> Scheduler:
    global _scheduler  # noqa: PLW0603
    _scheduler = Scheduler()
    await _scheduler.start()
    return _scheduler


async def stop_scheduler(scheduler: Scheduler) -> None:
    await scheduler.stop()
