"""Retry and circuit breaker tests — pure logic, no I/O."""

import pytest

from worker.circuit_breaker import CircuitBreaker, CircuitOpenError, State


class TestCircuitBreaker:
    @pytest.mark.asyncio
    async def test_starts_closed(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=10, name="test")
        assert cb.state == State.CLOSED

    @pytest.mark.asyncio
    async def test_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=10, name="test")

        async def failing():
            raise RuntimeError("boom")

        for _ in range(2):
            with pytest.raises(RuntimeError):
                await cb.call(failing)

        assert cb.state == State.OPEN

    @pytest.mark.asyncio
    async def test_open_circuit_raises_immediately(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=999, name="test")

        async def failing():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            await cb.call(failing)

        with pytest.raises(CircuitOpenError):
            await cb.call(failing)

    @pytest.mark.asyncio
    async def test_success_resets_failure_count(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=10, name="test")

        async def failing():
            raise RuntimeError("boom")

        async def succeeding():
            return "ok"

        # 2 failures (below threshold)
        for _ in range(2):
            with pytest.raises(RuntimeError):
                await cb.call(failing)

        # 1 success resets
        result = await cb.call(succeeding)
        assert result == "ok"
        assert cb._failure_count == 0

        # 2 more failures still below threshold
        for _ in range(2):
            with pytest.raises(RuntimeError):
                await cb.call(failing)

        assert cb.state == State.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_after_recovery_timeout(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0, name="test")

        async def failing():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            await cb.call(failing)

        # recovery_timeout=0 means it transitions immediately
        assert cb.state == State.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_success_closes(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0, name="test")

        async def failing():
            raise RuntimeError("boom")

        async def succeeding():
            return "ok"

        with pytest.raises(RuntimeError):
            await cb.call(failing)

        # Should be half-open now (recovery_timeout=0)
        result = await cb.call(succeeding)
        assert result == "ok"
        assert cb.state == State.CLOSED
