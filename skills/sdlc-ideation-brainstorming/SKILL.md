---
name: sdlc-ideation-brainstorming
description: Execute Phase 0 of the Agile SDLC (Ideation, Product Discovery Brainstorming, and Proof-of-Concept Exploration) for any new or existing project in Notion. Use when the user has a raw idea, wants to start a new software project or product module, needs to validate a Proof of Concept (PoC), or is unsure how to approach a problem before formal requirements.
---
# SDLC Phase 0 - Ideation and Product Brainstorming (Multi-Project)

Guide the user through Phase 0 (Ideation and Exploration) of an iterative Agile SDLC aligned with ColombianCode's Notion relational funnel (`Clientes → Proyectos → Bases hijas`), adapting dynamically to whether the initiative is a **brand-new project** or a **new module inside an existing project**.

## Clarification Gate (Mandatory Before Generating Outputs)

Never jump straight into full specifications or code when an idea is still open-ended. Ask **2 to 3 targeted, Socratic questions at a time** to uncover:
- Whether this idea is a **new standalone project** (with its own client, methodology, and modules) or a **new module/feature inside an existing project**.
- Who the target client/ally or end users are, and what measurable outcome defines success.
- Hard constraints (concurrency, budget, integrations, or target deadlines).

## Notion Workspace Rules (consult `NOTION_SCHEMA.md`)

1. **Dynamic Project Scoping:** Query `Proyectos activos` (`ds: 41ae618d-5d53-814a-8721-000b00330ce7`) to verify if the project already exists. Never hardcode modules or IDs from unrelated projects.
2. **Client Relationship:** `ColombianCode` is the workspace root, not a client record. For `Producto propio`, link to an active `Canal / Aliado` if one exists, or leave `Cliente` empty.
3. **Traceability Chain:** Respect `Proyecto → Requisito (RF/RNF) → Épica → Historia (HU) ↔ Regla (BR) → Caso de prueba`.

## Workflow

### Step 0: Check Existing Context First
- If targeting an existing project, query its `Documentos`, `PoCs y decisiones`, and `Requisitos` in Notion, summarize what exists, and focus your 2–3 Socratic questions on open gaps or risks.
- If starting a brand-new project, clarify the core problem, target users, and constraints first.

### Step 1: Socratic Exploration (Zero Assumptions)
Iterate in short conversational turns (2–3 focused questions per turn) until the value proposition and boundaries are clear.

### Step 2: Divergent Options and Trade-Offs
Present **2 to 3 distinct approaches**:
- **Option A (Lean / Low-Effort):** Fastest way to validate value.
- **Option B (Balanced / Recommended):** Best trade-off between impact and build effort.
- **Option C (Ambitious / Differentiator):** High-impact capability for later iterations.

### Step 3: Proof of Concept (PoC) Scoping (When Needed)
For high-uncertainty assumptions, define a time-boxed PoC (Hypothesis, Minimal Experiment, Pass/Fail Criteria) ready to log in **`PoCs y decisiones`** (`db: 41ae618d-5d53-815d-9fb6-d48297f1dc72`).

### Step 4: Notion Sync & Hand-Off to Phase 1
Once approved:
1. If new, create the row in **`Proyectos activos`** (`db: 41ae618d-5d53-8114-84ff-c6242f64b641`) with `Estado = Ideación` and `Fase = 1 Inicio` (and create the `Cliente` first if needed).
2. Create the Concept Brief / `PT-PP` in **`Documentos`** (`db: 41ae618d-5d53-8108-94d8-ccb73d7034f2`) and any PoC in **`PoCs y decisiones`**.
3. Write `.sdlc/00-idea-brief.md` in the project: title, date, type (`Cliente Externo` | `Proyecto Propio`), complexity 1–5; 1) problem and success criterion; 2) scope: Core (MVP), optional, out of scope; 3) assumptions and risks; 4) preliminary hours/sprints range.
4. Route by type: external client → **`propuesta-comercial`** (Claude) and wait for the client's approval; own project or approved increment → **`sdlc-discovery-analysis`**.

## Gotchas

- Always conduct the conversation and write all Notion records in Spanish, unless explicitly requested otherwise.
- Keep questioning iterative (2–3 questions per turn).
