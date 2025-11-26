from typing import Any, Callable, Dict, List

from core.domain import Budget, Transaction


class BudgetService:
    def __init__(self, validators: List[Callable], calculators: List[Callable]):
        self.validators = validators
        self.calculators = calculators

    def monthly_report(
        self, budgets: tuple[Budget, ...], trans: tuple[Transaction, ...]
    ) -> Dict[str, Any]:
        """
        Calculates status for each budget.
        Using composition if applicable, or just pure logic.
        """
        report = {}
        for b in budgets:
            # Simple logic: filter trans for budget category -> sum
            spent = sum(
                abs(t.amount) for t in trans if t.cat_id == b.cat_id and t.amount < 0
            )
            status = "OK" if spent <= b.limit else "OVER"
            report[b.id] = {"limit": b.limit, "spent": spent, "status": status}
        return report


class ReportService:
    def __init__(self, aggregators: Dict[str, Callable]):
        self.aggregators = aggregators

    def category_report(
        self, cat_id: str, trans: tuple[Transaction, ...]
    ) -> Dict[str, Any]:
        """
        Aggregates data for a category.
        """
        # Example aggregation: total spent, count
        filtered = [t for t in trans if t.cat_id == cat_id and t.amount < 0]
        total = sum(abs(t.amount) for t in filtered)
        count = len(filtered)

        return {"cat_id": cat_id, "total_expense": total, "transaction_count": count}

    async def expenses_by_month(
        self, trans: List[Transaction], months: List[str]
    ) -> Dict[str, int]:
        """
        Async calculation of expenses for multiple months concurrently (conceptually).
        Since this is CPU bound in Python, true parallelism requires multiprocessing,
        but asyncio is fine for the requirement.
        """
        import asyncio

        async def calc_month(m: str) -> int:
            # Simulate I/O or delay
            await asyncio.sleep(0.01)
            # Filter by month string (YYYY-MM) in ts
            return sum(
                abs(t.amount) for t in trans if t.ts.startswith(m) and t.amount < 0
            )

        tasks = [calc_month(m) for m in months]
        results = await asyncio.gather(*tasks)

        return dict(zip(months, results))
