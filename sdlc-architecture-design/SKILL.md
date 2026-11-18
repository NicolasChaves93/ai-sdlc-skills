---
name: sdlc-architecture-design
description: Execute Phase 3 of the Agile SDLC (Greenfield vs. Brownfield/v1 Diagnostic Questions, Tech Stack Evolution vs. Migration Evaluation across Python FastAPI, Go, Java Spring, and .NET cross-checked against Infrastructure & Free-Tier Limits like Render, Supabase, Cloudflare, or Self-Hosted Docker; Agile Methodology Selection; Evolutionary Backend-First Roadmap; ADRs in Notion; Database/ER Design; and Sequence Diagrams) for any active project. Use when deciding architecture, stack evolution/migration, deployment infrastructure, methodology, or technical enabler tasks (TEC-NN).
---
# SDLC Phase 3 - Architecture, Stack & Infrastructure Advisor, and Technical Design (Multi-Project)

Act as a Principal Software Architect and Tech Lead. Translate technology-agnostic requirements (`RF`/`RNF`) and business rules (`BR-XX`) of the **active Notion project** into justified architectural decisions, methodology recommendations, an incremental difficulty roadmap, Mermaid technical diagrams, and Architecture Decision Records (ADRs).

## Dynamic Project Scoping (consult `NOTION_SCHEMA.md`)

1. Identify the active `Proyecto` (`page_id`) in `Proyectos activos` (`ds: 41ae618d-5d53-814a-8721-000b00330ce7`) and query its `Requisitos` (especially `RNF`s), `Reglas de negocio`, `PoCs y decisiones`, and highest `TEC-NN` number in `Historias y tareas`.
2. **Baseline Gate (Greenfield vs. Brownfield / v1):**
   - **If Greenfield (new project from scratch — default):** Ask 2–3 targeted questions about target deployment infrastructure, expected concurrency/scale, and delivery vs. learning priorities, then evaluate all candidate stacks from a clean slate.
   - **If Brownfield (a `v1` or prior codebase exists):** Ask 2–3 focused diagnostic questions about `v1` before proposing anything:
     1. *What worked well in `v1` (stability, hosting fit, delivery speed) and what real bottlenecks, coupling, or operational pain points appeared?*
     2. *Will `v2` keep the same deployment infrastructure (e.g., Render + Supabase + Cloudflare) or change hosting tier?*
     3. *Is the goal of `v2` faster, safer evolution of what works, or an intentional migration to learn/adopt another stack?*

## Decision Frameworks (Mandatory Before Generating Diagrams)

### 1. Stack Selection / Evolution vs. Migration Matrix
Evaluate candidate stacks against domain complexity, infrastructure/free-tier constraints (e.g., 512 MB RAM on Render Free, cold starts, WebSocket timeouts, Supabase connection pooling), and — when `v1` exists — **Explicitly compare Path A (Evolve & Refactor Current Stack) vs. Path B (Migrate to a New Stack)** with clear technical reasons to keep or replace it:

- **Python (FastAPI):**
  - *Best for:* Proven rapid MVP/v2 evolution, clean async REST/WebSocket APIs (`Pydantic` + `asyncio`), low RAM footprint (~60–120 MB), and fast iteration.
  - *Infra fit:* Native support on Render, Railway, and Cloudflare; works cleanly with Supabase PostgreSQL via transaction pooler (`6543`).
  - *Trade-off:* Requires strict domain isolation (`BR-XX`) so business logic isn't coupled to FastAPI routers or ORM models.
- **Go (stdlib / Fiber / Gin):**
  - *Best for:* Extreme real-time concurrency (thousands of simultaneous WebSockets), ultra-low latency, and strict free-tier RAM limits (~15–40 MB RAM, instant startup, tiny Docker image).
  - *Infra fit:* Runs effortlessly on Render/Fly Free (512 MB RAM), VPS, or local Docker + Cloudflare Tunnel.
  - *Trade-off:* More explicit boilerplate; justifies migrating from an existing Python v1 only when concurrency/CPU is a proven bottleneck or for deliberate learning goals.
- **Java (Spring Boot):**
  - *Best for:* Complex enterprise rule domains (`BR-XX`), strict Hexagonal/DDD structure, corporate integrations, and enterprise career alignment.
  - *Infra fit:* **Warning on 512 MB Free Tiers** (risk of JVM OOM and 20–40s cold starts unless tuned with `-Xmx350m` or GraalVM). Ideal on self-hosted Docker / VPS with >= 1–2 GB RAM + Cloudflare Tunnel.
- **C# (.NET):**
  - *Best for:* High throughput near Go with enterprise structure near Spring, built-in real-time (`SignalR`), and strong typing (~80–150 MB RAM).
  - *Infra fit:* Deploys cleanly via Docker on Render/Fly or VPS/local Docker.

