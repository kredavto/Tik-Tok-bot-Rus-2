from app.workers.scheduler import PeriodicDispatch, dispatch_once


class FakeRedis:
    def __init__(self) -> None:
        self.keys: set[str] = set()
        self.deleted: list[str] = []

    async def set(
        self,
        key: str,
        value: str,
        *,
        ex: int,
        nx: bool,
    ) -> bool:
        assert value
        assert ex > 0
        assert nx is True
        if key in self.keys:
            return False
        self.keys.add(key)
        return True

    async def delete(self, key: str) -> int:
        self.deleted.append(key)
        if key not in self.keys:
            return 0
        self.keys.remove(key)
        return 1


async def test_scheduler_dispatches_each_task_once_per_lease() -> None:
    queued: list[str] = []
    dispatches = (
        PeriodicDispatch("subscriptions", 60, lambda: queued.append("subscriptions")),
        PeriodicDispatch("retention", 3600, lambda: queued.append("retention")),
    )
    redis = FakeRedis()

    first = await dispatch_once(redis, dispatches)  # type: ignore[arg-type]
    second = await dispatch_once(redis, dispatches)  # type: ignore[arg-type]

    assert first == ["subscriptions", "retention"]
    assert second == []
    assert queued == ["subscriptions", "retention"]


async def test_scheduler_releases_lease_when_enqueue_fails() -> None:
    attempts = 0

    def enqueue() -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("broker unavailable")

    redis = FakeRedis()
    dispatches = (PeriodicDispatch("subscriptions", 60, enqueue),)

    try:
        await dispatch_once(redis, dispatches)  # type: ignore[arg-type]
    except RuntimeError:
        pass
    else:
        raise AssertionError("enqueue failure must propagate")

    assert redis.deleted == ["scheduler:lease:subscriptions"]
    assert await dispatch_once(redis, dispatches) == ["subscriptions"]  # type: ignore[arg-type]
    assert attempts == 2
