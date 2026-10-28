"""Test investigation engine and scoring."""

import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from scamlens.core.models import (
    IncidentStage,
    InvestigationSubmission,
    VerdictEnum,
)
from scamlens.investigator.engine import ScamInvestigator


class TestInvestigator(unittest.TestCase):
    def setUp(self):
        self.investigator = ScamInvestigator()

    def test_benign_submission(self):
        submission = InvestigationSubmission(
            text="Hello, here is the meeting notes link https://docs.google.com for today.",
            urls=["https://docs.google.com"],
            incident_stage=IncidentStage.PRE_ACTION,
        )
        result = self.investigator.investigate(submission)
        self.assertEqual(result.verdict, VerdictEnum.NO_CLEAR_INDICATORS)
        self.assertLess(result.risk_score, 40)

    def test_phishing_submission(self):
        submission = InvestigationSubmission(
            text="Dear customer, your bank account blocked within 24 hours. Click http://hdfc-update.xyz to complete KYC immediately.",
            urls=["http://hdfc-update.xyz"],
            incident_stage=IncidentStage.PRE_ACTION,
        )
        result = self.investigator.investigate(submission)
        self.assertIn(result.verdict, (VerdictEnum.LIKELY_SCAM, VerdictEnum.SUSPICIOUS))
        self.assertGreaterEqual(result.risk_score, 50)
        self.assertGreater(len(result.recommended_actions), 0)

    def test_post_harm_emergency_guidance(self):
        submission = InvestigationSubmission(
            text="I transferred Rs 5000 to fraudster",
            incident_stage=IncidentStage.POST_ACTION,
        )
        result = self.investigator.investigate(submission)
        self.assertTrue(any("1930" in act or "bank" in act.lower() for act in result.recommended_actions))


if __name__ == "__main__":
    unittest.main()
