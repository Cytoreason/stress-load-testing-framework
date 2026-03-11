"""
Synchronous timing context manager (used in Pytest smoke tests).

For Locust load runs, use ``locust_plugins.users.playwright.event()`` instead,
which wires timing into Locust's statistics engine automatically.
"""
from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator


@dataclass
class Timing:
    name: str
    elapsed_ms: int = 0


@contextmanager
def time_block(name: str) -> Iterator[Timing]:
    """
    Measure elapsed wall-clock time for a code block.

    Usage::

        with time_block("UI_Open_Programs_Page") as t:
            # do something
        print(t.elapsed_ms)
    """
    start = time.perf_counter()
    timing = Timing(name=name)
    try:
        yield timing
    finally:
        timing.elapsed_ms = int((time.perf_counter() - start) * 1000)
