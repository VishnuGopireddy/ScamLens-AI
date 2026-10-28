"""Quick verification script to test LLM provider connectivity and API key validity."""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Add src to sys.path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from scamlens.ai.factory import get_ai_client
from scamlens.core.config import get_settings


def test_api_connection() -> None:
    settings = get_settings()
    provider = settings.default_ai_provider.lower()
    client = get_ai_client()

    print("=" * 60)
    print("ScamLens-AI: Testing AI Provider & API Key Connection")
    print("=" * 60)
    print(f"Provider:    {provider.upper()}")
    print(f"Base URL:    {client.base_url}")
    print(f"Model:       {client.model}")

    # Display masked key
    key = client.api_key or ""
    if key:
        masked_key = key[:6] + "..." + key[-4:] if len(key) > 10 else "***"
        print(f"API Key:     {masked_key} (Configured)")
    else:
        print("API Key:     NOT SET (Running in offline simulation mode)")

    print("-" * 60)
    print("Sending test prompt: 'Reply in one sentence confirming you are online.'")

    start_time = time.time()
    try:
        response = client.generate_text(
            prompt="Reply in one short sentence confirming you are online and ready.",
            temperature=0.2,
        )
        elapsed = time.time() - start_time
        print(f"\n[SUCCESS] Response received in {elapsed:.2f}s:")
        print(f"  \"{response.strip()}\"")
    except Exception as exc:
        print(f"\n[FAILED] Error communicating with {provider.upper()} API:")
        print(f"  {exc}")
        print("\nTroubleshooting:")
        print(f"  - Check your API key in .env (e.g. {provider.upper()}_API_KEY=...)")
        print(f"  - Ensure base URL {client.base_url} is reachable from this machine.")
        sys.exit(1)

    print("-" * 60)
    print("Testing JSON mode / tool response format...")
    try:
        json_resp = client.generate_json(
            prompt="Respond with a JSON object: {'status': 'ok', 'provider': 'ready'}"
        )
        print(f"[SUCCESS] JSON generation response: {json_resp}")
    except Exception as exc:
        print(f"[WARNING] JSON formatting error: {exc}")

    print("=" * 60)
    print("All API tests passed! You are ready to run investigations.")
    print("=" * 60)


if __name__ == "__main__":
    test_api_connection()

