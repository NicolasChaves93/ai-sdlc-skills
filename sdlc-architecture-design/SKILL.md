---
name: sdlc-architecture-design
description: Execute Phase 3 of the Agile SDLC (Technical Architecture, Evolutionary Backend-First Roadmap, Hexagonal/Clean Domain Isolation, ADRs in Notion, Database/ER Design, and Sequence Diagrams) for any active project. Use after requirements and business rules are defined, or when designing architecture, data models, and technical enabler tasks (TEC-NN).
---
# SDLC Phase 3 - Architecture, Technical Design, and ADRs (Multi-Project)

Translate technology-agnostic requirements (`RF`/`RNF`) and business rules (`BR-XX`) of the **active Notion project** into an evolutionary technical architecture, Mermaid technical diagrams (`erDiagram`, `sequenceDiagram`, `flowchart`), and Architecture Decision Records (ADRs).

## Dynamic Project Scoping (consult `NOTION_SCHEMA.md`)

1. Identify the active `Proyecto` (`page_id`) and query its `Requisitos` (especially `RNF`s), `Reglas de negocio`, `PoCs y decisiones`, and highest `TEC-NN` number in `Historias y tareas`.
2. Adapt technical depth, concurrency mechanisms, and evolution stages to the project's scale and learning/delivery goals.

## Core Architectural Principles

1. **Pure Domain Isolation (Hexagonal / Ports & Adapters):** Isolate business rules (`BR-XX`) and core domain logic in pure, framework-free modules so they can be unit-tested independently of HTTP/WebSockets or database engines.
2. **Evolutionary Backend-First Roadmap (Adaptable by Project):** Unless the project strictly requires a different sequence, structure implementation from the inside out so each layer is validated before adding infrastructure complexity:
   - **Stage 1 — Pure Core (Domain + `BR-XX`):** Pure business logic in memory with zero external dependencies, verified via fast unit tests.
   - **Stage 2 — In-Memory Persistence + Backend API:** Repository ports implemented with temporary in-memory stores (`Map`/arrays) exposed via HTTP/WebSocket contracts to validate API flows early.
   - **Stage 3 — Lightweight Local Database (`SQLite`):** Swap repository adapters to SQLite to validate relational schema, transactions, and SQL queries without external servers.
   - **Stage 4 — Production Database & Scale (`PostgreSQL` / Concurrency):** Swap adapters to production-grade DB (and caching/queues if `RNF`s require high live concurrency) without altering core domain rules.
   - **Stage 5 — Frontend / UI Clients:** Build user interfaces on top of a stable, tested backend API.
3. **NFR-Driven Design:** Address every `RNF` explicitly (concurrency, latency, data privacy, resilience) with concrete mechanisms.

## Workflow

### Step 1: Audit Active Project Requirements & Past ADRs
- Query `Requisitos` and `PoCs y decisiones` filtered by the active `Proyecto`.

### Step 2: Architecture Decision Records (ADRs)
- Draft ADRs (Context, Options Considered, Decision, Trade-offs) ready to store in **`PoCs y decisiones`** (`db: 41ae618d-5d53-815d-9fb6-d48297f1dc72`) linked to the active `Proyecto`.

### Step 3: Technical Diagrams & Physical Schema
- Produce Mermaid diagrams for **`Documentos`** (`Fase = 3 Diseño`, template `PT-IGS` or technical architecture template):
  - **System & Hexagonal Container Architecture** (`flowchart TD`)
  - **Physical Data Model** (`erDiagram` with PKs, FKs, indexes, constraints)
  - **Critical Flows** (`sequenceDiagram`)

### Step 4: Evolutionary Technical Enabler Tasks (`TEC-NN`)
- Propose sequential `TEC-NN` tasks in **`Historias y tareas`** (`db: 41ae618d-5d53-8184-be52-f537089e5943`) aligned with the evolutionary stages and linked to the active `Proyecto` and relevant `RNF`s.

## Gotchas

- Always conduct the conversation and write all Notion records in Spanish, unless explicitly requested otherwise.
- Keep the 5-stage evolutionary roadmap flexible: adapt stage granularity to the size and constraints of each project.
- Confirm with the user before writing ADRs, technical documents, or `TEC-NN` tasks into Notion.
