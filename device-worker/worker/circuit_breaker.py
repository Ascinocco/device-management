"""Simple in-process circuit breaker — no external dependencies."""

import time
from enum import Enum


class State(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Wraps async callables with fail-fast behaviour.

    Args:
        failure_threshold: consecutive failures before opening.
        recovery_timeout: seconds to wait before trying half-open.
        name: label for logging.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        name: str = "circuit",
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name

        self._state = State.CLOSED
        self._failure_count = 0
        self._last_failure_time: float = 0.0

    @property
    def state(self) -> State:
        if self._state == State.OPEN:
            if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                self._state = State.HALF_OPEN
        return self._state

    async def call(self, func, *args, **kwargs):
        """Execute *func* through the breaker.

        Raises ``CircuitOpenError`` when the circuit is open.
        """
        current = self.state

        if current == State.OPEN:
            raise CircuitOpenError(
                f"Circuit '{self.name}' is open — failing fast"
            )

        try:
            result = await func(*args, **kwargs)
        except Exception:
            self._record_failure()
            raise

        self._record_success()
        return result

    # -- internals --------------------------------------------------

    def _record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self.failure_threshold:
            self._state = State.OPEN

    def _record_success(self) -> None:
        self._failure_count = 0
        self._state = State.CLOSED


class CircuitOpenError(Exception):
    """Raised when a call is attempted while the circuit is open."""
