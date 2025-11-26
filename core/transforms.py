import json
from functools import reduce
from typing import Any, Dict, Tuple

from core.domain import Account, Budget, Category, Transaction
from core.ftypes import Either, Maybe


def load_seed(
    path: str,
) -> Tuple[
    Tuple[Account, ...],
    Tuple[Category, ...],
    Tuple[Transaction, ...],
    Tuple[Budget, ...],
]:
    with open(path, "r") as f:
        data = json.load(f)

    accounts = tuple(Account(**item) for item in data["accounts"])
    categories = tuple(Category(**item) for item in data["categories"])
    transactions = tuple(Transaction(**item) for item in data["transactions"])
    budgets = tuple(Budget(**item) for item in data["budgets"])

    return accounts, categories, transactions, budgets


def add_transaction(
    trans: Tuple[Transaction, ...], t: Transaction
) -> Tuple[Transaction, ...]:
    return trans + (t,)


def update_budget(
    budgets: Tuple[Budget, ...], bid: str, new_limit: int
) -> Tuple[Budget, ...]:
    return tuple(
        b
        if b.id != bid
        else Budget(id=b.id, cat_id=b.cat_id, limit=new_limit, period=b.period)
        for b in budgets
    )


def account_balance(trans: Tuple[Transaction, ...], acc_id: str) -> int:
    return reduce(
        lambda acc, t: acc + t.amount,
        filter(lambda t: t.account_id == acc_id, trans),
        0,
    )


def by_category(cat_id: str):
    def _filter(t: Transaction) -> bool:
        return t.cat_id == cat_id

    return _filter


def by_date_range(start: str, end: str):
    def _filter(t: Transaction) -> bool:
        return start <= t.ts <= end

    return _filter


def by_amount_range(min_val: int, max_val: int):
    def _filter(t: Transaction) -> bool:
        return min_val <= abs(t.amount) <= max_val

    return _filter


# Lab 4 Functions


def safe_category(cats: Tuple[Category, ...], cat_id: str) -> Maybe[Category]:
    found = next((c for c in cats if c.id == cat_id), None)
    return Maybe(found)


def validate_transaction(
    t: Transaction, accs: Tuple[Account, ...], cats: Tuple[Category, ...]
) -> Either[Dict[str, str], Transaction]:
    # Check account exists
    if not any(a.id == t.account_id for a in accs):
        return Either.left({"error": f"Account {t.account_id} not found"})

    # Check category exists
    if safe_category(cats, t.cat_id).is_present() is False:
        return Either.left({"error": f"Category {t.cat_id} not found"})

    return Either.right(t)


def check_budget(
    b: Budget, trans: Tuple[Transaction, ...]
) -> Either[Dict[str, Any], Budget]:
    # Sum expenses for this budget's category (and children?)
    # Simplification: just direct category matches for now, or assume flattened list passed in?
    # The prompt implies a check. Let's filter by category.
    # Note: in a real app we'd handle hierarchy here or rely on pre-filtered/aggregated data.
    # Let's just check exact category match for simplicity unless recursion is required here too.

    spent = sum(abs(t.amount) for t in trans if t.cat_id == b.cat_id and t.amount < 0)

    if spent > b.limit:
        return Either.left(
            {
                "error": "Over Budget",
                "budget_id": b.id,
                "limit": b.limit,
                "spent": spent,
            }
        )
    return Either.right(b)
