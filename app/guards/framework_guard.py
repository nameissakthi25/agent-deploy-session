"""The same job as input_guard.py, done with Guardrails AI instead.

Added so the session can compare a hand-written guard against a framework one
on the same answer key, rather than arguing about it. Our guard stays the
default; this one runs when GUARD_BACKEND=framework, and evals/guard_eval.py
scores both.

READ THE TELEMETRY NOTE BELOW BEFORE USING THIS ANYWHERE REAL.
"""

import os
import re

# --- telemetry, disabled before anything else imports -----------------------
#
# Out of the box this library POSTs OpenTelemetry spans to
#   https://hty0gc1ok3.execute-api.us-east-1.amazonaws.com/v1/traces
# hardcoded at guardrails/utils/hub_telemetry_utils.py:70. We caught it in the
# logs the first time we ran it offline, retrying against that host.
#
# For this session that is not a footnote. The honest reason to self-host is
# data residency -- "our data cannot leave the country" -- and a guardrail
# library that ships trace data to us-east-1 by default cuts directly against
# it. Note also `use_remote_inferencing` in the rc config, which can run
# validator inference on their servers instead of yours. It defaults to False;
# check that it still does.
#
# Both switches are set here rather than left to a config file, so nothing
# leaves the box because somebody forgot to write ~/.guardrailsrc.
os.environ.setdefault("GUARDRAILS_DISABLE_TELEMETRY", "true")
os.environ.setdefault("GUARDRAILS_ENABLE_METRICS", "false")

from guardrails import Guard  # noqa: E402
from guardrails.classes.validation.validation_result import (  # noqa: E402
    FailResult,
    PassResult,
    ValidationResult,
)
from guardrails.settings import settings  # noqa: E402
from guardrails.validator_base import Validator, register_validator  # noqa: E402

from app.guards.input_guard import (  # noqa: E402
    INJECTION_PHRASES,
    MAX_INPUT_CHARS,
    PII_PATTERNS,
    InputRejected,
)

settings.disable_tracing = True


# --- a local validator, so this works with no Hub and no network ------------
#
# Guardrails AI ships ZERO usable validators. All ~65 live in a Hub that is
# fetched over the network from hub.api.guardrailsai.com, one
# `guardrails hub install` at a time. On an air-gapped box you get a framework
# with nothing in it.
#
# So the default here is a validator we define ourselves, which needs no Hub.
# It reuses the exact patterns from input_guard, which means it scores the
# same -- that is the point: it proves the wiring, not the detection.
#
# The real comparison needs a Hub validator. Install one on the box:
#   guardrails hub install hub://guardrails/detect_pii
# then set GUARD_VALIDATOR=hub. DetectPII wraps Presidio, so it should beat
# our 14% corpus coverage substantially. Measure it; do not assume it.
@register_validator(name="corplabs/it-support-input", data_type="string")
class ITSupportInput(Validator):
    """Length, injection phrases and PII, expressed as one validator."""

    def _validate(self, value: str, metadata: dict) -> ValidationResult:
        if len(value) > MAX_INPUT_CHARS:
            return FailResult(
                error_message=(
                    f"input is {len(value)} characters, over the "
                    f"{MAX_INPUT_CHARS} character limit"
                )
            )
        lowered = value.lower()
        for phrase in INJECTION_PHRASES:
            if phrase in lowered:
                return FailResult(
                    error_message=f"input contains the injection phrase {phrase!r}"
                )
        for label, pattern in PII_PATTERNS.items():
            if pattern.search(value):
                return FailResult(error_message=f"input matched the {label} pattern")
        return PassResult()


def _build_guard() -> Guard:
    """Assemble the Guard. Hub validators only if one was installed."""
    if os.environ.get("GUARD_VALIDATOR") == "hub":
        try:
            from guardrails.hub import DetectPII  # type: ignore

            return Guard().use(DetectPII(pii_entities="pii", on_fail="exception"))
        except ImportError as error:
            raise RuntimeError(
                "GUARD_VALIDATOR=hub, but no Hub validator is installed. Run: "
                "guardrails hub install hub://guardrails/detect_pii"
            ) from error
    # on_fail belongs on the validator, not on .use()
    return Guard().use(ITSupportInput(on_fail="exception"))


_guard = _build_guard()

# Reused so a caller can tell which path actually ran without reading env vars.
BACKEND = (
    "guardrails-ai/hub"
    if os.environ.get("GUARD_VALIDATOR") == "hub"
    else ("guardrails-ai/local")
)


def check_input(message: str) -> str:
    """Return the message unchanged, or raise InputRejected saying why.

    Same signature and same exception as app.guards.input_guard.check_input,
    so the two are interchangeable and the eval can score them side by side.
    """
    try:
        _guard.validate(message)
    except Exception as error:
        # Guardrails raises its own exception type and wraps our message in
        # "Validation failed for field with errors: ...". Unwrap it, so the
        # rejection reason that reaches the trace and the user reads the same
        # whichever backend ran.
        reason = str(error).strip().replace("\n", " ")
        reason = re.sub(r"^Validation failed for field with errors:\s*", "", reason)
        raise InputRejected(reason[:200]) from error
    return message
