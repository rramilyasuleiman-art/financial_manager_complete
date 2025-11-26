from collections import defaultdict
from typing import Callable, Iterable, Iterator, Tuple

from core.domain import Category, Transaction


def iter_transactions(
    trans: Tuple[Transaction, ...], pred: Callable[[Transaction], bool] = None
) -> Iterable[Transaction]:
    """
    Generator that yields transactions, optionally filtered by a predicate.
    """
    for t in trans:
        if pred is None or pred(t):
            yield t


def lazy_top_categories(
    trans: Iterable[Transaction], cats: Tuple[Category, ...], k: int
) -> Iterator[Tuple[str, int]]:
    """
    Lazily computes top k categories by expense.
    Actually, to sort top K we generally need to see all data (unless using approximate streaming algos).
    But we can consume the iterator fully here (materialization step) or yield incrementally if the logic allows.
    The prompt says "lazy top categories... streaming count".
    Let's consume the stream into a dict, then sort.
    This is "lazy processing" until the sort happens.
    """
    expenses = defaultdict(int)

    # Consume the iterator
    for t in trans:
        if t.amount < 0:
            expenses[t.cat_id] += abs(t.amount)

    # Now sort and take top K
    # Convert cat_id to name for better output
    cat_map = {c.id: c.name for c in cats}

    sorted_expenses = sorted(expenses.items(), key=lambda x: x[1], reverse=True)

    for cat_id, amount in sorted_expenses[:k]:
        yield (cat_map.get(cat_id, cat_id), amount)
