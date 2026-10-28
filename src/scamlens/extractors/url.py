"""URL and link analysis extractor.

Aligns with README §4 Objective 3 & §5 Use Case B.
"""

from __future__ import annotations

import re
from typing import List, Set
from urllib.parse import urlparse

from scamlens.core.models import EvidenceCategory, EvidenceItem, SeverityLevel

_URL_REGEX = re.compile(
    r"https?://(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?::\d+)?(?:/[^\s]*)?",
    re.IGNORECASE,
)

_SUSPICIOUS_TLDS = {
    "xyz", "top", "work", "loan", "click", "vip", "cfd", "gq", "ml", "tk", "ga"
}

_IMPERSONATION_TARGETS = [
    "sbi", "hdfc", "icici", "pnb", "axis", "kotak", "paytm", "phonepe",
    "gpay", "amazon", "flipkart", "indiapost", "incometax", "uidai", "aadhaar"
]


def extract_urls(text: str) -> List[str]:
    """Find all URLs embedded within arbitrary text."""
    if not text:
        return []
    matches = _URL_REGEX.findall(text)
    return list(dict.fromkeys(matches))


def analyze_url(url: str) -> List[EvidenceItem]:
    """Analyze a URL for structural scam indicators and phishing characteristics."""
    findings: List[EvidenceItem] = []
    if not url:
        return findings

    try:
        parsed = urlparse(url)
    except Exception:
        findings.append(
            EvidenceItem(
                category=EvidenceCategory.URL_DOMAIN,
                severity=SeverityLevel.HIGH,
                summary="Malformed URL",
                details=f"The supplied URL could not be parsed: {url}",
                source="url_parser",
            )
        )
        return findings

    hostname = (parsed.hostname or "").lower()

    # 1. IP address in hostname (e.g., http://192.168.1.1/login)
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", hostname):
        findings.append(
            EvidenceItem(
                category=EvidenceCategory.URL_DOMAIN,
                severity=SeverityLevel.HIGH,
                summary="Direct IP address in link",
                details=f"URL uses a direct IP address ({hostname}) rather than an authenticated domain.",
                source="url_parser",
            )
        )

    # 2. Suspicious TLD check
    tld = hostname.rsplit(".", 1)[-1] if "." in hostname else ""
    if tld in _SUSPICIOUS_TLDS:
        findings.append(
            EvidenceItem(
                category=EvidenceCategory.URL_DOMAIN,
                severity=SeverityLevel.MEDIUM,
                summary=f"Uncommon or high-abuse top-level domain (.{tld})",
                details=f"Domain uses '.{tld}', commonly associated with low-cost disposable phishing sites.",
                source="url_parser",
            )
        )

    # 3. Impersonation keyword in non-official domain (e.g., sbi-verification-portal.com)
    for brand in _IMPERSONATION_TARGETS:
        if brand in hostname:
            parts = hostname.split(".")
            # If brand is combined with hyphens or excessive subdomains
            if any("-" in p and brand in p for p in parts) or len(parts) > 3:
                findings.append(
                    EvidenceItem(
                        category=EvidenceCategory.IMPERSONATION,
                        severity=SeverityLevel.HIGH,
                        summary=f"Possible impersonation of '{brand.upper()}' in domain",
                        details=f"Hostname '{hostname}' includes brand name '{brand}' in an unconventional structure.",
                        source="domain_heuristic",
                    )
                )

    # 4. Insecure protocol with sensitive claims
    if parsed.scheme == "http":
        findings.append(
            EvidenceItem(
                category=EvidenceCategory.URL_DOMAIN,
                severity=SeverityLevel.LOW,
                summary="Unencrypted HTTP protocol",
                details="URL does not use secure HTTPS encryption.",
                source="url_parser",
            )
        )

    return findings

