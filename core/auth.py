from typing import List, Optional

USERS = {
    "admin": "admin123",
    "user1": "userpass1",
    "user2": "userpass2"
}

USER_ACCOUNTS = {
    "user1": ["acc1"],
    "user2": ["acc2"]
}

def verify_credentials(username, password):
    return USERS.get(username) == password

def get_user_role(username):
    return "admin" if username == "admin" else "user"

def get_user_accounts(username) -> Optional[List[str]]:
    """
    Returns list of allowed account IDs.
    Returns None if user has access to ALL accounts (admin).
    """
    if username == "admin":
        return None
    return USER_ACCOUNTS.get(username, [])
