"""Privacy and sensitive data redaction module.

Aligns with README §4 Objective 7: "Design for privacy and responsible use".
Prevents leaking or storing OTPs, passwords, bank account numbers, and phone numbers.
"""

from __future__ import annotations

import re
from typing import Tuple

# Regex patterns for sensitive information
_OTP_PATTERN = re.compile(r"\b(otp|one time password|verification code)[\s:=]+([0-9]{4,8})\b", re.IGNORECASE)
_CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
_PHONE_IN_PATTERN = re.compile(r"(?<!\d)(?:\+91[\-\s]?)?[6-9]\d{9}(?!\d)")
_PASSWORD_PATTERN = re.compile(r"\b(password|passwd|pin)[\s:=]+([^\s,;]+)", re.IGNORECASE)


def redact_pii(text: str) -> Tuple[str, int]:
    """Redact sensitive PII and authentication secrets from user-submitted text.

    Returns:
        Tuple of (redacted_text, count_of_redactions)
    """
    if not text:
        return "", 0

    count = 0

    def _replace_otp(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        prefix = match.group(1)
        return f"{prefix}: [REDACTED_OTP]"

    def _replace_pwd(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        prefix = match.group(1)
        return f"{prefix}: [REDACTED_SECRET]"

    def _replace_card(match: re.Match[str]) -> str:
        nonlocal count
        digits = re.sub(r"\D", "", match.group(0))
        if 13 <= len(digits) <= 16:
            count += 1
            return "[REDACTED_CARD_NUMBER]"
        return match.group(0)

    def _replace_phone(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return "[REDACTED_PHONE]"

    redacted = _OTP_PATTERN.sub(_replace_otp, text)
    redacted = _PASSWORD_PATTERN.sub(_replace_pwd, redacted)
    redacted = _CARD_PATTERN.sub(_replace_card, redacted)
    redacted = _PHONE_IN_PATTERN.sub(_replace_phone, redacted)

    return redacted, count

