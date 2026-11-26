#!/usr/bin/env bash
# Valida diagramas dibujados a mano con las reglas del equipo (las de la extensión Miragon). Falla con errores O avisos.
# Uso: ./lint.sh <diagrama.bpmn> [...]      La primera vez copia .bpmnlintrc al espacio de trabajo para el editor.
set -euo pipefail
T="$(cd "$(dirname "$0")" && pwd)"
[ $# -ge 1 ] || { echo "uso: lint.sh <diagrama.bpmn> [...]" >&2; exit 2; }
[ -x "$T/web/node_modules/.bin/bpmnlint" ] || (cd "$T/web" && npm install --ignore-scripts --silent)
fail=0
for f in "$@"; do
  f="$(realpath "$f")"
  ws="$(dirname "$f")"; [ "$(basename "$ws")" = models ] && ws="$(dirname "$ws")"
  [ -f "$ws/.bpmnlintrc" ] || cp "$T/bpmnlintrc.json" "$ws/.bpmnlintrc"
  tmp="$(mktemp -d "$T/web/.lint-XXXXXX")"; cp "$T/bpmnlintrc.json" "$tmp/.bpmnlintrc"; cp "$f" "$tmp/"
  if out="$(cd "$tmp" && "$T/web/node_modules/.bin/bpmnlint" "$(basename "$f")" 2>&1)" && [ -z "$out" ]; then echo "OK  $f"
  else echo "FALLA  $f"; echo "$out"; fail=1; fi
  rm -rf "$tmp"
done
exit $fail
