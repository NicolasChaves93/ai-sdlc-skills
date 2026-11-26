---
name: sdlc-discovery-analysis
description: Execute Phases 1 and 2 of the Agile SDLC (Requirements Engineering, DMN Decision Tables for Business Rules, BPMN As-Is/To-Be Bottleneck Modeling & Interactive Flow Simulation, UML Use Cases, State Machines, Conceptual ER Models, Epics, User Stories with Gherkin/Fibonacci, and Test Case Traceability) dynamically for any project in Notion. Use when transitioning from Phase 0 to formal analysis, defining a new project or module increment, or generating structured backlog items in Notion.
---
# SDLC Phases 1 & 2 - Discovery, Requirements Analysis, and Backlog Structuring (Multi-Project)

Transform validated concepts into structured, traceable, technology-agnostic engineering artifacts stored in Notion (`Documentos`, `Requisitos`, `Reglas de negocio`, `Épicas`, `Historias y tareas`, and `Casos de prueba`), dynamically scoped to whichever project is active.

## Dynamic Project Discovery (Mandatory First Step)

Consult `NOTION_SCHEMA.md` for global database IDs, then **always scope to the active project**:
1. Identify the target `Proyecto` (`page_id`) in `Proyectos activos` (`ds: 41ae618d-5d53-814a-8721-000b00330ce7`).
2. Query `Requisitos` (`ds: 41ae618d-5d53-810f-ad12-000b66155d6c`), `Reglas de negocio` (`ds: 41ae618d-5d53-8156-a96a-000b8180cc4a`), and `Historias y tareas` (`ds: 41ae618d-5d53-81bd-9697-000b39998e0b`) **filtered by that `Proyecto`**:
   - If the project has **0 records**, start sequences at **`RF-01`**, **`RNF-01`**, **`BR-01`**, and **`HU-01` / `TEC-01`**.
   - If the project **already has records**, find the highest existing number per prefix and continue sequentially without collisions.
3. Inspect the `Módulo` property options in Notion (or confirm the module taxonomy for a new project) so tags match the project's domain.

## Mandatory Workspace Rules

1. **Traceability Chain (`RF → HU → BR → Prueba`):**
   - Link every `Historia` directly to `Proyecto`, `Épica`, `Requisitos`, `Módulo`, and applicable `Reglas`.
   - Link every `Caso de prueba` to `Proyecto`, `Historia`, and `Regla` (never directly to `Requisito`).
2. **Item Prefixes:** Use `HU-NN` for user stories, `TEC-NN` for technical/architecture/ADR tasks, and `SOP-NN` for live operations/support tasks.
3. **Epic Sizing:** Group 3 to 8 related `Historias` per `Épica`.
4. **100% Tech-Stack Agnostic:** Keep all Phase 1–2 diagrams, requirements, business rules, DMN tables, and conceptual models completely free of programming languages, frameworks, HTTP endpoints, or SQL data types.

## Workflow

### Step 1: Audit Active Project & Phase Gate
- Summarize existing artifacts for the active project and confirm whether the project should be at `1 Inicio` (`PT-PP`) or `2 Análisis` (`PT-ERS`, `PT-ECU`, `RF`/`RNF`, `BR`, `Épicas`/`Historias`).

### Step 2: Process Optimization (`BPMN As-Is → Simulation & Bottlenecks → BPMN To-Be`)
- Map the **current operational process (`As-Is`)** in Mermaid (`flowchart TD` with role swimlanes) to expose manual friction and delays.
- **Test the flow before any code** with the shared simulator `~/proyectos/ai-sdlc-skills/sim-template` (do not build a one-off HTML simulator):
  1. The BPMN is drawn in Camunda Modeler (pool, one lane per role, readable element IDs, a single start event) and saved as `<workspace>/models/<model>.bpmn`.
  2. The workspace is a folder outside the project repo (e.g. `~/proyectos/sim-<project>`); copy the layout of `sim-template/examples/permisos`: `workspace.json` and `scenarios/<model>.json` (times, probabilities, resources keyed by element ID). Mark every value as `negocio` or `supuesto`.
  3. Optional project indicators go in `workspace.json` → `ui` (see the template README).
