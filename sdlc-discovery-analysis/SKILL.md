---
name: sdlc-discovery-analysis
description: Execute Phases 1 and 2 of the Agile SDLC (Requirements Engineering, Business Rules, BPMN As-Is/To-Be Bottleneck Modeling, UML Use Cases, State Machines, Conceptual ER Models, Epics, User Stories with Gherkin/Fibonacci, and Test Case Traceability) dynamically for any project in Notion. Use when transitioning from Phase 0 to formal analysis, defining a new project or module increment, or generating structured backlog items in Notion.
---
# SDLC Phases 1 & 2 - Discovery, Requirements Analysis, and Backlog Structuring (Multi-Project)

Transform validated concepts into structured, traceable, technology-agnostic engineering artifacts stored in Notion (`Documentos`, `Requisitos`, `Reglas de negocio`, `Épicas`, `Historias y tareas`, and `Casos de prueba`), dynamically scoped to whichever project is active.

## Dynamic Project Discovery (Mandatory First Step)

Consult `NOTION_SCHEMA.md` for global database IDs, then **always scope to the active project**:
1. Identify the target `Proyecto` (`page_id`) in `Proyectos activos` (`ds: 41ae618d-5d53-814a-8721-000b00330ce7`).
2. Query `Requisitos` (`ds: 41ae618d-5d53-810f-ad12-000b66155d6c`), `Reglas de negocio` (`ds: 41ae618d-5d53-8156-a96a-000b8180cc4a`), and `Historias y tareas` (`ds: 41ae618d-5d53-81bd-9697-000b39998e0b`) **filtered by that `Proyecto`**:
   - If the project has **0 records**, start sequences at **`RF-01`**, **`RNF-01`**, **`BR-01`**, and **`HU-01` / `TEC-01`**.
   - If the project **already has records**, find the highest existing number per prefix and continue sequentially without collisions.
3. Inspect the `Módulo` property options in Notion (or confirm with the user the module taxonomy for a new project) so tags match the project's domain.

## Mandatory Workspace Rules

1. **Traceability Chain (`RF → HU → BR → Prueba`):**
   - Link every `Historia` directly to `Proyecto`, `Épica`, `Requisitos`, `Módulo`, and applicable `Reglas`.
   - Link every `Caso de prueba` to `Proyecto`, `Historia`, and `Regla` (never directly to `Requisito`).
2. **Item Prefixes:** Use `HU-NN` for user stories, `TEC-NN` for technical/architecture/ADR tasks, and `SOP-NN` for live operations/support tasks.
3. **Epic Sizing:** Group 3 to 8 related `Historias` per `Épica`.
4. **100% Tech-Stack Agnostic:** Keep all Phase 1–2 diagrams, requirements, business rules, and conceptual models completely free of programming languages, frameworks, HTTP endpoints, or SQL data types so non-technical stakeholders understand them and they survive stack changes.

## Workflow

### Step 1: Audit Active Project & Phase Gate
- Summarize existing artifacts for the active project and confirm whether the project should be at `1 Inicio` (`PT-PP`) or `2 Análisis` (`PT-ERS`, `PT-ECU`, `RF`/`RNF`, `BR`, `Épicas`/`Historias`).

### Step 2: Process Optimization Modeling (`BPMN As-Is → Bottlenecks → BPMN To-Be`)
- Map the **current operational process (`As-Is`)** in Mermaid (`flowchart TD` with role swimlanes) to expose manual friction, delays, and operational bottlenecks.
- Identify specific **bottlenecks & improvement opportunities**, then design the **improved target process (`To-Be`)** showing how the software eliminates or automates those bottlenecks.

### Step 3: Formalize Requirements (`RF-NN` / `RNF-NN`) & Pure Business Rules (`BR-NN`)
- **Functional Requirements (`RF-NN`):** System capabilities derived from the `To-Be` flow, tagged with `Módulo` and `MoSCoW` priority.
- **Non-Functional Requirements (`RNF-NN`):** Measurable thresholds (concurrency, latency, availability, security/compliance).
- **Business Rules (`BR-NN`):** Domain invariants, calculations, and transition rules (with DMN-style decision tables for multi-condition logic).

### Step 4: Pure Business Diagrams (Mermaid) & Backlog Decomposition
Produce technology-agnostic diagrams for **`Documentos`** (`PT-ERS` / `PT-ECU`):
1. **Use Case Diagram (`flowchart LR` / UML style):** Actors (e.g., Jugador, Administrador, Sistema) and business actions without UI screens or API endpoints.
2. **State Machine Diagram (`stateDiagram-v2`):** Lifecycle states of core entities (e.g., `CREADA → EN_ESPERA → EN_CURSO → PAUSADA → FINALIZADA`) and the `BR-XX` guard rules governing each transition.
3. **Conceptual Domain Model (`erDiagram`):** Business entities and relationships without physical SQL types (`VARCHAR`, `BIGINT`, indexes).

Then decompose into `Épicas` (3–8 stories each), `Historias` (`Como... quiero... para...`, `Módulo`, `MoSCoW`, `Fibonacci`, `Gherkin` + `DoD`), and `Casos de prueba` linked to `Proyecto`, `Historia`, and `Regla`.

### Step 5: Confirm Before Writing to Notion
Present a summary table of proposed records and write to Notion only after user approval.

## Gotchas

- Always conduct the conversation and write all Notion records in Spanish, unless explicitly requested otherwise.
- Never include SQL types, frameworks, or infrastructure details in Phase 1–2 diagrams; defer physical schemas and C4 diagrams to `sdlc-architecture-design`.
