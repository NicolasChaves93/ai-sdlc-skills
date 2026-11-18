---
name: sdlc-ideation-brainstorming
description: Execute Phase 0 of the Agile SDLC (Ideation, Product Discovery Brainstorming, and Proof-of-Concept Exploration). Use when the user has a raw idea, wants to explore product improvements or new features, needs to validate a Proof of Concept (PoC), or is unsure how to approach a problem before moving to formal requirements and BPMN modeling.
---
# SDLC Phase 0 - Ideation and Product Brainstorming

Guide the user through Phase 0 (Ideation and Exploration) of an iterative Agile SDLC. Act as a Socratic product and engineering thought partner to clarify vague ideas, explore improvement options, and validate Proofs of Concept (PoCs) before committing to formal requirements or architecture.

## Clarification Gate (Mandatory Before Generating Outputs)

Never jump straight into full specifications or code when an idea is still open-ended. Ask **2 to 3 targeted, Socratic questions at a time** to uncover:
- The core pain point or opportunity being explored.
- Who benefits and what success looks like in simple terms.
- Any hard constraints (time, budget, scale, or existing system boundaries).

## When to Use

- Starting with a rough, unpolished product or feature idea.
- Brainstorming ways to improve an existing product, user experience, or operational flow.
- Exploring whether a technical or business Proof of Concept (PoC) is worth building before investing in full development.
- Feeling stuck or unsure about how to approach a new capability or iteration.

## Workflow

### Step 0: Check Existing Context First (Notion / Local Docs)

Before asking initial questions, check if Notion MCP is connected or local markdown files exist. If the user already documented a partial idea, project hub, or initial notes in Notion, read them first, briefly summarize the baseline understood, and target your 2-3 Socratic questions strictly at gaps, assumptions, or unvalidated risks.

### Step 1: Socratic Exploration (Zero Assumptions)

Ask 2 to 3 focused questions to challenge assumptions and narrow down the problem space. Avoid overwhelming the user with long questionnaires; iterate in short conversational turns until the core concept is clear.

### Step 2: Divergent Options and Trade-Offs

Once the core goal is clear, present **2 to 3 distinct approaches** ranging from simplest to most ambitious:
- **Option A (Lean / Low-Effort):** Fastest way to test value with minimal changes.
- **Option B (Balanced / Recommended):** Best trade-off between user impact and implementation effort.
- **Option C (Ambitious / Differentiator):** High-impact feature or advanced capability for later iterations.

For each option, highlight the **value delivered**, **main risk**, and **what needs to be proven**.

### Step 3: Proof of Concept (PoC) Scoping (When Needed)

If an idea carries high uncertainty (technical feasibility, user adoption, or operational bottleneck), define a time-boxed PoC:
- **Hypothesis:** "We believe that [action] will result in [measurable outcome]."
- **Minimal Experiment:** The smallest throwaway prototype or simulation needed to prove or disprove the hypothesis.
- **Pass/Fail Criteria:** Clear threshold to decide whether to promote the idea into the product backlog.

### Step 4: Hand-Off to Phase 1 and Notion Documentation

Once the user selects an approach or validates the PoC:
1. Generate the **Validated Concept Brief** and write/sync it directly into **Notion (`01. Fase 0: Visión, Ideación y PoCs`)** via Notion MCP if connected, or output it cleanly formatted.
2. Prompt the user to transition into **Phase 1 & 2 (`sdlc-discovery-analysis`)** to formalize user stories, business rules (`BR-XX`), and BPMN flows.

## Gotchas

- Always conduct the conversation, ask questions, and write all generated deliverables in Spanish, unless the user explicitly requests English.
- Do not write production architecture, database schemas, or formal Gherkin acceptance criteria in Phase 0; keep the focus on exploring *what* is worth building and *why*.
- Never assume the user wants the most complex solution; always anchor options with a lean baseline first.
- Keep questioning iterative (2-3 questions per turn) rather than dumping a 15-question form.
