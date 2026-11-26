#!/usr/bin/env bash
# Todas las pruebas de la plantilla (motor, registro de eventos con PM4Py, servidor): unas 20 pruebas, ~25 s.
set -euo pipefail
cd "$(dirname "$0")"
.venv/bin/python -W ignore -m unittest discover -s tests -p "test_*.py" 2>&1 | grep -v -E "AGPL|license|Business use|processintelligence|=====|^\s*$"
