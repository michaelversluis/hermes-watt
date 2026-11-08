#!/usr/bin/env bash
set -euo pipefail
if [[ -x .dev/venv314/bin/python ]]; then
  .dev/venv314/bin/python -m pytest -q --tb=short
else
  python3 -m pytest -q --tb=short
fi
npm test
git diff --check
