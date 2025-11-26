import asyncio
import datetime
import time
import sys
import os

# Add project root to sys.path to allow imports from core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st

from core.domain import Transaction
from core.frp import Event, StateEventBus, check_budget_handler, on_transaction_added
from core.lazy import iter_transactions, lazy_top_categories
from core.memo import forecast_expenses
from core.recursion import flatten_categories, sum_expenses_recursive
from core.service import BudgetService, ReportService
from core.transforms import (
    by_amount_range,
    by_category,
    check_budget,
    load_seed,
    validate_transaction,
)
from core.auth import verify_credentials, get_user_role, get_user_accounts
from core.state_utils import update_account_balance, update_transaction, delete_transaction, create_transaction

# Configuration
st.set_page_config(page_title="Financial Manager", layout="wide")

# --- Authentication ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None

if not st.session_state.logged_in:
    st.title("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if verify_credentials(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = get_user_role(username)
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password")
    st.stop()

# Sidebar Logout
st.sidebar.write(f"Logged in as: **{st.session_state.username}** ({st.session_state.role})")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.rerun()

# Load Data (Simulated Global State for now, usually would be in session state)
if "state" not in st.session_state:
    accs, cats, trans, buds = load_seed("data/seed.json")
    st.session_state.state = {
        "accounts": accs,
        "categories": cats,
        "transactions": trans,
        "budgets": buds,
        "alerts": [],
    }

    # Init Event Bus
    bus = StateEventBus()
    bus.subscribe("TRANSACTION_ADDED", on_transaction_added)
    bus.subscribe("TRANSACTION_ADDED", check_budget_handler)
    st.session_state.bus = bus

state = st.session_state.state

# Filter Data based on User Role
allowed_accounts = get_user_accounts(st.session_state.username)

if allowed_accounts is None:
    # Admin sees all
    accounts = state["accounts"]
    transactions = state["transactions"]
else:
    # User sees only their accounts
    accounts = tuple(a for a in state["accounts"] if a.id in allowed_accounts)
    transactions = tuple(t for t in state["transactions"] if t.account_id in allowed_accounts)

categories = state["categories"]
budgets = state["budgets"] # Budgets might need filtering too but for now shared or all visible
alerts = state["alerts"]

# Sidebar Menu
# If Admin, show special "Manage Users"
menu_options = [
    "Overview",
    "Data",
    "Functional Core",
    "Pipelines",
    "Async/FRP",
    "Reports",
    "Tests",
    "About",
]
if st.session_state.role == "admin":
    menu_options.insert(1, "Manage Users")

menu = st.sidebar.radio("Menu", menu_options)

if menu == "Overview":
    st.title("Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Accounts", len(accounts))
    with col2:
        st.metric("Categories", len(categories))
    with col3:
        st.metric("Transactions", len(transactions))
    with col4:
        total_balance = sum(a.balance for a in accounts)
        st.metric("Total Balance", f"${total_balance}")

    st.subheader("Your Accounts")
    for acc in accounts:
        st.write(f"- **{acc.name}** (ID: {acc.id}): {acc.balance} {acc.currency}")

    st.subheader("Recent Transactions")
    # Show 100 if requested, or default
    # If Admin, show 100 or all? The prompt says "View ALL user data... access full 100-transaction history".
    # If Standard User, "display a Transaction History table containing exactly 100 dummy transaction records".
    # Let's show all available in the context (which is filtered by role).
    
    st.dataframe(transactions)
    
elif menu == "Manage Users":
    st.title("Admin: Manage Users")
    if st.session_state.role != "admin":
        st.error("Access Denied")
        st.stop()

    # Select User to Manage
    target_user = st.selectbox("Select User", ["user1", "user2"])
    target_acc_ids = get_user_accounts(target_user)
    
    st.subheader(f"Managing {target_user}")
    
    # 1. Manage Accounts (Balance)
    target_accounts = [a for a in state["accounts"] if a.id in target_acc_ids]
    
    for acc in target_accounts:
        with st.expander(f"Account: {acc.name} ({acc.id})"):
            new_bal = st.number_input(f"Balance for {acc.id}", value=acc.balance, key=f"bal_{acc.id}")
            if st.button(f"Update Balance {acc.id}"):
                st.session_state.state = update_account_balance(st.session_state.state, acc.id, new_bal)
                st.success("Balance Updated")
                st.rerun()

    # 2. Manage Transactions
    st.markdown("### Transactions")
    target_trans = [t for t in state["transactions"] if t.account_id in target_acc_ids]
    st.dataframe(target_trans)
    
    with st.expander("Edit Transaction"):
        t_id_to_edit = st.selectbox("Select Transaction ID", [t.id for t in target_trans])
        if t_id_to_edit:
            curr_t = next(t for t in target_trans if t.id == t_id_to_edit)
            edit_amt = st.number_input("Amount", value=curr_t.amount, key="edit_amt")
            edit_note = st.text_input("Note", value=curr_t.note, key="edit_note")
            col_upd, col_del = st.columns(2)
            if col_upd.button("Update Transaction"):
                st.session_state.state = update_transaction(st.session_state.state, t_id_to_edit, {"amount": edit_amt, "note": edit_note})
                st.success("Transaction Updated")
                st.rerun()
            if col_del.button("Delete Transaction"):
                st.session_state.state = delete_transaction(st.session_state.state, t_id_to_edit)
                st.success("Transaction Deleted")
                st.rerun()

    with st.expander("Create Transaction"):
        new_acc_id = st.selectbox("Account", [a.id for a in target_accounts])
        new_amt = st.number_input("Amount", 0)
        new_note = st.text_input("Note", "New Tx")
        if st.button("Create"):
             # Generate ID
             import uuid
             new_id = f"tx_{len(state['transactions'])}_{uuid.uuid4().hex[:4]}"
             new_t = Transaction(new_id, new_acc_id, "cat_general", int(new_amt), datetime.datetime.now().isoformat(), new_note)
             st.session_state.state = create_transaction(st.session_state.state, new_t)
             st.success("Transaction Created")
             st.rerun()

elif menu == "Data":
    st.title("Data Inspection")
    st.subheader("Accounts")
    st.table(accounts)
    st.subheader("Categories")
    st.table(categories)
    st.subheader("Budgets")
    st.table(budgets)
    st.subheader("Transactions")
    st.dataframe(transactions)

elif menu == "About":
    st.title("About")
    st.write("Financial Manager Project")
    st.write("Team: 2-3 Students")
    st.write("Stack: Python 3.11+, Streamlit, Pytest")

elif menu == "Functional Core":
    st.title("Functional Core")
    st.subheader("Filter Closures")

    # Filter Controls
    with st.expander("Filters", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            selected_cat = st.selectbox(
                "Category", ["All"] + [c.name for c in categories]
            )
        with col2:
            min_amt = st.number_input("Min Amount (Abs)", 0, 10000, 0)
            max_amt = st.number_input("Max Amount (Abs)", 0, 100000, 10000)

    # Apply Filters
    filtered_trans = transactions

    if selected_cat != "All":
        cat_id = next(c.id for c in categories if c.name == selected_cat)
        filtered_trans = tuple(filter(by_category(cat_id), filtered_trans))

    filtered_trans = tuple(filter(by_amount_range(min_amt, max_amt), filtered_trans))

    st.write(f"Filtered Transactions: {len(filtered_trans)}")
    st.dataframe(filtered_trans)

    st.subheader("Transaction Validation (Either/Maybe)")
    with st.form("validate_tx"):
        v_acc = st.text_input("Account ID", "acc1")
        v_cat = st.text_input("Category ID", "cat_food")
        v_amt = st.number_input("Amount", step=100)
        submitted = st.form_submit_button("Validate")

        if submitted:
            # Create a dummy transaction
            t_cand = Transaction("new", v_acc, v_cat, int(v_amt), "2023-01-01", "cand")

            result = validate_transaction(t_cand, accounts, categories)

            if result.is_right():
                st.success("Transaction is Valid!")

                # Check budgets if valid
                # Simple check against all budgets
                for b in budgets:
                    res_b = check_budget(b, transactions + (t_cand,))
                    if res_b.is_left():
                        st.warning(
                            f"Budget Alert: {res_b.unwrap()['error']} (Limit: {res_b.unwrap()['limit']}, Spent: {res_b.unwrap()['spent']})"
                        )
                    else:
                        pass  # Budget ok
            else:
                st.error(f"Validation Failed: {result.unwrap()['error']}")

elif menu == "Pipelines":
    st.title("Pipelines & Recursion")

    st.subheader("Lazy Top Categories")

    k = st.slider("Top K", 1, 10, 3)

    if st.button("Compute Top K (Lazy)"):
        # Create an iterator
        tx_iter = iter_transactions(transactions)

        # Compute
        top_k = list(lazy_top_categories(tx_iter, categories, k))

        st.write("Top Categories by Expense:")
        for name, amount in top_k:
            st.write(f"**{name}**: {amount}")

    st.divider()

    st.subheader("Recursive Expense Report")

    # Select root category
    root_cats = [c for c in categories if c.parent_id is None]
    selected_root = st.selectbox("Select Root Category", [c.name for c in root_cats])

    if selected_root:
        root_id = next(c.id for c in root_cats if c.name == selected_root)

        # Flatten
        flat_cats = flatten_categories(categories, root_id)
        st.write(f"Flattened Hierarchy for {selected_root}:")
        st.write(" > ".join([c.name for c in flat_cats]))

        # Recursive Sum
        total_expenses = sum_expenses_recursive(categories, transactions, root_id)
        st.metric(f"Total Expenses for {selected_root} (Tree)", f"{total_expenses}")

elif menu == "Async/FRP":
    st.title("Async / FRP")
    st.subheader("Event Bus Simulation")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Add Transaction (Event)")
        with st.form("event_tx"):
            amt = st.number_input("Amount", -1000, 1000, -100)
            cat = st.selectbox("Category", [c.name for c in categories])
            sub = st.form_submit_button("Publish TRANSACTION_ADDED")

            if sub:
                cat_id = next(c.id for c in categories if c.name == cat)
                # Pick random account
                acc_id = accounts[0].id

                new_t = Transaction(
                    id=f"tx_evt_{len(transactions)}",
                    account_id=acc_id,
                    cat_id=cat_id,
                    amount=amt,
                    ts=datetime.datetime.now().isoformat(),
                    note="Event TX",
                )

                evt = Event(
                    id=f"evt_{len(transactions)}",
                    ts=datetime.datetime.now().isoformat(),
                    name="TRANSACTION_ADDED",
                    payload={"transaction": new_t},
                )

                # Publish and Update State
                st.session_state.state = st.session_state.bus.publish(
                    evt, st.session_state.state
                )
                st.success("Event Published!")
                st.rerun()

    with col2:
        st.markdown("### Live Alerts")
        if alerts:
            for a in alerts:
                st.error(a)
        else:
            st.info("No alerts yet.")

    st.subheader("Live State Monitor")
    st.write(f"Total Transactions: {len(transactions)}")
    st.write("Accounts Balance (Updated via Event):")
    for a in accounts:
        st.write(f"{a.name}: {a.balance}")

    st.divider()
    st.subheader("Async Aggregation (Lab 8)")

    if st.button("Run Async Monthly Report"):
        rs = ReportService({})
        # Extract unique months from transactions
        months = sorted(list(set(t.ts[:7] for t in transactions)))

        # Async run
        async def run_report():
            return await rs.expenses_by_month(transactions, months)

        try:
            # streamlit usually handles async natively or we run loop
            res = asyncio.run(run_report())
            st.write("Expenses by Month (Calculated Async):")
            st.bar_chart(res)
        except Exception as e:
            # Fallback if loop is already running (Streamlit logic depends on version)
            # st.write(f"Async Error: {e}")
            # If asyncio.run fails due to existing loop, just await if inside async func?
            # Streamlit script is sync.
            st.error(f"Could not run async: {e}")


elif menu == "Reports":
    st.title("Reports")

    # Lab 7 Services
    st.subheader("Services & Composition")

    bs = BudgetService([], [])
    rs = ReportService({})

    tab1, tab2 = st.tabs(["Budget Report", "Category Report"])

    with tab1:
        if st.button("Generate Budget Report"):
            report = bs.monthly_report(budgets, transactions)
            st.json(report)

    with tab2:
        c_name = st.selectbox("Category", [c.name for c in categories], key="rep_cat")
        if st.button("Generate Category Report"):
            cid = next(c.id for c in categories if c.name == c_name)
            rep = rs.category_report(cid, transactions)
            st.json(rep)

    st.divider()

    st.subheader("Forecast (Cached)")

    cat_name = st.selectbox(
        "Category for Forecast", [c.name for c in categories], key="fc_cat"
    )
    periods = st.slider("Periods to forecast", 1, 12, 3)

    if st.button("Calculate Forecast"):
        cat_id = next(c.id for c in categories if c.name == cat_name)

        # Measure time
        start = time.perf_counter()
        prediction = forecast_expenses(cat_id, transactions, periods)
        end = time.perf_counter()

        elapsed_ms = (end - start) * 1000

        st.metric("Forecasted Expense", f"{prediction}")
        st.caption(f"Calculation time: {elapsed_ms:.2f} ms")
        st.info(
            "Try clicking again to see the cache effect (time should drop close to 0)."
        )

elif menu == "Tests":
    st.title("Tests")
    st.write("This section displays information about the project's test suite.")
    st.info("Tests are implemented using `pytest`.")
    
    st.markdown("""
    ### Available Test Modules:
    - `tests/test_lab1.py`: Domain & Transforms
    - `tests/test_lab2.py`: Recursion & Filters
    - `tests/test_lab3.py`: Memoization
    - `tests/test_lab4.py`: Validation (Maybe/Either)
    - `tests/test_lab5.py`: Lazy Evaluation
    - `tests/test_lab6.py`: FRP / Event Bus
    - `tests/test_lab7.py`: Composition & Services
    - `tests/test_lab8.py`: Async
    
    Run `pytest` in the console to execute them.
    """)

else:
    st.info(f"Section {menu} is under construction.")
