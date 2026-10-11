from __future__ import annotations

import random
from datetime import timedelta


def jittered_backoff(attempt: int, *, base: float = 0.5, cap: float = 30.0) -> timedelta:
    """Exponential backoff with full jitter for 429 / transient errors."""
    exp = min(cap, base * (2 ** max(0, attempt)))
    return timedelta(seconds=random.uniform(0, exp))
