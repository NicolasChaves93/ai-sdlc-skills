# sim-template — simulador de procesos (plantilla base)

Valida flujos BPMN antes de construir, encuentra cuellos de botella y límites de capacidad, y se calibra con logs reales.
Decisión y pruebas: **ADR-001** en Notion (PoCs y decisiones). Herramienta personal; PM4Py es AGPL, no distribuir.

## Uso
```
./run.sh                       # prepara los modelos de ~/proyectos/sim-juegos y arranca http://127.0.0.1:8099
./run.sh ~/proyectos/otro 8100 # otro espacio de trabajo / puerto
./test.sh                      # 21 pruebas (motor, PM4Py, servidor)
```
Un **espacio de trabajo** (carpeta de proyecto, fuera del repositorio del proyecto) tiene: `workspace.json`, `models/<m>.bpmn` (BPMN de negocio con `cc:carril`),
`scenarios/<m>.json`, `data/{synthetic,local,production}/`, `reports/`. `prepare.sh` genera `build/` (diagrama plano con carriles reales, por subprocesos y geometría).

## Piezas
| Carpeta | Qué es |
|---|---|
| `engine/simengine/` | Motor Python: SpiffWorkflow (lógica BPMN) + SimPy (tiempo, colas, capacidad) + PM4Py (`eventlog.py`: XES, conformidad, cuellos). |
| `server/server.py` | Servidor local (biblioteca estándar, solo 127.0.0.1, valida `Host`). API: `/api/simulate`, `/api/live/*`, `/api/analysis`, `/api/export/xes`. |
| `web/` | Interfaz `bpmn-js` (solo dibuja) y herramientas de trazado de BPMN (`tools/`, Node). `web/build.sh` genera `web/dist`. |
| `tests/` | `unittest`: paridad con el prototipo JS, subprocesos, perfiles de llegada, modo en vivo, bucles, reloj simulado, PM4Py, servidor. |

## Reglas del motor que conviene recordar
- **Contrato de trazabilidad:** el log del sistema real debe traer `case_id`, `activity_id` (= ID del elemento BPMN), `lifecycle` (schedule/start/complete), `timestamp`, `resource`.
- Ningún ID del BPMN puede llamarse `Start` (choca con una tarea interna de SpiffWorkflow).
- SpiffWorkflow busca tareas con profundidad máxima 1000 por defecto y **trunca en silencio**: el motor usa profundidad ilimitada y exige terminar en un evento de fin; además hay un tope de pasos por caso para detectar bucles sin fin.
- Las simulaciones corren de una en una (candado): el reloj simulado de los temporizadores (`vclock.py`) es global.

## Pendiente (alcance actual: solo el sorteo)
Trivia: `contadores`/`derivados` del escenario, multi-instancia de participantes y temporizadores sobre subprocesos (el reloj simulado está probado pero aún no conectado al motor).
Retirar el prototipo en JavaScript (`sim-juegos/legacy-js`) cuando ya no haga falta como referencia.
