"""Threat intelligence verification client (VirusTotal v3 & ICANN RDAP / WHOIS).

Aligns with README §4 Objective 3, §6.E, and agentic-ai-plan.md:
- ICANN RDAP: Free, open-standard domain registration & age evaluation.
- VirusTotal API v3: Multi-engine security reputation across 70+ antivirus vendors.
- Maintains provenance, avoids declaring sites safe solely due to lack of records,
  and provides simulated offline mocks for development and testing.
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx

from scamlens.core.config import get_settings
from scamlens.core.models import EvidenceCategory, EvidenceItem, SeverityLevel

logger = logging.getLogger(__name__)

_SECOND_LEVEL_CCTLDS = {
    "co.in", "gov.in", "org.in", "net.in", "ac.in", "edu.in", "nic.in", "res.in",
    "co.uk", "org.uk", "ac.uk", "gov.uk", "com.au", "net.au", "org.au", "co.nz",
}


def _to_registrable_domain(domain: str) -> str:
    """Reduce subdomains (e.g. click.grammarly.com) to the registrable apex domain for RDAP."""
    parts = [p for p in domain.lower().strip(".").split(".") if p]
    if len(parts) <= 2:
        return ".".join(parts)
    tail_two = ".".join(parts[-2:])
    if tail_two in _SECOND_LEVEL_CCTLDS and len(parts) >= 3:
        return ".".join(parts[-3:])
    return tail_two


def _is_mock_malicious_url(url: str) -> bool:
    """Match simulated threat-intel indicators on hostname/TLD or short path tokens, ignoring opaque base64 blobs."""
    parsed = urlparse(url if "://" in url else f"http://{url}")
    hostname = (parsed.hostname or "").lower()
    if hostname.endswith((".xyz", ".buzz")):
        return True

    host_terms = ("phish", "scam", "malware", "fake", "update-pan", "kyc")
    if any(re.search(rf"(?:^|[.-]){re.escape(t)}(?:$|[.-])", hostname) for t in host_terms):
        return True

    # Check human-readable path segments only (skip long opaque encoded tracking tokens)
    segments = [seg.lower() for seg in (parsed.path or "").split("/") if seg and len(seg) <= 24]
    path_terms = ("phish", "scam", "malware", "fake", "update-pan", "kyc")
    return any(
        re.search(rf"(?:^|[-_.]){re.escape(t)}(?:$|[-_.])", seg)
        for seg in segments
        for t in path_terms
    )


def _is_mock_new_domain(domain: str) -> bool:
    """Match simulated zero-day domain indicators on bounded domain labels or suspicious TLDs."""
    domain_lower = domain.lower()
    if domain_lower.endswith((".xyz", ".top")):
        return True
    # Avoid flagging official known bank domains like hdfcbank.com or icicibank.com
    apex = _to_registrable_domain(domain_lower)
    if apex in {"sbi.co.in", "onlinesbi.sbi", "hdfcbank.com", "icicibank.com", "axisbank.com", "pnbindia.in", "kotak.com"}:
        return False
    return any(
        re.search(rf"(?:^|[.-]){re.escape(t)}(?:$|[.-])", domain_lower)
        for t in ("fake", "kyc", "update", "verify", "secure", "login", "bank")
    )


def extract_domain_from_url(url_or_domain: str) -> str:
    """Normalize input and extract clean domain hostname."""
    if not url_or_domain:
        return ""
    target = url_or_domain.strip()
    if "://" not in target:
        target = "http://" + target
    try:
        parsed = urlparse(target)
        hostname = (parsed.hostname or "").lower()
        return hostname.split(":")[0]
    except Exception:
        return url_or_domain.split("/")[0].split(":")[0].lower()


class ThreatIntelligenceClient:
    """Interface for external threat intelligence checks (WhoisXML, ICANN RDAP & VirusTotal v3)."""

    def __init__(self, use_mock: Optional[bool] = None):
        self.settings = get_settings()
        self.use_mock = (
            use_mock if use_mock is not None else self.settings.use_mock_intelligence
        )
        self.vt_api_key = self.settings.virustotal_api_key
        self.whoisxml_api_key = self.settings.whoisxml_api_key

    def _build_domain_age_finding(
        self,
        domain: str,
        age_days: int,
        reg_date_str: Optional[str],
        source: str,
        registrar: Optional[str] = None,
    ) -> EvidenceItem:
        """Build standardized domain-age EvidenceItem across RDAP and WhoisXML."""
        date_display = reg_date_str[:10] if reg_date_str else "unknown date"
        meta: Dict[str, Any] = {"domain": domain, "age_days": age_days}
        if reg_date_str:
            meta["registration_date"] = reg_date_str
        if registrar:
            meta["registrar"] = registrar

        if age_days < 30:
            return EvidenceItem(
                category=EvidenceCategory.EXTERNAL_INTEL,
                severity=SeverityLevel.HIGH,
                summary=f"Newly registered domain ({age_days} days old)",
                details=(
                    f"Domain '{domain}' was registered on {date_display} "
                    f"({age_days} days ago). Newly created domains claiming established identities are high-risk."
                ),
                is_verified=True,
                source=source,
                metadata=meta,
            )
        if age_days < 90:
            return EvidenceItem(
                category=EvidenceCategory.EXTERNAL_INTEL,
                severity=SeverityLevel.MEDIUM,
                summary=f"Recently created domain ({age_days} days old)",
                details=f"Domain '{domain}' is less than 3 months old (registered {date_display}).",
                is_verified=True,
                source=source,
                metadata=meta,
            )
        return EvidenceItem(
            category=EvidenceCategory.EXTERNAL_INTEL,
            severity=SeverityLevel.INFO,
            summary=f"Established domain ({age_days // 365}+ years old)",
            details=f"Domain '{domain}' was registered on {date_display} ({age_days} days old).",
            is_verified=True,
            source=source,
            metadata=meta,
        )

    def _query_whoisxml(self, domain: str, query_domain: str) -> Optional[List[EvidenceItem]]:
        """Query WhoisXML WhoisService API for domain registration age and registrar."""
        if not self.whoisxml_api_key:
            return None
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(
                    "https://www.whoisxmlapi.com/whoisserver/WhoisService",
                    params={
                        "apiKey": self.whoisxml_api_key,
                        "domainName": query_domain,
                        "outputFormat": "JSON",
                    },
                )
            if resp.status_code != 200:
                logger.warning("WhoisXML query HTTP %s for %s", resp.status_code, query_domain)
                return None

            payload = resp.json()
            if payload.get("ErrorMessage"):
                logger.warning("WhoisXML API error for %s: %s", query_domain, payload["ErrorMessage"])
                return None

            record = payload.get("WhoisRecord") or {}
            registry = record.get("registryData") or {}
            registrar = record.get("registrarName") or registry.get("registrarName")

            if record.get("dataError") == "MISSING_WHOIS_DATA" and not (
                record.get("createdDate") or registry.get("createdDate") or record.get("estimatedDomainAge")
            ):
                return [
                    EvidenceItem(
                        category=EvidenceCategory.EXTERNAL_INTEL,
                        severity=SeverityLevel.MEDIUM,
                        summary="Domain WHOIS record missing (WhoisXML)",
                        details=(
                            f"Domain '{domain}' returned MISSING_WHOIS_DATA from WhoisXML. "
                            "It may be unregistered, suspended, or an invalid top-level domain."
                        ),
                        is_verified=True,
                        source="whoisxml",
                        metadata={"domain": domain, "data_error": "MISSING_WHOIS_DATA"},
                    )
                ]

            reg_date_str: Optional[str] = (
                record.get("createdDate")
                or registry.get("createdDate")
                or record.get("createdDateNormalized")
                or registry.get("createdDateNormalized")
            )
            age_days: Optional[int] = None
            if reg_date_str:
                try:
                    clean_ts = reg_date_str.replace(" UTC", "Z").replace(" ", "T")
                    if clean_ts.endswith("Z"):
                        clean_ts = clean_ts[:-1] + "+00:00"
                    reg_date = datetime.fromisoformat(clean_ts)
                    if reg_date.tzinfo is None:
                        reg_date = reg_date.replace(tzinfo=timezone.utc)
                    age_days = max(0, (datetime.now(timezone.utc) - reg_date).days)
                except ValueError:
                    age_days = None

            if age_days is None and record.get("estimatedDomainAge") is not None:
                try:
                    age_days = max(0, int(record["estimatedDomainAge"]))
                except (TypeError, ValueError):
                    age_days = None

            if age_days is not None:
                return [
                    self._build_domain_age_finding(
                        domain=domain,
                        age_days=age_days,
                        reg_date_str=reg_date_str,
                        source="whoisxml",
                        registrar=registrar,
                    )
                ]
        except Exception as exc:
            logger.warning("Live WhoisXML query failed (%s)", exc)
        return None

    # --------------------------------------------------------------------------
    # 1. WhoisXML & ICANN RDAP / WHOIS Domain Age & Registration Checker
    # --------------------------------------------------------------------------
    def inspect_domain_whois_rdap(self, domain_or_url: str) -> List[EvidenceItem]:
        """Inspect domain registration date and registrar via WhoisXML / ICANN RDAP (RFC 7482).

        Evaluates domain age:
        - Age < 30 days: HIGH severity (classic zero-day phishing indicator)
        - Age < 90 days: MEDIUM severity (recently registered domain)
        - Age >= 365 days: Established domain
        """
        findings: List[EvidenceItem] = []
        domain = extract_domain_from_url(domain_or_url)
        if not domain:
            return findings

        # Skip raw IP addresses
        if domain.replace(".", "").isdigit():
            return findings

        # 1. Live Lookup when use_mock=False (WhoisXML when configured, with ICANN RDAP fallback)
        if not self.use_mock:
            rdap_domain = _to_registrable_domain(domain)
            if self.whoisxml_api_key:
                whoisxml_findings = self._query_whoisxml(domain, rdap_domain)
                if whoisxml_findings is not None:
                    return whoisxml_findings

            try:
                rdap_url = f"https://rdap.org/domain/{rdap_domain}"
                with httpx.Client(timeout=10.0) as client:
                    resp = client.get(rdap_url, follow_redirects=True)
                    if resp.status_code == 200:
                        data = resp.json()
                        reg_date_str: Optional[str] = None
                        for event in data.get("events", []):
                            if event.get("eventAction") == "registration":
                                reg_date_str = event.get("eventDate")
                                break

                        if reg_date_str:
                            reg_date = datetime.fromisoformat(
                                reg_date_str.replace("Z", "+00:00")
                            )
                            age_days = (datetime.now(timezone.utc) - reg_date).days
                            findings.append(
                                self._build_domain_age_finding(
                                    domain=domain,
                                    age_days=age_days,
                                    reg_date_str=reg_date_str,
                                    source="icann_rdap",
                                )
                            )
                            return findings

                    elif resp.status_code == 404:
                        # Real API returned HTTP 404 (Domain not found in registry)
                        findings.append(
                            EvidenceItem(
                                category=EvidenceCategory.EXTERNAL_INTEL,
                                severity=SeverityLevel.MEDIUM,
                                summary="Domain not found in RDAP registry (HTTP 404)",
                                details=(
                                    f"Domain '{domain}' was queried against the ICANN RDAP registry and returned HTTP 404 (Not Found). "
                                    f"The domain may be unregistered, suspended, or an invalid top-level domain."
                                ),
                                is_verified=True,
                                source="icann_rdap",
                                metadata={"domain": domain, "status_code": 404, "is_registered": False},
                            )
                        )
                        return findings

                    elif resp.status_code == 429:
                        findings.append(
                            EvidenceItem(
                                category=EvidenceCategory.EXTERNAL_INTEL,
                                severity=SeverityLevel.LOW,
                                summary="RDAP query rate-limited (HTTP 429)",
                                details=f"RDAP service throttled the request for domain '{domain}'.",
                                is_verified=False,
                                source="icann_rdap",
                                metadata={"domain": domain, "status_code": 429},
                            )
                        )
                        return findings

            except Exception as exc:
                logger.warning("Live RDAP query failed (%s)", exc)
                findings.append(
                    EvidenceItem(
                        category=EvidenceCategory.EXTERNAL_INTEL,
                        severity=SeverityLevel.INFO,
                        summary=f"RDAP query unreachable ({type(exc).__name__})",
                        details=f"Could not connect to live RDAP service for '{domain}': {exc}",
                        is_verified=False,
                        source="icann_rdap_offline",
                        metadata={"domain": domain, "error": str(exc)},
                    )
                )
                return findings

        # 2. Simulated Offline / Mock Evaluation (ONLY when self.use_mock is True)
        if _is_mock_new_domain(domain):
            # Simulate a zero-day domain registered 3 days ago
            findings.append(
                EvidenceItem(
                    category=EvidenceCategory.EXTERNAL_INTEL,
                    severity=SeverityLevel.HIGH,
                    summary="Newly registered domain (3 days old) [Simulated RDAP]",
                    details=f"Domain '{domain}' was registered 3 days ago. Newly registered domains impersonating brands indicate active phishing.",
                    is_verified=True,
                    source="icann_rdap_mock",
                    metadata={"domain": domain, "age_days": 3, "registrar": "NameCheap / Hostinger"},
                )
            )
        else:
            findings.append(
                EvidenceItem(
                    category=EvidenceCategory.EXTERNAL_INTEL,
                    severity=SeverityLevel.INFO,
                    summary="Established domain age (>3 years) [Simulated RDAP]",
                    details=f"Domain '{domain}' is an established domain registered over 3 years ago.",
                    is_verified=True,
                    source="icann_rdap_mock",
                    metadata={"domain": domain, "age_days": 1250},
                )
            )
        return findings

    # --------------------------------------------------------------------------
    # 2. VirusTotal API v3 Threat Intelligence
    # --------------------------------------------------------------------------
    def check_virustotal_reputation(self, url: str) -> List[EvidenceItem]:
        """Query VirusTotal API v3 for multi-engine antivirus & phishing consensus."""
        findings: List[EvidenceItem] = []
        if not url:
            return findings

        # 1. Try Live VirusTotal v3 API if API key exists and not forcing mock
        if self.vt_api_key and not self.use_mock:
            try:
                url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
                headers = {"x-apikey": self.vt_api_key}
                vt_endpoint = f"https://www.virustotal.com/api/v3/urls/{url_id}"

                with httpx.Client(timeout=5.0) as client:
                    resp = client.get(vt_endpoint, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json().get("data", {})
                        attrs = data.get("attributes", {})
                        stats = attrs.get("last_analysis_stats", {})

                        malicious = stats.get("malicious", 0)
                        suspicious = stats.get("suspicious", 0)
                        total_engines = sum(stats.values()) or 70

                        if malicious >= 2:
                            findings.append(
                                EvidenceItem(
                                    category=EvidenceCategory.EXTERNAL_INTEL,
                                    severity=SeverityLevel.CRITICAL,
                                    summary=f"VirusTotal Consensus: Flagged by {malicious}/{total_engines} security vendors",
                                    details=(
                                        f"URL '{url}' is classified as malicious/phishing by {malicious} independent security scanners "
                                        f"and {suspicious} suspicious ratings on VirusTotal."
                                    ),
                                    is_verified=True,
                                    source="virustotal_v3",
                                    metadata={"malicious": malicious, "suspicious": suspicious, "total": total_engines},
                                )
                            )
                        elif malicious == 1 or suspicious >= 2:
                            findings.append(
                                EvidenceItem(
                                    category=EvidenceCategory.EXTERNAL_INTEL,
                                    severity=SeverityLevel.MEDIUM,
                                    summary=f"VirusTotal Warning: Suspicious indicator ({malicious} malicious, {suspicious} suspicious)",
                                    details=f"URL '{url}' has minor suspicious detections on VirusTotal.",
                                    is_verified=True,
                                    source="virustotal_v3",
                                    metadata={"malicious": malicious, "suspicious": suspicious, "total": total_engines},
                                )
                            )
                        else:
                            findings.append(
                                EvidenceItem(
                                    category=EvidenceCategory.EXTERNAL_INTEL,
                                    severity=SeverityLevel.INFO,
                                    summary="VirusTotal: No active threat detections",
                                    details="0 security vendors flagged this URL on VirusTotal. Note: Zero detections does not guarantee safety for newly launched sites.",
                                    is_verified=False,
                                    source="virustotal_v3",
                                    metadata={"malicious": 0, "total": total_engines},
                                )
                            )
                        return findings

                    elif resp.status_code == 404:
                        findings.append(
                            EvidenceItem(
                                category=EvidenceCategory.EXTERNAL_INTEL,
                                severity=SeverityLevel.INFO,
                                summary="URL not found on VirusTotal (HTTP 404)",
                                details=f"URL '{url}' has never been scanned or cataloged on VirusTotal yet. Newly created phishing domains typically return 404.",
                                is_verified=True,
                                source="virustotal_v3",
                                metadata={"status_code": 404, "malicious": 0},
                            )
                        )
                        return findings
                    else:
                        logger.warning("VirusTotal query HTTP %s for %s", resp.status_code, url)
                        findings.append(
                            EvidenceItem(
                                category=EvidenceCategory.EXTERNAL_INTEL,
                                severity=SeverityLevel.INFO,
                                summary=f"VirusTotal lookup unavailable (HTTP {resp.status_code})",
                                details=f"VirusTotal API returned HTTP {resp.status_code} for '{url}'.",
                                is_verified=False,
                                source="virustotal_v3_offline",
                                metadata={"status_code": resp.status_code},
                            )
                        )
                        return findings
            except Exception as exc:
                logger.warning("Live VirusTotal query failed (%s)", exc)
                findings.append(
                    EvidenceItem(
                        category=EvidenceCategory.EXTERNAL_INTEL,
                        severity=SeverityLevel.INFO,
                        summary=f"VirusTotal query unreachable ({type(exc).__name__})",
                        details=f"Could not connect to VirusTotal API for '{url}': {exc}",
                        is_verified=False,
                        source="virustotal_v3_offline",
                        metadata={"error": str(exc)},
                    )
                )
                return findings

        # 2. Simulated Offline / Mock Evaluation
        if _is_mock_malicious_url(url):
            findings.append(
                EvidenceItem(
                    category=EvidenceCategory.EXTERNAL_INTEL,
                    severity=SeverityLevel.CRITICAL,
                    summary="VirusTotal Consensus: Flagged by 14/72 security vendors (Simulated)",
                    details=f"URL '{url}' is blacklisted as phishing/malware by 14 security engines on VirusTotal.",
                    is_verified=True,
                    source="virustotal_mock",
                    metadata={"malicious": 14, "suspicious": 3, "total": 72},
                )
            )
        else:
            findings.append(
                EvidenceItem(
                    category=EvidenceCategory.EXTERNAL_INTEL,
                    severity=SeverityLevel.INFO,
                    summary="VirusTotal: No threat records (0/72 engines) (Simulated)",
                    details="No security vendors flagged this URL on VirusTotal. Note: Absence of record != proof of safety.",
                    is_verified=False,
                    source="virustotal_mock",
                    metadata={"malicious": 0, "total": 72},
                )
            )
        return findings

    # --------------------------------------------------------------------------
    # 3. Aggregated Unified Check (backward compatible)
    # --------------------------------------------------------------------------
    def check_url_reputation(self, url: str) -> List[EvidenceItem]:
        """Query reputation databases for known malicious URLs."""
        findings = []
        # Run WHOIS/RDAP age inspection
        findings.extend(self.inspect_domain_whois_rdap(url))
        # Run VirusTotal multi-engine check
        findings.extend(self.check_virustotal_reputation(url))
        return findings
