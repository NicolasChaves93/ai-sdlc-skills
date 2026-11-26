# Simulador de procesos — referencia técnica

La guía de uso está en [README.md](README.md). Decisión y pruebas: **ADR-001** en Notion. Herramienta personal; PM4Py es AGPL, no distribuir.

```bash
./run.sh <espacio-de-trabajo> [puerto]   # puerto por defecto 8099
./lint.sh <diagrama.bpmn> [...]          # estándar de diagramas
./test.sh                                # motor, registro de eventos, servidor, preparación y composición
```

## Estándar de diagramas

Todo diagrama que vea una persona se dibuja **a mano** y pasa `./lint.sh` sin errores **ni avisos** (`bpmnlint` + reglas Miragon, `bpmnlintrc.json`).

- Un **carril por rol**. Por eso `flow-target-alignment` está apagada.
- Separar por **cuándo ocurre** (preparación, ejecución) y dejar las operaciones poco usadas en su propio diagrama.
- Archivos y títulos **numerados por orden y nivel**: `1.0_`, `2.0_`, `2.1_`, `2.1.1_`. Cada caja «+» lleva el número del diagrama que abre.
- Tareas 100×80, rombos 50×50 (con su X), eventos 36×36. A una tarea se entra por la izquierda y se sale por la derecha.
- Los caminos que regresan se unen con un rombo antes de la tarea. Líneas rectas, sin cruces. Cada paso declara `incoming` y `outgoing`.

## Dos formas de preparar un espacio de trabajo

| | Un diagrama | Varios diagramas dibujados a mano (recomendado para mostrar) |
|---|---|---|
| Se activa | Por defecto (`prepare.sh`) | Si existe `compose.json` (`compose.py`) |
| Dibujo | Se **redibuja** para simular | Se **conserva** |
| Partes por separado | No | Sí |

```
mi-proceso/
├── workspace.json
├── compose.json              # solo en la segunda forma
├── models/                   # diagramas (en la segunda forma, compose.json dice cuáles)
├── scenarios/mi.json
├── reports/                  # generado
└── escenarios_guardados/     # lo que guarda la persona
```

`workspace.json`:
```json
{"name": "Mi proceso", "model": "mi", "process_title": "Mi proceso", "scenario": "scenarios/mi.json",
 "ui": {"indicadores": [{"titulo": "Aprobadas", "valor": "T_Registrar", "detalle": "de {T_Revisar} revisadas"}],
        "reprocesos": ["T_Corregir"],
        "crecimiento": {"N": {"etq": "Solicitudes", "vals": [20, 40, 80, 160]}}}}
```
`valor` y `{...}` son ID del BPMN (sumables con `+`).

`compose.json`:
```json
{"source": "models",
 "diagrams": {"P": "1.0_preparacion", "E": "2.0_ejecucion", "O": "2.1_operaciones"},
 "calls": {"Call_Operar": "O"},
 "parts": [
   {"id": "preparacion", "prefix": "P", "subprocess": "SP_Preparacion", "title": "1. Preparación", "lane": "Administrador", "whole": true},
   {"id": "ejecucion",   "prefix": "E", "subprocess": "SP_Ejecucion",   "title": "2. Ejecución",   "lane": "Operador",      "whole": true},
   {"id": "operaciones", "prefix": "O", "subprocess": "SP_Operaciones", "title": "2.1 Operaciones", "lane": "Operador"}
 ]}
```
- El **prefijo** encabeza los ID del modelo compuesto (`P_T_Crear`): así se nombran en el escenario.
- `whole`: partes que forman «todo el proceso», en orden.
- `compose.py` genera `build/`, `models/<model>.bpmn` y `partes/`, y escribe `partes` y `ui.vista` en `workspace.json`.

**No admite** (se detiene y nombra el elemento): temporizadores y otros eventos con definición, eventos de borde, repeticiones o multi-instancia, condiciones en las flechas, tareas de envío, recepción, script o regla, y cajas «+» sin diagrama asignado. Importar con `⤒ .bpmn` no hace esta revisión.

`examples/permisos` muestra la estructura de la primera forma; su diagrama es de prueba y no cumple el estándar.

## Formato del escenario

