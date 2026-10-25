import logging
import time

from metrics import CIRCUIT_OPEN

log = logging.getLogger(__name__)


class CircuitOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(self, name, threshold=5, cooldown=30):
        self.name = name
        self.threshold = threshold
        self.cooldown = cooldown
        self.failures = 0
        self.opened_at = None
        CIRCUIT_OPEN.labels(name).set(0)

    def check(self):
        if self.opened_at is None:
            return
        waited = time.monotonic() - self.opened_at
        if waited < self.cooldown:
            raise CircuitOpenError(f"circuit open, {self.name} failing (retry in {self.cooldown - waited:.0f}s)")
        # half-open: let one call through, and a single failure reopens it
        self.opened_at = None
        self.failures = self.threshold - 1
        CIRCUIT_OPEN.labels(self.name).set(0)

    def record_success(self):
        self.failures = 0

    def record_failure(self):
        self.failures += 1
        if self.failures >= self.threshold and self.opened_at is None:
            self.opened_at = time.monotonic()
            CIRCUIT_OPEN.labels(self.name).set(1)
            log.warning("%s circuit opened after %d failures", self.name, self.failures)
