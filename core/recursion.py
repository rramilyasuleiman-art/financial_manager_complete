from typing import Tuple

from core.domain import Category, Transaction


def flatten_categories(
    cats: Tuple[Category, ...], root_id: str | None = None
) -> Tuple[Category, ...]:
    """
    Recursively finds all categories starting from a root (or None for top-level).
    If root_id is provided, it returns that category and all its descendants.
    If root_id is None, it returns all categories (conceptually descendants of a virtual root).
    Wait, the task says: flatten_categories(cats, root:str).
    Let's assume root is the ID of the category we want to start flattening from.
    """
    if root_id is None:
        # Return all top level categories and their children
        roots = [c for c in cats if c.parent_id is None]
        result = []
        for r in roots:
            result.extend(flatten_categories(cats, r.id))
        return tuple(result)

    # Find the root category object
    # This is inefficient O(N) search in recursion, but fits "recursive function" requirement.
    root_cat = next((c for c in cats if c.id == root_id), None)
    if not root_cat:
        return ()

    children = [c for c in cats if c.parent_id == root_id]

    # Recursive step
    flat_children = []
    for child in children:
        flat_children.extend(flatten_categories(cats, child.id))

    return (root_cat,) + tuple(flat_children)


def sum_expenses_recursive(
    cats: Tuple[Category, ...], trans: Tuple[Transaction, ...], root_id: str
) -> int:
    """
    Sums expenses for a category and all its subcategories recursively.
    """
    # 1. Sum expenses for current category directly
    current_expenses = sum(t.amount for t in trans if t.cat_id == root_id)

    # 2. Find children
    children = [c for c in cats if c.parent_id == root_id]

    # 3. Recursive step
    children_expenses = sum(
        sum_expenses_recursive(cats, trans, child.id) for child in children
    )

    return current_expenses + children_expenses