```json
{
  "nombre": "Permisos",
  "params": {
    "N":     {"etiqueta": "Solicitudes", "valor": 40, "min": 1, "max": 500, "paso": 1, "unidad": "solicitudes", "origen": "supuesto", "grupo": "Carga"},
    "JEFES": {"etiqueta": "Jefes", "valor": 1, "min": 1, "max": 10, "paso": 1, "unidad": "personas", "origen": "real", "grupo": "Personas",
              "nota": "Confirmado por el área.", "probar": [2, 3]},
    "P_SI":  {"etiqueta": "Solicitudes aprobadas", "valor": 0.8, "min": 0, "max": 1, "paso": 0.05, "unidad": "prob.", "origen": "supuesto", "grupo": "Carga",
              "calculo": "aprobadas ÷ revisadas."}
  },
  "raiz": {"instancias": "N", "ventana": 3600, "llegadas": {"tipo": "uniforme", "min": 0, "max": 3600}},
  "recursos": {"jefe": {"nombre": "Jefe", "capacidad": "JEFES"}},
  "elementos": {
    "T_Solicitar": {"dur": {"tipo": "const", "valor": 60}},
    "T_Revisar":   {"dur": {"tipo": "triangular", "min": 60, "moda": 120, "max": 300}, "recurso": "jefe"},
    "G_Aprueba":   {"prob": {"F_Si": "P_SI"}, "caminoMejor": "F_Si"},
    "T_Registrar": {"dur": 2}
  }
}
```

**`params`** (cada uno es un control)

| Campo | Para qué |
|---|---|
| `origen` | `negocio`, `real` (anotar la fuente en `nota`) o `supuesto`. **Solo los supuestos varían** en los escenarios aleatorios. |
| `grupo` | Sección plegable; la primera se abre. |
| `unidad: "prob."` | Muestra el valor en palabras y la leyenda. |
| `calculo`, `nota`, `br` | Cómo obtenerlo, aclaración y regla relacionada. |
| `probar` | Valores sugeridos para datos `real`. |
| `min`, `max`, `paso` | Límites. Pon `max` < 1 si una probabilidad en 1 crea un bucle sin fin. |

**`recursos`:** `capacidad` puede ser número o parámetro; si es parámetro, se sugiere cuánto subirlo.

**`elementos`:** claves = ID del BPMN. Cualquier número admite expresiones (`"B*0.002"`, `"1-P_SI"`). Tiempos en segundos; un paso sin datos tarda 0.

| `dur.tipo` | Campos | Cuándo |
|---|---|---|
| `const` | `valor` | Casi siempre igual (sistema). |
| `uniforme` | `min`, `max` | Solo conoces el rango. |
| `triangular` | `min`, `moda`, `max` | Mínimo, habitual y máximo. |
| `lognormal` | `media`, `cv` | Trabajo de personas. |
| `exp` | `media` | Muy variable. |

`escala` multiplica la duración.

**Rombos:** `prob` (lo no declarado se reparte entre las demás flechas); `tipo: "contador"`, `veces`, `flujo` (repite hasta la N-ésima visita); `tipo: "exitos"`, `veces`, `prob`, `flujo` (repite hasta juntar N aciertos, p. ej. «buscar 5 ganadores reales»; no lo reemplaces por una probabilidad promedio, exagera la variación); `caminoMejor`, `caminoPeor`, `repPeor`. En cualquier elemento, `"reinicia": ["<rombo>"]` borra la cuenta de esos rombos al pasar por él (útil si una vuelta se abandona antes de completarse).

## Piezas

| Carpeta | Qué es |
|---|---|
| `engine/simengine/` | SpiffWorkflow (lógica BPMN) + SimPy (tiempo, colas, capacidad) + PM4Py (`eventlog.py`: XES, conformidad, cuellos). |
| `server/` | `server.py` (solo 127.0.0.1; valida `Host` y `Origin`), `report.py` (informes), `explore.py` (aleatorios), `saved.py` (guardados). |
| `web/` | Interfaz `bpmn-js` y herramientas de trazado (`tools/`, Node). `web/build.sh` genera `web/dist`. |
| `tests/` | `unittest`. |

API: `/api/project[?parte=]`, `/api/simulate`, `/api/explore`, `/api/saved/{save,list,load,compare,real,delete}`, `/api/live/*`, `/api/analysis`, `/api/export/xes`.

## Reglas del motor

- **Contrato de trazabilidad:** el log del sistema real debe traer `case_id`, `activity_id` (= ID del elemento BPMN), `lifecycle` (schedule/start/complete), `timestamp`, `resource`.
- Ningún ID puede llamarse `Start` (choca con una tarea interna de SpiffWorkflow).
- SpiffWorkflow busca tareas con profundidad máxima 1000 y **trunca en silencio**: el motor usa profundidad ilimitada, exige terminar en un evento de fin y limita los pasos por caso.
- Las simulaciones corren de una en una: el reloj simulado de los temporizadores (`vclock.py`) es global.
- Dentro de un caso los pasos van uno tras otro; sin comprobar que los tiempos de compuertas paralelas se solapen.
- Pendiente: trivia (`contadores`/`derivados`, multi-instancia y temporizadores sobre subprocesos).
