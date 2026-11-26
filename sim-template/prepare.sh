#!/usr/bin/env bash
# Genera <espacio-de-trabajo>/build/: diagrama plano con carriles reales, diagrama por subprocesos y geometría de carriles.
# Uso: ./prepare.sh <espacio-de-trabajo>
set -euo pipefail
T="$(cd "$(dirname "$0")" && pwd)"; W="$(cd "${1:?uso: prepare.sh <espacio-de-trabajo>}" && pwd)"
[ -d "$T/web/node_modules" ] || (cd "$T/web" && npm install --silent)
cfg() { python3 -c "import json,sys; print(json.load(open('$W/workspace.json'))['$1'])"; }
M="$(cfg model)"; TITLE="$(cfg process_title)"
cd "$W"
rm -f "build/${M}_flat.bpmn" "build/${M}_hier.bpmn"   # que no quede un modelo viejo si la revisión falla
node "$T/web/tools/check-supported.mjs" "$M"
node "$T/web/tools/build-models.mjs" "$M" >/dev/null
node "$T/web/tools/export-flat.mjs" "$M" "$TITLE" v3 >/dev/null
node "$T/web/tools/validate-bpmn.mjs" "build/${M}_flat.bpmn"
