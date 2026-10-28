"""Regional advisory and trusted knowledge base interface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class RegionalKnowledgeBase:
    """Provides verified domain references, official helplines, and safety rules."""

    def __init__(self, data_path: Optional[Path] = None):
        if data_path is None:
            data_path = Path(__file__).parent / "data" / "trusted_domains.json"
        self.data_path = data_path
        self._data: Dict[str, Any] = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        if not self.data_path.is_file():
            return {"banks": {}, "government_services": {}, "upi_legitimacy_guidelines": []}
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"banks": {}, "government_services": {}, "upi_legitimacy_guidelines": []}

    def verify_domain_against_brand(self, brand: str, domain: str) -> Optional[bool]:
        """Check if a given domain matches the official registry for a known brand.

        Returns:
            True if matches official domain
            False if brand is known but domain does NOT match
            None if brand is not in the registry
        """
        brand_key = brand.lower().strip()
        banks = self._data.get("banks", {})
        if brand_key in banks:
            official_domains = banks[brand_key].get("official_domains", [])
            domain_clean = domain.lower().strip().split(":")[0]
            for od in official_domains:
                if domain_clean == od or domain_clean.endswith("." + od):
                    return True
            return False
        return None

    def get_national_cybercrime_helpline(self) -> str:
        """Returns the national cyber fraud emergency helpline (e.g. 1930 in India)."""
        gov = self._data.get("government_services", {})
        cyber = gov.get("cybercrime", {})
        return cyber.get("national_helpline", "1930")

    def get_upi_safety_rules(self) -> List[str]:
        """Returns fundamental rules for UPI transactions."""
        return self._data.get("upi_legitimacy_guidelines", [])

