# AGENTS.md — Orquestador SDLC y Estándares de Ingeniería

Este proyecto sigue una fábrica de software evolutiva en 7 fases con separación estricta entre **Negocio Puro**, **Arquitectura** e **Implementación por Niveles**.

## 1. Roles y Orquestación Activa (`agents-registry.yaml`)
- **Agente Principal (Orquestador): Claude Code (`claude`)** — Recibe las solicitudes, identifica la fase SDLC actual, aplica las compuertas y ejecuta directamente Fases 4–5 (código, TDD, Postman, k6, Docker).
- **Agente Especialista Delegado: Gemini CLI (`gemini`)** — Se invoca automáticamente vía `gemini -p "<instrucción>"` cuando la tarea requiere sincronizar Notion MCP, modelar BPMN/DMN, generar simuladores HTML, redactar ADRs/diagramas C4 (Fases 0–3) o cerrar cortes de fase (Fases 6–7).

## 2. Activación Automática de Skills por Fase
- **Fase 0 (Ideación y Viabilidad):** `sdlc-ideation-brainstorming`
- **Fases 1–2 (Negocio Puro: BPMN, Simulador HTML, DMN, UML, Historias):** `sdlc-discovery-analysis`
- **Fase 3 (Diseño Técnico: C4, Secuencia, ERD Físico, Stack vs. Infra, ADR):** `sdlc-architecture-design`
- **Fases 4–7 (Código por Niveles, QA y Operación):** `sdlc-delivery-operations`
- **Skills de apoyo (Fases 4–5), se combinan con la anterior:**
  - `test-driven-development` — antes de escribir cualquier código de implementación o corrección (Niveles 1–5).
  - `systematic-debugging` — ante cualquier bug, test fallido o comportamiento inesperado, antes de proponer una corrección.
  - `postman-cli` — colecciones y pruebas funcionales de API en `postman/` (desde Nivel 2).
  - `k6-load-testing` — pruebas de carga y escalabilidad (desde Nivel 4).

## 3. Regla de Despacho Automático
Antes de ejecutar cualquier tarea:
1. Consulta `~/proyectos/ai-sdlc-skills/agents-registry.yaml`.
2. Si la fase pertenece a **Claude** (`4, 5`), ejecútala directamente.
3. Si la fase pertenece a **Gemini** (`0, 1, 2, 3, 6, 7`), invócalo automáticamente desde terminal mediante:
   `gemini -p "Usa <skill_correspondiente>. <contexto_y_tarea_detallada>"`
   y presenta el resultado consolidado al usuario.

## 4. Compuertas Obligatorias (Zero-Skip Gates)
1. **Negocio Puro antes de Tecnología:** Prohibido mencionar frameworks, endpoints o tipos SQL en `RF`/`RNF`, tablas DMN (`BR-XX`), casos de uso, máquinas de estado o BPMN. Si cambia el flujo en construcción, actualizar primero el BPMN `To-Be` y las tablas DMN.
2. **ADR Aprobado antes de Código:** Prohibido crear carpetas de código o instalar dependencias sin un ADR aprobado en Notion / `docs/adr/`.
3. **Niveles Evolutivos:** `Nivel 1 (Núcleo Puro)` → `Nivel 2 (API Memoria + Postman)` → `Nivel 3 (SQLite)` → `Nivel 4 (PostgreSQL + k6)` → `Nivel 5 (Frontend)`.
4. **Corte y Freeze 24h:** Sincronizar estado en Notion al cerrar cada nivel y respetar congelamiento de despliegues 24h antes de eventos en vivo.

## 5. Convenciones
- Conversación y Notion en **español**; código, ramas, commits y carpetas (`api-<proyecto>`, `app-<proyecto>`, `infra-<proyecto>`) en **inglés**.
