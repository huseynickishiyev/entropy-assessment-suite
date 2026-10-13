#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON="${PYTHON:-python3}"
"$PYTHON" -m venv .venv
PYTHON="$(pwd)/.venv/bin/python"
"$PYTHON" -m pip install --disable-pip-version-check -r requirements.txt
cc -O2 -std=c11 -Wall -Wextra engine/health.c -lm -o engine/ip4_health
"$PYTHON" scripts/prepare_nist.py --install-deps
"$PYTHON" -m unittest discover -s tests -v
"$PYTHON" app/gui.py
