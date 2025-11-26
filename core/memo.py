from functools import lru_cache
from typing import Tuple

from core.domain import Transaction

# To make caching work with immutable args, they must be hashable.
# Tuples of Frozen DataClasses are hashable.


@lru_cache
def forecast_expenses(cat_id: str, trans: Tuple[Transaction, ...], period: int) -> int:
    """
    Simulates a heavy calculation to forecast expenses.
    Calculates average expense for the category over the provided transactions,
    then multiplies by period.
    """
    # Simulate work
    import time

    time.sleep(0.1)  # Simulate 100ms delay per call to make it "expensive"

    filtered = [t for t in trans if t.cat_id == cat_id and t.amount < 0]
    if not filtered:
        return 0

    total = sum(abs(t.amount) for t in filtered)
    avg = total / len(filtered)
    return int(avg * period)
