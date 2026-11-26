# AGENTS.md — Orquestador SDLC y Estándares de Ingeniería

Este proyecto sigue una fábrica de software evolutiva en 7 fases con separación estricta entre **Negocio Puro**, **Arquitectura** e **Implementación por Niveles**.

## 1. Roles y Orquestación Activa (`agents-registry.yaml`)
- **Agente Principal (Orquestador): Claude Code (`claude`)** — Recibe las solicitudes, identifica la fase SDLC actual, aplica las compuertas y ejecuta directamente Fases 4–7 (código, TDD, Postman, k6, Docker, operación y cierre).
- **Agente Especialista Delegado: Gemini CLI (`gemini`)** — Se invoca automáticamente vía `gemini -p "<instrucción>"` cuando la tarea requiere sincronizar Notion MCP, modelar BPMN/DMN, probar el flujo en el simulador visual (`sim-template`), o redactar ADRs/diagramas C4 (Fases 0–3).

## 2. Activación Automática de Skills por Fase
- **Fase 0 (Ideación y Viabilidad):** `sdlc-ideation-brainstorming`
- **Fases 1–2 (Negocio Puro: BPMN, simulador visual, DMN, UML, Historias):** `sdlc-discovery-analysis`
- **Fase 3 (Diseño Técnico: C4, Secuencia, ERD Físico, Stack vs. Infra, ADR):** `sdlc-architecture-design`
- **Fases 4–5 (Código por Niveles, TDD, QA):** `sdlc-delivery-operations`
- **Fases 6–7 (Operación en vivo, deploy/freeze 24h, SOP-NN, Cierre y Retrospectiva):** `sdlc-operations-closure`
- **Skills de apoyo (Fases 4–5), se combinan con `sdlc-delivery-operations`:**
  - `test-driven-development` — antes de escribir cualquier código de implementación o corrección (Niveles 1–5).
  - `systematic-debugging` — ante cualquier bug, test fallido o comportamiento inesperado, antes de proponer una corrección.
  - `postman-cli` — colecciones y pruebas funcionales de API en `postman/` (desde Nivel 2).
  - `k6-load-testing` — pruebas de carga y escalabilidad (desde Nivel 4).

### Pre-SDLC comercial (solo clientes externos)
La cotización es pre-venta, no parte de las Fases 1–7.
- **Idea nueva o cliente externo:** Fase 0 → `propuesta-comercial` (Claude) → aprobación → Fase 1–2. No se escriben ADR ni código antes de la aprobación.
- **Proyecto propio o incremento de un proyecto aprobado:** Fase 0 o 1–2 directo.

## 3. Regla de Despacho Automático
Antes de ejecutar cualquier tarea:
1. Consulta `~/proyectos/ai-sdlc-skills/agents-registry.yaml`.
2. Si la fase pertenece a **Claude** (`4, 5, 6, 7`), ejecútala directamente.
3. Si la fase pertenece a **Gemini** (`0, 1, 2, 3`), invócalo automáticamente desde terminal mediante:
   `gemini -p "Usa <skill_correspondiente>. <contexto_y_tarea_detallada>"`
   y presenta el resultado consolidado al usuario.

### Contrato de traspaso entre fases
El traspaso se hace por archivos del proyecto, no por la conversación:
- `.sdlc/00-idea-brief.md` (Fase 0): problema, alcance (MVP, opcional, fuera), supuestos y riesgos, estimación.
- `.sdlc/active/01-stories.md` (Fases 1–2): historias, reglas `BR-XX`, escenarios Gherkin y fechas del incremento.
- `.sdlc/active/02-design.md` (Fase 3): diseño, contratos de API y modelo de datos.
- `docs/adr/NNNN-titulo.md`: decisiones técnicas con `- **Estado:** Aceptada | En validación | Descartada`. Git es la fuente de verdad y Notion su espejo.
- `.sdlc/state.json`: incremento, nivel en curso y compuertas. Las aprobaciones las confirma el usuario.
- `.sdlc/history/INC-NNN/`: incrementos cerrados.
- **Prueba del flujo antes de código:** BPMN de Camunda Modeler en `sim-template`. Claude termina levantando el modelo visual (`sim-template/run.sh <espacio-de-trabajo>`) y entrega la URL al usuario.

## 4. Compuertas Obligatorias (Zero-Skip Gates)
1. **Negocio Puro antes de Tecnología:** Prohibido mencionar frameworks, endpoints o tipos SQL en `RF`/`RNF`, tablas DMN (`BR-XX`), casos de uso, máquinas de estado o BPMN. Si cambia el flujo en construcción, actualizar primero el BPMN `To-Be` y las tablas DMN.
2. **ADR Aprobado antes de Código:** Prohibido crear carpetas de código o instalar dependencias sin un ADR aceptado en `docs/adr/`.
3. **Niveles Evolutivos:** `Nivel 1 (Núcleo Puro)` → `Nivel 2 (API Memoria + Postman)` → `Nivel 3 (SQLite)` → `Nivel 4 (PostgreSQL + k6)` → `Nivel 5 (Frontend)`.
4. **Corte y Freeze 24h:** Sincronizar estado en Notion al cerrar cada nivel y respetar congelamiento de despliegues 24h antes de eventos en vivo.

5. **Compuertas del incremento** (con `.sdlc/state.json`): sin historias cerradas no se edita `src/` ni `tests/`; desde Nivel 2 exige además ADR aceptado; no hay commit sin pruebas ni con documentación pendiente. Un bug menor de Nivel 1 solo exige Fase 1–2.

## 5. Protocolo Zero-Drift (hueco descubierto en Fase 4)
1. Detén la edición de `src/` y pon `"pending_doc_sync": true`.
2. Agrega `### [AMENDMENT - YYYY-MM-DD]` en `01-stories.md` con el ajuste y su escenario Gherkin.
3. Si cambia un contrato o la arquitectura, actualiza `02-design.md` o el ADR.
4. Vuelve a `false`, escribe la prueba del escenario nuevo y continúa.
5. Si cambia el alcance aprobado con el cliente, pon `"phase_3_adr_approved": false` y escala a Fases 1–3.

## 6. Convenciones
- **Diagramas:** los procesos se entregan en BPMN (`.bpmn`), dibujados a mano con un carril por rol, divididos según cuándo ocurren y numerados por orden y nivel (`1.0_`, `2.0_`, `2.1_`, `2.1.1_`). Deben pasar `~/proyectos/ai-sdlc-skills/sim-template/lint.sh <archivo>` sin errores ni avisos (reglas: `.bpmnlintrc`). Los demás diagramas UML (casos de uso, estados, dominio, secuencia) van en draw.io (`.drawio`).
- **Simulación:** una sola por proyecto, fuera del repositorio, que conserva esos dibujos (`compose.json`) y permite simular todo o una parte. Cada valor se marca `negocio`, `real` (confirmado por el usuario, con fuente) o `supuesto`; el valor base es la situación real. Cómo armarla: `~/proyectos/ai-sdlc-skills/sim-template/TECNICO.md`; cómo usarla: su `README.md`.
- Conversación y Notion en **español**; código, ramas, commits y carpetas (`api-<proyecto>`, `app-<proyecto>`, `infra-<proyecto>`) en **inglés**.
