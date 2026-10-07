# Python Demo – Intentionally Vulnerable Project

**⚠️ WARNING: This project contains DELIBERATELY INSECURE code for educational purposes ONLY.**

Do NOT use any code from this project in a real application.

## Purpose

This sample project is provided to demonstrate the capabilities of the
Secure Code Review Assistant.  It contains multiple intentional security
vulnerabilities so that students can see real scanner findings and AI explanations.

## Vulnerabilities Included

| # | Vulnerability | Location |
|---|---------------|----------|
| 1 | Hardcoded credentials / secrets | `app.py` lines 18-20 |
| 2 | SQL Injection (string concatenation) | `app.py` `get_user()` |
| 3 | SQL Injection (f-string) | `app.py` `login()` |
| 4 | Command Injection (`shell=True`) | `app.py` `ping_host()` |
| 5 | OS Command Injection (`os.system`) | `app.py` `list_directory()` |
| 6 | Weak Cryptography (MD5) | `app.py` `hash_password()` |
| 7 | Weak Cryptography (SHA-1) | `app.py` `hash_password_sha1()` |
| 8 | Path Traversal | `app.py` `read_file()` |
| 9 | Insecure Deserialization (pickle) | `app.py` `load_user_data()` |
| 10 | Hardcoded backdoor token | `app.py` `admin_override()` |

## How to Scan

1. ZIP the `python_demo` folder
2. Upload via the Secure Code Review Assistant
3. Click "Run Security Scan"
4. Review findings on the dashboard
