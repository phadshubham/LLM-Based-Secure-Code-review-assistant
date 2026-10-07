"""
=======================================================================
INTENTIONALLY VULNERABLE DEMONSTRATION PROJECT
=======================================================================
This file contains DELIBERATELY INSECURE code for educational purposes.
DO NOT use any of this code in a real application.

Purpose: Demonstrate common security vulnerabilities for scanner testing.
=======================================================================
"""

import hashlib
import os
import sqlite3
import subprocess


# ─── Vulnerability 1: Hardcoded credentials ──────────────────────────────────
DB_PASSWORD = "admin123"          # INSECURE: hardcoded password
SECRET_KEY = "mysecretkey1234"    # INSECURE: hardcoded secret
API_KEY = "sk-demo-key-12345678"  # INSECURE: hardcoded API key


# ─── Vulnerability 2: SQL Injection ──────────────────────────────────────────

def get_user(username: str):
    """Fetch a user from the database."""
    conn = sqlite3.connect("demo.db")
    cursor = conn.cursor()
    # INSECURE: string concatenation in SQL query
    query = "SELECT * FROM users WHERE username='" + username + "'"
    cursor.execute(query)
    return cursor.fetchone()


def login(username: str, password: str):
    """Authenticate a user."""
    conn = sqlite3.connect("demo.db")
    cursor = conn.cursor()
    # INSECURE: f-string SQL injection
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)
    result = cursor.fetchone()
    if result:
        return True
    return False


# ─── Vulnerability 3: Unsafe subprocess / Command Injection ───────────────────

def ping_host(hostname: str):
    """Ping a host."""
    # INSECURE: shell=True with user-controlled input → command injection
    result = subprocess.run(
        f"ping -c 1 {hostname}",
        shell=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def list_directory(path: str):
    """List directory contents."""
    # INSECURE: os.system with user input
    os.system(f"ls -la {path}")


# ─── Vulnerability 4: Weak Cryptography ──────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a password."""
    # INSECURE: MD5 is cryptographically broken
    return hashlib.md5(password.encode()).hexdigest()


def hash_password_sha1(password: str) -> str:
    """Hash a password with SHA-1."""
    # INSECURE: SHA-1 is deprecated for password hashing
    return hashlib.sha1(password.encode()).hexdigest()


# ─── Vulnerability 5: Insecure file read (path traversal risk) ────────────────

def read_file(filename: str) -> str:
    """Read a file."""
    # INSECURE: no path sanitization; user could supply ../../etc/passwd
    with open(filename, "r") as f:
        return f.read()


# ─── Vulnerability 6: Insecure deserialization ────────────────────────────────

def load_user_data(serialized: bytes):
    """Load user session data."""
    import pickle  # noqa
    # INSECURE: pickle.loads on untrusted data is dangerous
    return pickle.loads(serialized)


# ─── Vulnerability 7: Debug/developer backdoor ────────────────────────────────

def admin_override(token: str):
    """Check admin token."""
    # INSECURE: hardcoded backdoor token
    if token == "DEBUG_OVERRIDE_2024":
        return True
    return False


if __name__ == "__main__":
    print("Demo app running – this is intentionally vulnerable!")
    print("Username lookup:", get_user("admin"))
