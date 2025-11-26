from typing import Dict, Any, Tuple
from core.domain import Account, Transaction, Category, Budget

# Helper functions to update state immutably

def update_account_balance(state: Dict[str, Any], acc_id: str, new_balance: int) -> Dict[str, Any]:
    accounts = state.get("accounts", ())
    new_accounts = tuple(
        Account(id=a.id, name=a.name, balance=new_balance, currency=a.currency) 
        if a.id == acc_id else a 
        for a in accounts
    )
    return {**state, "accounts": new_accounts}

def create_transaction(state: Dict[str, Any], t: Transaction) -> Dict[str, Any]:
    transactions = state.get("transactions", ())
    new_transactions = transactions + (t,)
    return {**state, "transactions": new_transactions}

def update_transaction(state: Dict[str, Any], t_id: str, new_data: Dict) -> Dict[str, Any]:
    transactions = state.get("transactions", ())
    new_transactions = tuple(
        Transaction(
            id=t.id,
            account_id=new_data.get("account_id", t.account_id),
            cat_id=new_data.get("cat_id", t.cat_id),
            amount=int(new_data.get("amount", t.amount)),
            ts=new_data.get("ts", t.ts),
            note=new_data.get("note", t.note)
        ) if t.id == t_id else t
        for t in transactions
    )
    return {**state, "transactions": new_transactions}

def delete_transaction(state: Dict[str, Any], t_id: str) -> Dict[str, Any]:
    transactions = state.get("transactions", ())
    new_transactions = tuple(t for t in transactions if t.id != t_id)
    return {**state, "transactions": new_transactions}
