from typing import Callable, Dict, List

from core.domain import Event


class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}

    def subscribe(self, name: str, handler: Callable[[Event], None]):
        if name not in self._subscribers:
            self._subscribers[name] = []
        self._subscribers[name].append(handler)

    def publish(self, event: Event):
        if event.name in self._subscribers:
            for handler in self._subscribers[event.name]:
                handler(event)


# Subscribers (Pure functions logic-wise, but usually side-effecting in "subscribe" context or returning new state)
# The prompt says: "Subscribers (pure): update account balance, check budget, create notifications"
# If they are pure, they should return a new state.
# But `subscribe` takes a handler.
# Usually in FRP/EventBus, handlers are side-effecting OR the bus manages state transition.
# Prompt: "def subscribe(self, name:str, handler: Callable[[Event, dict], dict]): ..."
# It seems the handler receives Event + Current State (dict) and returns New State (dict).


class StateEventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event, Dict], Dict]]] = {}

    def subscribe(self, name: str, handler: Callable[[Event, Dict], Dict]):
        if name not in self._subscribers:
            self._subscribers[name] = []
        self._subscribers[name].append(handler)

    def publish(self, event: Event, state: Dict) -> Dict:
        """
        Publishes event and runs all handlers sequentially, threading the state.
        """
        current_state = state
        if event.name in self._subscribers:
            for handler in self._subscribers[event.name]:
                current_state = handler(event, current_state)
        return current_state


# Handlers


def on_transaction_added(event: Event, state: Dict) -> Dict:
    """
    Updates the list of transactions and potentially account balances in the state.
    Payload: {"transaction": Transaction}
    """
    t = event.payload["transaction"]

    # Update transactions list
    trans = state.get("transactions", ())
    new_trans = trans + (t,)

    # Update account balance (simplified, if we store balances in state)
    # The Seed accounts are immutable, so we replace the account list with updated one.
    accs = state.get("accounts", ())
    new_accs = tuple(
        acc
        if acc.id != t.account_id
        # Updating balance assuming it's mutable or replacing it.
        # Account is frozen, so we replace.
        # Note: Account balance in seed was just initial. Let's assume we update it here.
        # account_balance function calculates from scratch, but if we want to update the cached balance:
        else acc.__class__(acc.id, acc.name, acc.balance + t.amount, acc.currency)
        for acc in accs
    )

    return {**state, "transactions": new_trans, "accounts": new_accs}


def check_budget_handler(event: Event, state: Dict) -> Dict:
    """
    Checks if the added transaction causes a budget overflow.
    If so, adds a notification (alert) to state.
    """
    t = event.payload["transaction"]
    budgets = state.get("budgets", ())
    trans = state.get(
        "transactions", ()
    )  # This includes the new one if run after on_transaction_added

    alerts = state.get("alerts", [])

    # We need to find relevant budget
    relevant_budgets = [b for b in budgets if b.cat_id == t.cat_id]

    new_alerts = list(alerts)
    for b in relevant_budgets:
        # Calculate spent for this budget category
        spent = sum(
            abs(tx.amount) for tx in trans if tx.cat_id == b.cat_id and tx.amount < 0
        )
        if spent > b.limit:
            new_alerts.append(
                f"Budget Alert: {b.id} exceeded! Limit {b.limit}, Spent {spent}"
            )

    return {**state, "alerts": new_alerts}