- **Formats:** processes are BPMN (`.bpmn`, standard below). Every other diagram (UML use cases, state machines, domain model, sequence) is delivered as a draw.io file (`.drawio`).
- **Diagram standard (mandatory before showing any BPMN):** hand-laid diagrams keep one lane per role and must pass `~/proyectos/ai-sdlc-skills/sim-template/lint.sh <file>.bpmn` with no errors **and no warnings** (rules in the template README; `setup.sh` copies them as `.bpmnlintrc` into each project). Number files and pool titles by order and level (`1.0_`, `2.0_`, `2.1_`, `2.1.1_`), and name each collapsed call box with the number of the diagram it opens. Split long processes by when they happen (e.g. preparation vs. event day) and keep rarely used operations in their own diagram.
- **Always finish with the visual model running:** start `sim-template/run.sh <workspace> [port]` in the background, check `http://127.0.0.1:<port>/api/project` answers, and give the user that URL so they can test it. Report bottlenecks from the run. The step is not done until the user has the URL; if you cannot keep a server running (non-interactive delegate), hand the exact command to the orchestrator, which must run it.
- Design the **improved target process (`To-Be`)** showing how the system eliminates those bottlenecks, and keep this BPMN updated whenever downstream phases uncover flow adjustments.

### Step 3: Formalize Requirements (`RF-NN` / `RNF-NN`) & DMN Business Rules (`BR-NN`)
- **Functional Requirements (`RF-NN`):** System capabilities derived from the `To-Be` flow, tagged with `Módulo` and `MoSCoW` priority.
- **Non-Functional Requirements (`RNF-NN`):** Measurable thresholds (concurrency, latency, availability, compliance).
- **Business Rules (`BR-NN`) with DMN Decision Tables:** Express every multi-condition business rule, scoring formula, eligibility filter, or tie-breaker as a formal **DMN Decision Table** (`Hit Policy`: `Unique` / `First` / `Collect`, `Input` columns, `Output` columns) inside Notion's `Reglas de negocio` so domain unit tests map 1-to-1 to DMN rows.

### Step 4: Pure Business Diagrams (Mermaid) & Backlog Decomposition
Produce technology-agnostic diagrams for **`Documentos`** (`PT-ERS` / `PT-ECU`):
1. **Use Case Diagram (`flowchart LR` / UML style):** Actors and business actions without UI screens or API endpoints.
2. **State Machine Diagram (`stateDiagram-v2`):** Lifecycle states of core entities (`CREADA → EN_ESPERA → EN_CURSO → PAUSADA → FINALIZADA`) and the `BR-XX` guard rules governing each transition.
3. **Conceptual Domain Model (`erDiagram`):** Business entities and relationships without physical SQL types (`VARCHAR`, `BIGINT`, indexes).

Then decompose into `Épicas` (3–8 stories each), `Historias` (`Como... quiero... para...`, `Módulo`, `MoSCoW`, `Fibonacci`, `Gherkin` + `DoD`), and `Casos de prueba` linked to `Proyecto`, `Historia`, and `Regla`.

### Hand-off file
Read `.sdlc/00-idea-brief.md` (and the approved proposal option for clients). Write the increment's stories, `BR-XX`, Gherkin scenarios and committed dates to `.sdlc/active/01-stories.md`, with no technology names. The user approves before `phase_1_2_stories` is set.

### Step 5: Confirm Before Writing to Notion
Present a summary table of proposed records and write to Notion only after user approval.

## Gotchas

- Always conduct the conversation and write all Notion records in Spanish, unless explicitly requested otherwise.
- Never include SQL types, frameworks, or infrastructure details in Phase 1–2 diagrams; defer physical schemas and C4 diagrams to `sdlc-architecture-design`.
