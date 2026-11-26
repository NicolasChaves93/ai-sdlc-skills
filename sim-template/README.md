# Simulador de procesos — guía

Sirve para **probar un flujo antes de programarlo**: recorre un diagrama BPMN con tiempos y probabilidades, muestra dónde se va el tiempo, quién se vuelve cuello de botella y qué caminos casi nunca ocurren.

No usa datos reales ni predice por sí solo: **los resultados valen lo que valgan los números del escenario**.

- [Empezar](#empezar) · [La pantalla](#la-pantalla) · [Recetas](#recetas-qué-quiero-saber) · [Resultados para IA](#resultados-para-una-ia-u-otra-herramienta) · [Escenarios aleatorios](#escenarios-aleatorios) · [Guardar y comparar](#guardar-lo-que-pasó-y-comparar) · [Crear escenarios](#crear-y-cambiar-escenarios) · [Proyecto nuevo](#crear-un-proyecto-de-simulación-desde-cero) · [Problemas](#problemas-frecuentes) · [Técnico](#referencia-técnica)

## Empezar

```bash
cd ~/proyectos/ai-sdlc-skills/sim-template
./run.sh examples/permisos          # abre http://127.0.0.1:8099
./run.sh <carpeta-del-proyecto> 8100
```
Se detiene con `Ctrl+C`. La primera vez instala dependencias y tarda más.

> Algunos proyectos traen su propio arranque porque conservan los diagramas dibujados a mano (en el sorteo: `~/proyectos/sim-juegos/v4/ver.sh`). Ahí **no** uses `run.sh`, que los redibuja.

## Palabras que conviene tener claras

| Palabra | Qué significa |
|---|---|
| **Caso** | Un recorrido completo del diagrama: un evento, una solicitud, un pedido. **No es una persona** ni un registro de una base de datos. |
| **Recurso** | Quien hace un paso y puede estar ocupado: una persona, un equipo, el sistema. |
| **Capacidad** | Cuántos pasos atiende ese recurso a la vez. |
| **Cola** | Casos esperando a que un recurso se libere. |
| **Escenario** | Los números de la prueba: tiempos, probabilidades, capacidades. |
| **Semilla** | Fija el azar: misma semilla y mismos valores dan el mismo resultado. |
| `negocio` / `real` / `supuesto` | Regla del producto, dato medido o confirmado, o estimación. El valor base representa tu situación; lo que quieras probar se cambia en pantalla. |

## La pantalla

### Arriba
| Control | Para qué |
|---|---|
| **Análisis** / **En vivo** | Análisis corre todo y lo reproduce. En vivo avanza con un reloj y permite inyectar casos y forzar caminos mientras corre. |
| **Completa** / **Subprocesos** | Todo en un plano, o cajas **+** que se abren (flecha azul para entrar, ruta de arriba para volver). |
| ▶ y 10× … 1000× | Reproducir y velocidad (segundos simulados por segundo real). |
| **＋ Inyectar caso** / **⚡ Ráfaga +10** | Añade 1 o 10 casos **que compiten por los mismos recursos**. Útil si llegan muchos casos independientes; no si el proceso lo atiende una sola persona. |
| ⤓ / ⤒ `.bpmn` | Descargar el diagrama o cargar otro (con su dibujo). |
| ⤓ / ⤒ `escenario` | Descargar o cargar los números de la prueba. |
| ⟲ | Volver a los valores originales. |

### Izquierda
- **Flujo:** *Al azar* (según probabilidades), *Mejor caso* (camino favorable y tiempos rápidos) o *Peor caso* (reprocesos y tiempos lentos).
- **Cómo llegan los casos:** repartidos en la ventana, progresivo, todos a la vez o aleatorios. Solo importa con varios casos.
- **🎲 Otra:** otra corrida al azar.
- **Resultado:** casos completados, duración total, tiempo por caso (`p95` = 95 de cada 100 tardan eso o menos) e indicadores del proyecto.
- **Escenario:** los parámetros, agrupados en secciones plegables. Cada una dice cuántos valores cambiaste.

### Centro
- **Simular:** (si el proyecto tiene partes) todo el proceso o solo una.
- **Mapa de calor:** colorea los pasos por espera acumulada, espera p95, cola máxima, veces que se pasa o duración.
- En la reproducción: ⏳ esperando, ⚙ en ejecución, ▣ dentro del subproceso.

### Derecha
- **Puntos críticos:** *Alertas* (colas), *Dónde se va el tiempo*, *Casos borde a probar* (hay que bajar), *Qué pasa si cambia la capacidad* y la *Sugerencia* de cuántas personas o capacidad subir. Las dos últimas solo aparecen cuando hay fila.
- **Paso:** al hacer clic en el diagrama. Cambia su duración, quién lo hace, las probabilidades de un rombo o **Forzar camino**.
- **Pruebas:**
  - *Comparar mejor / azar / peor*, con 30 corridas al azar para ver el rango.
  - *Probar aumento:* sube un valor paso a paso y busca dónde se quiebra.
  - *Analizar escenario:* comprueba que lo simulado sigue las flechas del diagrama (no que el flujo sea correcto para el negocio) y descarga el registro XES.

## Recetas: qué quiero saber

| Pregunta | Cómo |
|---|---|
| ¿Cuánto tarda normalmente? | **Pruebas → Comparar**: mira la mediana y el p95 de las 30 corridas, no una sola. |
| ¿Dónde se va el tiempo? | **Puntos críticos → Dónde se va el tiempo**. Un paso de una persona pesa mucho sin ser un problema. |
| ¿Qué pasa si crece X? | **Pruebas → Probar aumento**, eligiendo X. |
| ¿Necesito otra persona? | Sube los casos simultáneos y mira *Alertas* y *Sugerencia*. Con un solo caso no hay fila, y otra persona no lo acelera. |
| ¿Qué pasa si falla algo? | Clic en el rombo → **Forzar camino**. |
| ¿Qué casos debo probar en el código? | *Casos borde a probar*. Un 0 % en una corrida solo dice que esa vez no ocurrió. |
| ¿Comparar dos propuestas? | Guarda un escenario o diagrama por propuesta y corre **Comparar** en cada uno. |

## Resultados para una IA u otra herramienta

Cada vez que se simula, el proyecto guarda **un solo archivo que se reemplaza**: `<carpeta-del-proyecto>/reports/ultimo_resultado.json`.

| Contiene | Detalle |
|---|---|
| `como_leer` | Las precauciones para no sacar conclusiones de más. |
| `condiciones` | Parte simulada, tipo de flujo, caminos forzados y cada parámetro (valor usado, original y si es supuesto). |
| `corrida` | Lo que viste en pantalla: duración, recursos, pasos ordenados por tiempo, pasos no recorridos y cuántas veces se tomó cada camino. |
| `repeticiones` | Rango de 30 corridas al azar. Se añade unos segundos después. |

Se actualiza al cambiar cualquier valor o la parte (en *En vivo*, al terminar todos los casos). Las comparaciones de la pestaña *Pruebas* no lo cambian.
Para conservar uno, cópialo con otro nombre.

Para pedir recomendaciones, deja la prueba que te interesa en pantalla y dile al asistente:
> Lee `reports/ultimo_resultado.json` y propón mejoras al proceso. Separa lo que depende de supuestos y no cambies diagramas sin mi aprobación.

## Escenarios aleatorios

En **Pruebas → Escenarios aleatorios**. Cambia al azar **solo los `supuesto`** (parámetros y, si lo marcas, el tiempo de cada paso); lo `real` y `negocio` queda fijo.

1. En **Simular:** elige la parte que te interesa (la duración es la de esa parte).
2. Elige cuántos escenarios, cuánto pueden cambiar y, si quieres, una **meta** de duración máxima.
3. Lee: el rango, en cuántos se cumple la meta, **qué supuestos pesan más** y los mejores y peores casos (*Aplicar en pantalla* los carga; ⟲ vuelve a la base).

Los datos `real` los cambias a mano (por ejemplo, base de 5 000) y el azar parte de ese valor. En **Puntos críticos → Sugerencias para probar datos reales** salen valores para probar, con su efecto y un botón **Probar** (se definen con `"probar": [500, 5000]` en el parámetro).

Cada escenario se corre 3 veces. El resultado queda en `reports/exploracion.json`, que se reemplaza.

Precauciones: los porcentajes **no son probabilidades reales**, porque dependen de los márgenes que elijas. «Qué pesa más» es una comparación entre los escenarios bajos y altos, no una prueba de causa. Algunos valores no los controla tu aplicación (por ejemplo, cuántos sorteados resultan ganadores).

## Guardar lo que pasó y comparar

Pestaña **Guardados** (panel derecho). Sirve para: «en tal evento pasó esto; ajusto y miro si se soluciona».

1. Elige la parte en **Simular:** y pon en pantalla lo que ocurrió (parámetros, tiempos de los pasos, caminos forzados).
2. **Guardar**, con nombre y una nota de qué pasó.
3. Cuando quieras: **Cargar** (vuelven los mismos valores).
4. Ajusta lo que propones cambiar.
5. **Comparar con lo de ahora:** duración y colas antes y después, y la lista de lo que cambiaste.

Cada uno es un archivo en `<carpeta-del-proyecto>/escenarios_guardados/` (para borrarlo, borra el archivo). Guarda los números, **no el diagrama**: si el diagrama cambió, la comparación lo avisa. Que mejore en la simulación no demuestra que se solucione en la realidad: confírmalo en el siguiente evento y guarda lo que pase.

## Crear y cambiar escenarios

Hay tres niveles:

1. **Probar en pantalla.** Mueve parámetros o edita un paso. Se guarda solo en tu navegador; ⟲ lo deshace.
2. **Guardar una variante.** `⤓ escenario` la descarga; `⤒ escenario` la carga. La carga es temporal: al recargar vuelve el archivo del proyecto.
3. **Dejarlo fijo.** Edita `scenarios/<nombre>.json` (o reemplázalo por la variante) y recarga la página. Si `workspace.json` apunta a otro archivo, usa ese. En proyectos con `partes`, ejecuta su paso de regeneración (sorteo: `v4/ver.sh componer`).

Si agregas o quitas parámetros o pasos, o cambias un valor base, la página avisa y restaura los valores originales.

### Formato del escenario

```json
{
  "nombre": "Permisos",
  "params": {
    "N":     {"etiqueta": "Solicitudes", "valor": 40, "min": 1, "max": 500, "paso": 1, "unidad": "solicitudes", "origen": "supuesto", "grupo": "Carga"},
    "JEFES": {"etiqueta": "Jefes", "valor": 1, "min": 1, "max": 10, "paso": 1, "unidad": "personas", "origen": "supuesto", "grupo": "Personas"},
    "P_SI":  {"etiqueta": "Solicitudes aprobadas", "valor": 0.8, "min": 0, "max": 1, "paso": 0.05, "unidad": "prob.", "origen": "supuesto", "grupo": "Carga",
              "nota": "Texto de ayuda bajo el control."}
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

- **`params`:** cada uno es un control en pantalla, con `origen`: `negocio`, `real` (anota la fuente en `nota`) o `supuesto`. Opcionales: `grupo` (sección; la primera se abre), `nota`, `br` (regla relacionada), `unidad`, `calculo` (cómo obtener el valor).
- Con `"unidad": "prob."` la pantalla muestra el valor en palabras y la leyenda de probabilidades.
- **`raiz`:** cuántos casos (`instancias`) y cómo llegan dentro de `ventana` segundos.
- **`recursos`:** `capacidad` puede ser un número o un parámetro. Si es un parámetro, el simulador puede sugerir subirlo.
- **`elementos`:** las claves son los **ID del BPMN** (pasos, rombos y flechas).
- En cualquier número puedes usar una expresión con parámetros: `"B*0.002"`, `"1-P_SI"`.
- Todos los tiempos van en **segundos**. Un paso sin datos tarda 0.

**Duraciones**

| `tipo` | Campos | Cuándo usarla |
|---|---|---|
| `const` | `valor` | Casi siempre igual (sistema). |
| `uniforme` | `min`, `max` | Solo conoces el rango. |
| `triangular` | `min`, `moda`, `max` | Conoces lo mínimo, lo habitual y lo máximo. Buena para empezar. |
| `lognormal` | `media`, `cv` | Trabajo de personas: a veces se alarga mucho. |
| `exp` | `media` | Llegadas o tiempos muy variables. |

`escala` multiplica la duración (por ejemplo, según el tamaño de la base).

**Cómo sacar una probabilidad:** veces que pasó ÷ veces que podía pasar (5 de 20 = 0,25). Va de 0 (nunca) a 1 (siempre). Orientación: hasta 0,10 raro, de 0,10 a 0,40 a veces, de 0,40 a 0,70 cerca de la mitad, más de 0,70 casi siempre. Con menos de unas 20 observaciones, prueba también valores más bajos y más altos.

**Rombos**
- `"prob": {"<flecha>": 0.3}`: lo que no declares se reparte entre las demás.
- `"tipo": "contador", "veces": "SORTEOS", "flujo": "<flecha>"`: repite ese camino hasta la N-ésima visita.
- `caminoMejor`, `caminoPeor`, `repPeor`: qué hacer en *Mejor* y *Peor caso*.

## Crear un proyecto de simulación desde cero

```
mi-proceso/
├── workspace.json
├── models/mi.bpmn        # de Camunda Modeler, con carriles
└── scenarios/mi.json
```
`workspace.json`:
```json
{"name": "Mi proceso", "model": "mi", "process_title": "Mi proceso", "scenario": "scenarios/mi.json"}
```
Luego: `./lint.sh mi-proceso/models/mi.bpmn` y `./run.sh mi-proceso`. La forma más rápida de ver la estructura es copiar `examples/permisos` y cambiarlo; ese diagrama es solo de prueba y **no** cumple el estándar, así que dibuja el tuyo en Camunda Modeler.

**Admite:** un proceso con un inicio, tareas (simple, de usuario, manual, de servicio), rombos exclusivos y paralelos y subprocesos.
**No admite** (se detiene y nombra el elemento): temporizadores y otros eventos con definición, eventos de borde, repeticiones o multi-instancia, condiciones en las flechas, tareas de envío, recepción, script, regla o llamada. Importar con `⤒ .bpmn` no hace esta revisión.

### Opciones de `workspace.json`

```json
"ui": {
  "indicadores": [{"titulo": "Aprobadas", "valor": "T_Registrar", "detalle": "de {T_Revisar} revisadas"}],
  "reprocesos": ["T_Corregir"],
  "crecimiento": {"N": {"etq": "Solicitudes", "vals": [20, 40, 80, 160]}},
  "vista": "subprocesos",
  "raiz": "<id del subproceso que se abre al entrar>"
},
"partes": [{"id": "preparacion", "nombre": "1. Preparación", "carpeta": "partes/preparacion"}]
```
- `valor` y `{...}` son ID del BPMN (sumables con `+`).
- Cada parte es una subcarpeta con su propio `workspace.json`, `build/` y `scenarios/`.

## Estándar de diagramas

Todo diagrama que se entregue a una persona pasa `./lint.sh <diagrama.bpmn>` sin errores ni avisos (`bpmnlint` + reglas Miragon, `bpmnlintrc.json`).
- Carriles por rol, para ver quién hace cada paso. Por eso `flow-target-alignment` está apagada.
- Tareas 100×80, rombos 50×50, eventos 36×36. A una tarea se entra por la izquierda y se sale por la derecha.
- Los caminos que regresan se unen con un rombo antes de la tarea. Cada paso declara `incoming` y `outgoing`.
- `prepare.sh` redibuja el diagrama para simular: los archivos de `build/` no son entregables.

## Problemas frecuentes

| Síntoma | Qué hacer |
|---|---|
| «No hay conexión con el motor» | Inícialo con `run.sh` (o el arranque del proyecto) y abre la dirección `http://127.0.0.1:…`, no el archivo `index.html`. |
| El puerto está ocupado | Usa otro: `./run.sh <carpeta> 8100`. |
| No veo un cambio mío | Recarga la página (F5). Si cambiaste el servidor o el motor, reinícialo. |
| «Bucle sin fin» | Un camino forzado nunca termina; la página lo quita. |
| No aparece la sugerencia | No hay fila: con un solo caso es lo normal. |
| Un paso tarda 0 | No tiene datos en `elementos`, o el ID no coincide. |

## Referencia técnica

Decisión y pruebas: **ADR-001** en Notion. Herramienta personal; PM4Py es AGPL, no distribuir.

| Carpeta | Qué es |
|---|---|
| `engine/simengine/` | Motor Python: SpiffWorkflow (lógica BPMN) + SimPy (tiempo, colas, capacidad) + PM4Py (`eventlog.py`: XES, conformidad, cuellos). |
| `server/server.py` | Servidor local (solo 127.0.0.1, valida `Host`). API: `/api/project`, `/api/simulate`, `/api/live/*`, `/api/analysis`, `/api/export/xes`. |
| `web/` | Interfaz `bpmn-js` y herramientas de trazado (`tools/`, Node). `web/build.sh` genera `web/dist`. |
| `tests/` | `./test.sh` corre las pruebas del motor, el registro de eventos, el servidor y la preparación. |

- **Contrato de trazabilidad:** el log del sistema real debe traer `case_id`, `activity_id` (= ID del elemento BPMN), `lifecycle` (schedule/start/complete), `timestamp`, `resource`.
- Ningún ID del BPMN puede llamarse `Start` (choca con una tarea interna de SpiffWorkflow).
- SpiffWorkflow busca tareas con profundidad máxima 1000 y **trunca en silencio**: el motor usa profundidad ilimitada, exige terminar en un evento de fin y limita los pasos por caso.
- Las simulaciones corren de una en una: el reloj simulado de los temporizadores (`vclock.py`) es global.
- Sin comprobar: que los tiempos de las compuertas paralelas se solapen.
- Pendiente: trivia (`contadores`/`derivados`, multi-instancia y temporizadores sobre subprocesos).
