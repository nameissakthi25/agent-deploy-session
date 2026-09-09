"""The first guard: runs before anything reaches the model.

The cheapest possible place to say no. Everything here is a plain string or
regex check -- no model call, no library, so it costs nothing and a learner
can read it and see exactly what it checks.

Honest note for the session: in production you would reach for Presidio for
the PII half and a small classifier such as
protectai/deberta-v3-base-prompt-injection-v2 for the injection half. This is
the minimum, not the standard. evals/guard_eval.py measures how much that
costs us.
"""

import re

MAX_INPUT_CHARS = 4000


class InputRejected(Exception):
    """Raised when the input never should have reached the model."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


# Kept here, visible, rather than in a config file. Lowercase; the input is
# lowercased before matching. Deliberately a plain list a reader can audit.
INJECTION_PHRASES = [
    "ignore previous instructions",
    "ignore all previous instructions",
    "disregard the above",
    "disregard your instructions",
    "forget your instructions",
    "you are now",
    "act as if you have no restrictions",
    "reveal your system prompt",
    "show me your system prompt",
    "repeat the text above",
    "print your instructions",
    "developer mode",
    "jailbreak",
    "do anything now",
    "override your safety",
]

# Email, phone, and card-shaped digit strings. Named so a rejection reason can
# say which one fired, which is what makes the trace readable.
PII_PATTERNS = {
    "email address": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone number": re.compile(
        r"(?<!\d)(?:\+\d{1,3}[\s-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\d)"
    ),
    "card-shaped digits": re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)"),
}


def check_input(message: str) -> str:
    """Return the message unchanged, or raise InputRejected saying why.

    Checks run cheapest-first: length, then phrases, then regex.
    """
    if len(message) > MAX_INPUT_CHARS:
        raise InputRejected(
            f"input is {len(message)} characters, over the "
            f"{MAX_INPUT_CHARS} character limit"
        )

    lowered = message.lower()
    for phrase in INJECTION_PHRASES:
        if phrase in lowered:
            raise InputRejected(f"input contains the injection phrase {phrase!r}")

    for label, pattern in PII_PATTERNS.items():
        if pattern.search(message):
            raise InputRejected(f"input matched the {label} pattern")

    return message
