#!/bin/bash
# Fast test runner: parallel non-GUI tests + serial GUI tests
# Typical time: ~2.5 min (vs ~7 min serial)
set -e
cd "$(dirname "$0")"

echo "=== Non-GUI tests (parallel) ==="
xvfb-run -a .venv/bin/pytest --ignore=tests/e2e -m "not gui" -q --disable-warnings -n auto "$@"

echo ""
echo "=== GUI tests (serial, Tk requires single thread) ==="
xvfb-run -a .venv/bin/pytest --ignore=tests/e2e -m "gui" -q --disable-warnings "$@"
