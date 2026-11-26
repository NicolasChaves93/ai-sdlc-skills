#!/usr/bin/env bash
# Levanta el simulador: prepara (o compone) los modelos del proyecto y arranca el servidor en http://127.0.0.1:8099
# Uso: ./run.sh <espacio-de-trabajo> [puerto]      (puerto por defecto 8099)
set -euo pipefail
T="$(cd "$(dirname "$0")" && pwd)"; W="${1:?uso: run.sh <espacio-de-trabajo> [puerto]}"; PORT="${2:-8099}"
if [ ! -x "$T/.venv/bin/python" ]; then python3 -m venv "$T/.venv" && "$T/.venv/bin/pip" install -q -r "$T/requirements.txt"; fi
# con compose.json se conserva el dibujo hecho a mano; sin él, el diagrama se redibuja para simular
if [ -f "$W/compose.json" ]; then python3 "$T/compose.py" "$W"; else "$T/prepare.sh" "$W"; fi
if [ ! -f "$T/web/dist/app.js" ] || [ -n "$(find "$T/web/src" "$T/web/public" -newer "$T/web/dist/app.js" -print -quit)" ]; then "$T/web/build.sh"; fi
exec "$T/.venv/bin/python" "$T/server/server.py" --workspace "$W" --port "$PORT"
