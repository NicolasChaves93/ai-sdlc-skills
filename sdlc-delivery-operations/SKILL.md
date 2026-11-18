---
name: sdlc-delivery-operations
description: Execute Phases 4, 5, 6, and 7 of the Agile SDLC (Implementation, QA Test Cases & Verification, Sprint Iterations, Operations SOP, and Living Documentation split between Git Repo and Notion) for any active project. Use when implementing stories, writing tests for BR-XX rules, populating Casos de prueba in Notion, planning Iteraciones, or running operational checklists and retrospectives.
---
# SDLC Phases 4–7 - Implementation, QA, Delivery, and Operations (Multi-Project)

Guide execution from code implementation (`4 Construcción`) through QA (`5 Entrega`), live operations (`6 Operación`), and closure (`7 Cierre`) for whichever project and local repository are currently active.

## Dynamic Project Scoping (consult `NOTION_SCHEMA.md`)

1. Identify the active `Proyecto` (`page_id`) in Notion and the active local Git repository directory.
2. Query `Iteraciones`, `Historias y tareas`, `Reglas de negocio`, and `Casos de prueba` **filtered by that `Proyecto`**.

## Living Documentation Split (Git vs. Notion)

- **Active Code Repository:** `README.md`, `CHANGELOG.md`, API contracts, runbooks, environment setup, and automated unit/integration tests covering `BR-XX`.
- **Notion Workspace:** `Iteraciones` (sprint scope), `Historias y tareas` status updates, `Casos de prueba` (`RF → HU → BR → Prueba`), and `Documentos` (Sprint Review, Operational Checklist, Lessons Learned).

## Workflow

### Step 1: Sprint / Increment Scoping (`Iteraciones`)
- Query `Iteraciones` (`ds: 41ae618d-5d53-812e-ae57-000bf3a3593a`) for the active `Proyecto` and link selected `HU-NN` / `TEC-NN` items.

### Step 2: Test-First Verification (`BR-XX` & `Casos de prueba`)
- Write isolated unit tests for business rules (`BR-XX`) in the repository first.
- Generate structured **`Casos de prueba`** (`db: 41ae618d-5d53-81c1-92e2-fd49db796abf`) in Notion linked strictly to `Proyecto`, `Historia`, and `Regla` (`BR-XX`) — never directly to `Requisito`.

### Step 3: Implementation & Operational Readiness (`SOP-NN`)
- Implement modular code matching Phase 3 architecture and verify operational/deployment runbooks (`SOP-NN`) when moving to `6 Operación`.

### Step 4: Sprint Review, Retrospective & Next Loop
- Update item statuses in Notion, log Sprint Review / Lessons Learned in **`Documentos`**, and identify the next backlog slice to loop back into Phase 1/2 or Phase 3.

## Gotchas

- Always conduct the conversation and write all Notion records in Spanish, unless explicitly requested otherwise.
- Never link `Casos de prueba` directly to `Requisitos`; always close the chain via `Historia` and `Regla`.
