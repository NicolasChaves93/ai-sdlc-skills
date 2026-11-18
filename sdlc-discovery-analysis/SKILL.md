---
name: sdlc-discovery-analysis
description: Execute Phases 1 and 2 of the Agile SDLC (Project Initiation, Requirements Engineering, Business Rules, BPMN/UML Modeling, Epics, User Stories with Gherkin/Fibonacci, and Test Case Traceability). Use when transitioning from Phase 0 ideation to formal analysis, defining a new module or sprint increment, or generating structured requirements and backlog items in Notion.
---
# SDLC Phases 1 & 2 - Discovery, Requirements Analysis, and Backlog Structuring

Transform validated concepts from Phase 0 into structured, traceable engineering artifacts stored in Notion (`Documentos`, `Requisitos`, `Reglas de negocio`, `Épicas`, `Historias y tareas`, and `Casos de prueba`), completely decoupled from specific tech stack choices.

## Notion Schema & IDs Reference

Always read `NOTION_SCHEMA.md` in the skills repository before querying or creating records. Key IDs:
- **Proyecto activo (`🚀 Plataforma de Juegos para Eventos v2`):** `41ae618d-5d53-813a-930c-c6b1aa70d536`
- **Documentos:** `db: 41ae618d-5d53-8108-94d8-ccb73d7034f2` | `ds: 41ae618d-5d53-81d3-a930-000b170506e9`
- **Requisitos:** `db: 41ae618d-5d53-815d-a02e-fab86aa23944` | `ds: 41ae618d-5d53-810f-ad12-000b66155d6c`
- **Reglas de negocio:** `db: 41ae618d-5d53-8172-81e5-df5d18954a99` | `ds: 41ae618d-5d53-8156-a96a-000b8180cc4a`
- **Épicas:** `db: 41ae618d-5d53-819c-a5d5-e1edd5aaf08e` | `ds: 41ae618d-5d53-8152-a7f9-000b63a1bcab`
- **Historias y tareas:** `db: 41ae618d-5d53-8184-be52-f537089e5943` | `ds: 41ae618d-5d53-81bd-9697-000b39998e0b`
- **Casos de prueba:** `db: 41ae618d-5d53-81c1-92e2-fd49db796abf` | `ds: 41ae618d-5d53-8171-b312-000b17fc8c7d`

## Mandatory Workspace Rules

1. **Sequential Numbering Check:** Before creating new `RF-NN`, `RNF-NN`, or `BR-NN` items, query the existing `Requisitos` or `Reglas de negocio` data source filtered by `Proyecto` to find the highest existing code and continue sequentially without collisions.
2. **Valid `Módulo` Values Only:** Tag every `Requisito` and `Historia` strictly with one of the 8 schema values: `Sorteo`, `Mejores servidores`, `Trivia`, `Trivia interactiva`, `Administración`, `Portal participante`, `Infraestructura`, `General`.
3. **Traceability Chain (`RF → HU → BR → Prueba`):**
   - Link every `Historia` directly to `Proyecto`, `Épica`, `Requisitos`, `Módulo`, and applicable `Reglas`.
   - Link every `Caso de prueba` to `Proyecto`, `Historia`, and `Regla` (never directly to `Requisito`).
4. **Epic Sizing:** Group 3 to 8 related `Historias` per `Épica`.
5. **Tech-Stack Agnostic:** Keep requirements, business rules, and conceptual diagrams focused on business behavior and domain entities, leaving infrastructure/framework choices for Phase 3 (`sdlc-architecture-design`).

## Workflow

### Step 1: Audit Existing Records & Phase Gate
- Query Notion (`Documentos`, `Requisitos`, `Épicas`, `Historias y tareas`) for the target `Proyecto` and `Módulo` to avoid duplicating existing work.
- Confirm whether the project phase in Notion should be at `1 Inicio` (when drafting `PT-PP` / Concept Brief) or advanced to `2 Análisis` (when formalizing `PT-ERS`, `RF`/`RNF`, `BR`, and `Épicas`/`Historias`).

### Step 2: Formalize Requirements (`RF-NN` / `RNF-NN`) & Business Rules (`BR-NN`)
- **Functional Requirements (`RF-NN`):** Clear system capabilities tagged with `Módulo` and priority (`MoSCoW`).
- **Non-Functional Requirements (`RNF-NN`):** Measurable thresholds for live event concurrency, latency, availability, and security.
- **Business Rules (`BR-NN`):** Explicit domain invariants, scoring formulas, tie-breaker logic, and state transitions (include a Markdown Decision Table / DMN-style matrix when rules have multiple conditions).

### Step 3: Conceptual Process & Domain Modeling (Mermaid)
- Generate technology-agnostic Mermaid diagrams inside the `PT-ERS` / `PT-ECU` document:
  - **Process Flow (BPMN-style `flowchart TD`):** End-to-end operational flow across roles (e.g., Organizador, Participante, Sistema).
  - **Conceptual Domain Model (`erDiagram`):** Core domain entities and cardinalities without physical SQL types.

### Step 4: Decompose into Epics, User Stories (`HU`), and Test Cases
For each `Épica` (3–8 stories), draft `Historias` containing:
- **Narrative:** `Como [rol], quiero [acción], para [beneficio de negocio].`
- **Metadata:** `Módulo`, `Prioridad (MoSCoW)`, `Puntos (Fibonacci: 1, 2, 3, 5, 8, 13)`, `Valor de negocio`.
- **Acceptance Criteria (Gherkin):** `Dado [contexto] / Cuando [evento] / Entonces [resultado verificable]`.
- **Definition of Done (DoD)** and linked `Casos de prueba` (`Dado/Cuando/Entonces` + datos de prueba) tied to the `Historia` and `BR-NN`.

### Step 5: Confirmation Before Bulk Creation in Notion
Present a concise summary table of the proposed `RF`/`RNF`, `BR`, `Épicas`, `Historias`, and `Casos de prueba` to the user. Once approved, create the records in Notion respecting the exact parent `database_id`s and relational links, pacing writes cleanly to respect free-tier API rate limits.

## Gotchas

- Always conduct the conversation and write all Notion records and deliverables in Spanish, unless explicitly instructed otherwise.
- When creating pages in Notion via MCP, inspect one existing record (`API-retrieve-a-database` or `API-query-data-source` with `page_size: 1`) if exact property key names or types need confirmation before batch insertion.
- Never assign `Cliente` to `ColombianCode`; keep the existing project relation (`Compensar · Área de bienestar` or empty for standalone internal products).
