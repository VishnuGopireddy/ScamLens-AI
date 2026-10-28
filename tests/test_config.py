"""Test configuration loading."""

import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from scamlens.core.config import get_settings


class TestConfig(unittest.TestCase):
    def test_settings_defaults(self):
        settings = get_settings()
        self.assertIn(settings.app_env, ("development", "test", "production"))
        self.assertGreater(settings.api_port, 0)
        self.assertEqual(settings.default_region, "IN")
        self.assertTrue(settings.enable_pii_redaction)


if __name__ == "__main__":
    unittest.main()
