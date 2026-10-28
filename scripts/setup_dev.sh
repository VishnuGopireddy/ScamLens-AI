#!/usr/bin/env bash
# ==============================================================================
# ScamLens-AI Developer Environment Setup Script
# ==============================================================================
set -e

echo "=== Setting up ScamLens-AI Development Environment ==="

# 1. Check Python version
python3 --version

# 2. Setup .env from .env.example if missing
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# 3. Run test suite
echo "Running unit test suite..."
python3 -m unittest discover tests

# 4. Run evaluation benchmark
echo "Running evaluation benchmark..."
python3 benchmark/runner.py

# 5. Test AI Provider connectivity
echo "Checking AI Provider & API Key status..."
python3 scripts/test_api.py

echo ""
echo "=== Setup complete! ==="
echo "Try running an investigation via CLI:"
echo "  python3 src/scamlens/cli.py --text \"Urgent: Account blocked. Update KYC immediately.\" --url \"http://sbi-fake.xyz\""

