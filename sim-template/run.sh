#!/usr/bin/env bash
# Levanta el simulador: prepara los modelos del proyecto y arranca el servidor en http://127.0.0.1:8099
# Uso: ./run.sh [espacio-de-trabajo] [puerto]      (por defecto ~/proyectos/sim-juegos y 8099)
set -euo pipefail
T="$(cd "$(dirname "$0")" && pwd)"; W="${1:-$HOME/proyectos/sim-juegos}"; PORT="${2:-8099}"
if [ ! -x "$T/.venv/bin/python" ]; then python3 -m venv "$T/.venv" && "$T/.venv/bin/pip" install -q -r "$T/requirements.txt"; fi
"$T/prepare.sh" "$W"
[ -f "$T/web/dist/index.html" ] || "$T/web/build.sh"
exec "$T/.venv/bin/python" "$T/server/server.py" --workspace "$W" --port "$PORT"
