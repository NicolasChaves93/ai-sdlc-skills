#!/usr/bin/env bash
# Copia los insumos de prueba desde el espacio de trabajo del sorteo (no versionar datos reales).
set -euo pipefail
W="${1:-$HOME/proyectos/sim-juegos/legacy-js}"; F="$(dirname "$0")/fixtures"
cp "$W/entregables/sorteo/bpmn_to-be_sorteo_v3.bpmn" "$F/sorteo_flat.bpmn"
sed -E 's/ cc:carril="[^"]*"//g; s/ xmlns:cc="[^"]*"//' "$W/generated/sorteo.bpmn" > "$F/sorteo_hier.bpmn"
cp "$W/escenarios/sorteo.json" "$F/sorteo.json"; cp "$W/spike-py/referencia/js.json" "$F/js_reference.json"; cp "$W/spike-py/salida/timer_prueba.bpmn" "$F/timer.bpmn"
