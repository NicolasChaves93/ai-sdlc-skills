---
name: sdlc-architecture-design
description: Execute Phase 3 of the Agile SDLC (Technical Architecture, Stack Selection, ADRs in Notion, Database/ER Design, Sequence Diagrams, and Evolutionary Roadmap) for any active project in Notion. Use after requirements and business rules are defined, or when designing architecture, data models, and technical enabler tasks (TEC-NN).
---
# SDLC Phase 3 - Architecture, Technical Design, and ADRs (Multi-Project)

Translate technology-agnostic requirements (`RF`/`RNF`) and business rules (`BR-XX`) of the **active Notion project** into architectural decisions, Mermaid technical diagrams (`erDiagram`, `sequenceDiagram`, `flowchart`), and Architecture Decision Records (ADRs).

## Dynamic Project Scoping (consult `NOTION_SCHEMA.md`)

1. Identify the active `Proyecto` (`page_id`) and query its `Requisitos` (especially `RNF`s), `Reglas de negocio`, `PoCs y decisiones`, and highest `TEC-NN` number in `Historias y tareas`.
2. Tailor stack, concurrency, and deployment topology specifically to that project's scale and constraints (e.g., lightweight single-node vs. high-concurrency real-time event system).

## Core Architectural Principles

1. **Pure Domain Isolation:** Isolate business rules (`BR-XX`) in framework-free domain modules so they can be unit-tested independently of delivery transports.
2. **NFR-Driven Design:** Address every `RNF` explicitly (concurrency, latency, data privacy, offline/resilience) with concrete mechanisms.
3. **Evolutionary Roadmap:** Propose pragmatic iterations (MVP → Production Scale) rather than premature over-engineering.

## Workflow

### Step 1: Audit Active Project Requirements & Past ADRs
- Query `Requisitos` and `PoCs y decisiones` filtered by the active `Proyecto`.

### Step 2: Architecture Decision Records (ADRs)
- Draft ADRs (Context, Options Considered, Decision, Trade-offs) ready to store in **`PoCs y decisiones`** (`db: 41ae618d-5d53-815d-9fb6-d48297f1dc72`) linked to the active `Proyecto`.

### Step 3: Technical Diagrams & Physical Schema
- Produce Mermaid diagrams for **`Documentos`** (`Fase = 3 Diseño`, template `PT-IGS` or technical architecture template):
  - **System & Container Architecture** (`flowchart TD`)
  - **Physical Data Model** (`erDiagram` with PKs, FKs, indexes, constraints)
  - **Critical Flows** (`sequenceDiagram`)

### Step 4: Technical Enabler Tasks (`TEC-NN`)
- Propose sequential `TEC-NN` tasks in **`Historias y tareas`** (`db: 41ae618d-5d53-8184-be52-f537089e5943`) linked to the active `Proyecto` and relevant `RNF`s.

## Gotchas

- Always conduct the conversation and write all Notion records in Spanish, unless explicitly requested otherwise.
- Confirm with the user before writing ADRs, technical documents, or `TEC-NN` tasks into Notion.
