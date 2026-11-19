---
name: sdlc-delivery-operations
description: Execute Phases 4, 5, 6, and 7 of the Agile SDLC (Implementation, QA Test Cases & Verification, Sprint Iterations, Operations SOP, and Living Documentation split between Git Repo and Notion) for any active project. Use when implementing stories, writing tests for BR-XX rules, populating Casos de prueba in Notion, planning Iteraciones, or running operational checklists and retrospectives.
---
# SDLC Phases 4–7 - Implementation, QA, Delivery, and Operations (Multi-Project)

Guide execution from code implementation (`4 Construcción`) through QA (`5 Entrega`), live operations (`6 Operación`), and closure (`7 Cierre`) for whichever project and local repository are currently active.

## Mandatory Pre-Implementation Gate (Stop Before Writing Any Code!)

Before creating directories, boilerplate, or source code files:
1. **Verify Phase 3 (`sdlc-architecture-design`) Completion:** Check Notion (`PoCs y decisiones` for an approved Stack ADR) and the local repository (`docs/adr/` or existing project files).
2. **If no Stack ADR / language decision exists yet:** **STOP immediately.** Do NOT guess a language (Python, Go, Java, .NET, JS/TS) and do NOT scaffold files. Instead, trigger **`sdlc-architecture-design`** first (running the Greenfield vs. `v1` diagnostic questions, evaluating Stack vs. Free-Tier/Hosting limits, and getting explicit user approval on the language and 5-level evolutionary plan).

## Dynamic Project Scoping (consult `NOTION_SCHEMA.md`)

1. Identify the active `Proyecto` (`page_id`) in Notion and the active local Git repository directory.
2. Query `Iteraciones`, `Historias y tareas`, `Reglas de negocio`, and `Casos de prueba` **filtered by that `Proyecto`**.

## Living Documentation Split (Git vs. Notion)

- **Active Code Repository:** `README.md`, `CHANGELOG.md`, `docs/adr/`, API contracts, runbooks, environment setup, and automated unit/integration tests covering `BR-XX`.
- **Notion Workspace:** `Iteraciones` (sprint scope), `Historias y tareas` status updates, `Casos de prueba` (`RF → HU → BR → Prueba`), and `Documentos` (Sprint Review, Operational Checklist, Lessons Learned).

## Workflow

### Step 1: Verify Architecture Gate & Sprint Scoping (`Iteraciones`)
- Confirm the approved tech stack and current Evolutionary Level (`Level 1: Pure Core` → `Level 5: Frontend`).
- Query `Iteraciones` (`ds: 41ae618d-5d53-812e-ae57-000bf3a3593a`) for the active `Proyecto` and link selected `HU-NN` / `TEC-NN` items.

### Step 2: Test-First Verification (`BR-XX` & `Casos de prueba`)
- Write isolated unit tests for business rules (`BR-XX`) in the repository first, using only the approved language and pure domain constructs (zero web frameworks or DB drivers in Level 1).
- Generate structured **`Casos de prueba`** (`db: 41ae618d-5d53-81c1-92e2-fd49db796abf`) in Notion linked strictly to `Proyecto`, `Historia`, and `Regla` (`BR-XX`) — never directly to `Requisito`.

### Step 3: Implementation & Operational Readiness (`SOP-NN`)
- Implement modular code matching Phase 3 hexagonal boundaries and verify operational/deployment runbooks (`SOP-NN`) when moving to `6 Operación`.

### Step 4: Sprint Review, Retrospective & Next Loop
- Update item statuses in Notion, log Sprint Review / Lessons Learned in **`Documentos`**, and identify the next backlog slice to loop back into Phase 1/2 or Phase 3.

## Gotchas

- Always conduct the conversation and write all Notion records in Spanish, unless explicitly requested otherwise.
- Never write or scaffold code before Phase 3 has locked the tech stack and infrastructure constraints with the user.
- Never link `Casos de prueba` directly to `Requisitos`; always close the chain via `Historia` and `Regla`.

## Testing Pyramid & Tooling by Evolutionary Stage

- **Unit Tests (Stage 1+):** Fast in-memory tests (`pytest` / `go test` / `JUnit`) validating pure business rules (`BR-XX`) with zero I/O.
- **API Functional & Exploratory Tests (Stage 2+ — Postman Desktop & CLI):** Use Postman for interactive endpoint exploration during development, functional contract assertions (`pm.test`), regression runs via `postman collection run`, and shareable API documentation (`postman/`).
- **Persistence Integration Tests (Stages 3–4):** Automated repository/database tests verifying SQLite and PostgreSQL transactions, constraints, and connection pooling.
- **Load & Concurrency Tests (Stage 4 — `k6`):** Store `k6` scripts in `k6/` to validate `RNF` concurrency thresholds (e.g., burst traffic, p95 latency, WebSocket/HTTP throughput) against staging/production infrastructure limits.

## Notion Sync & Operational Freeze Rules (Phases 4–6)

- **Mandatory State Sync on Milestone Advance:** Whenever an evolutionary stage (`Level 1` to `Level 5`) or module slice completes, update the `Proyecto` phase in Notion (`4 Construcción` / `5 Entrega` / `6 Operación`), verify Mermaid diagram syntax before moving `Documentos` from `Borrador` to `Aprobado`, and ensure every implemented `BR-XX` rule has matching `Casos de prueba` linked to its `HU-NN`.
- **Live Event Deployment Freeze (24h Rule):** When operating under `Scrumban` or `Kanban` for live events, enforce a strict **24-hour pre-event deployment freeze** (`SOP-NN` checklist mode only — no schema migrations, refactors, or unverified deploys within 24h of a scheduled live session).