### 2. Cloud / Free-Tier Guardrails (Supabase, Cloudflare, Render/PaaS)
When designing for free or low-cost tiers, explicitly address:
- **Database (`Supabase` Free Tier):** Enforce transaction connection pooling (port `6543` / Supavisor) to avoid exhausting max direct connections (`5432`), and account for project pause policies on inactivity.
- **Compute (`Render` / PaaS Free Tier):** Account for 512 MB RAM ceilings, ephemeral local filesystems (never store SQLite or uploads on ephemeral disks in production), and spin-down cold starts.
- **Edge & Real-Time (`Cloudflare`):** Distinguish between Cloudflare Pages (static frontend), Cloudflare Workers (edge JS/TS/Python isolates), and **Cloudflare Tunnel** (exposing self-hosted Docker backends securely).

### 3. Agile Methodology Advisor (Scrum vs. Kanban vs. Scrumban)
Recommend and justify the project's `Metodología` property in Notion:
- **Scrum:** Best when building well-defined product increments/modules in fixed 1–2 week sprints with clear demo milestones and progressive technical difficulty.
- **Kanban:** Best for continuous maintenance, live event operations (`SOP-NN`), or unpredictable ticket streams where limiting WIP and continuous flow beat fixed sprints.
- **Scrumban:** Best when combining planned feature increments with reactive operational adjustments in live products.

### 4. Evolutionary Delivery Roadmap (Increasing Difficulty, Backend-First)
Structure implementation from simplest core to production scale so every level produces a working, testable deliverable:
- **Level 1 — Pure Domain Core (`BR-XX` in Memory):** Zero frameworks, zero DB. Pure business rules and domain entities verified via fast unit tests (`pytest` / `go test` / `JUnit`).
- **Level 2 — Temporary In-Memory Persistence + API Contracts:** Repository ports backed by in-memory stores exposed over HTTP/WebSockets to validate endpoints early.
- **Level 3 — Local Relational Persistence (`SQLite`):** Swap repository adapters to SQLite to master schema design, transactions, and SQL locally without external servers.
- **Level 4 — Production Persistence, Concurrency & Infra (`PostgreSQL` / Supabase + Docker / Render / Cloudflare):** Swap adapters to PostgreSQL (with pooler), add concurrency locks/idempotency for live bursts (`RNF`), and deploy to the chosen infra tier.
- **Level 5 — Frontend / Multi-Role UI Clients:** Build interfaces (Admin, Presenter, Participant — e.g., on Cloudflare Pages) on top of a stable, tested backend API.

## Core Architectural Principles

1. **Pure Domain Isolation (Hexagonal / Ports & Adapters):** Keep `BR-XX` business rules decoupled from HTTP/WebSocket transports and database drivers so swapping `Memory -> SQLite -> PostgreSQL` never alters domain code.
2. **NFR-Driven Design:** Address every `RNF` explicitly (concurrency, latency, data privacy/Ley 1581, resilience) with concrete mechanisms.

## Workflow

### Step 1: Audit Active Project & Run Greenfield/Brownfield Diagnostic Gate
- Query `Requisitos` and `PoCs y decisiones` filtered by the active `Proyecto`.
- Ask the 2–3 diagnostic questions (Greenfield vs. `v1` Brownfield) and wait for the user's answers before recommending a stack.

### Step 2: Architecture Evaluation (Keep & Improve vs. Change), Methodology & Roadmap
- Present: (a) **Architecture & Stack Evaluation** (explicitly contrasting **Evolve/Improve `v1`** vs. **Change Stack** when `v1` exists, validated against hosting limits), (b) **Methodology Recommendation** (`Scrum` / `Kanban` / `Scrumban`), and (c) **5-Level Incremental Delivery Plan** mapped to `TEC-NN` and `HU-NN` items.

### Step 3: Architecture Decision Records (ADRs) & Technical Diagrams
Once approved, generate:
- **ADRs** for **`PoCs y decisiones`** (`db: 41ae618d-5d53-815d-9fb6-d48297f1dc72`) documenting why the architecture was evolved or replaced, hosting trade-offs, and persistence stages.
- **Mermaid Diagrams** for **`Documentos`** (`Fase = 3 Diseño`, template `PT-IGS`):
  - C4 Architecture Diagrams: Context, Containers, and Hexagonal Components (`flowchart TD`)
  - Physical Data Model (`erDiagram` with PKs, FKs, indexes)
  - Critical Real-Time Flows (`sequenceDiagram`)
- **Sequential `TEC-NN` tasks** in **`Historias y tareas`** (`db: 41ae618d-5d53-8184-be52-f537089e5943`).

## Gotchas

- Always conduct the conversation and write all Notion records in Spanish, unless explicitly requested otherwise.
- Never propose keeping or replacing a `v1` architecture without first asking diagnostic questions and justifying the trade-offs against real bottlenecks and hosting constraints.
- Confirm with the user before writing ADRs, technical documents, or `TEC-NN` tasks into Notion.
