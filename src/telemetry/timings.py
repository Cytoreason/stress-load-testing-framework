from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class Timing:
    name: str
    elapsed_ms: int


@contextmanager
def time_block(name: str) -> Iterator[Timing]:
    start = time.perf_counter()
    timing = Timing(name=name, elapsed_ms=0)
    try:
        yield timing
    finally:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        object.__setattr__(timing, "elapsed_ms", elapsed_ms)
