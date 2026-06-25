import re

# OWASP A03 — SQL Injection: detect common injection patterns in user input.
# All DB access uses SQLAlchemy ORM (parameterised), so this layer provides
# defence-in-depth by rejecting obviously malicious payloads early.
# Single/double quotes are intentionally excluded because they appear
# legitimately in names (e.g. O'Neill).
_SQL_INJECTION_RE = re.compile(
    r"(--|;|/\*|\*/|xp_|union\s+select|select\s+\S+\s+from|"
    r"insert\s+into|drop\s+table|or\s+1\s*=\s*1|and\s+1\s*=\s*1)",
    re.IGNORECASE
)

# OWASP A07: Password complexity rule enforced server-side.
# Min 8 chars, at least one uppercase, one lowercase, one digit, one special char.
_PASSWORD_RE = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{8,}$'
)

# Email format: standard printable characters before @, domain label(s), TLD >= 2 letters.
_EMAIL_RE = re.compile(
    r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
)

# Phone: optional field; allows digits, spaces, +, -, (, ) up to 30 chars.
_PHONE_RE = re.compile(r'^[\d\s+\-(). ]{1,30}$')


def contains_sql_injection(value: str) -> bool:
    """Return True if value matches known SQL injection patterns."""
    return bool(_SQL_INJECTION_RE.search(value))


def is_strong_password(password: str) -> bool:
    """Return True if password satisfies complexity requirements."""
    return bool(_PASSWORD_RE.match(password))


def is_valid_email(email: str) -> bool:
    """Return True if email matches the expected format."""
    return bool(_EMAIL_RE.match(email))


def is_valid_phone(phone: str) -> bool:
    """Return True if phone matches the allowed format."""
    return bool(_PHONE_RE.match(phone))


def validate_balance(value, fallback=0.0):
    """Parse and validate a wallet balance.

    Returns (float, None) on success or (None, error_message) on failure.
    """
    try:
        balance = float(value if value is not None else fallback)
    except (TypeError, ValueError):
        return None, 'Invalid balance value'
    if balance < 0:
        return None, 'Balance cannot be negative'
    return balance, None
