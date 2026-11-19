---
name: sdlc-operations-closure
description: Execute Phases 6 and 7 of the Agile SDLC (6 Operación - live operation, deploys, SOP-NN checklists, 24h freeze, incident handling; 7 Cierre - exit criteria, final Notion sync, retrospective, archive) for any active project. Use when preparing a release or live event, running or authoring operational runbooks, deciding whether a deploy is allowed, handling an incident, or closing a module/level/project.
---
# SDLC Phases 6–7 - Operation and Closure (Multi-Project)

Phases 4–5 (build and QA) belong to `sdlc-delivery-operations`. This skill starts when a level or slice is verified (`5 Entrega` done) and covers running it (`6 Operación`) and closing it (`7 Cierre`). Executed directly by Claude Code; no delegation to Gemini.

## Entry Gate (Phase 5 → 6)
Do not move the `Proyecto` to `6 Operación` until all hold; report any that does not, with evidence:
1. Every implemented `BR-XX` has `Casos de prueba` in Notion linked to its `HU-NN`.
2. The automated suites for the current level are green (unit; Postman `collection run` from Level 2; DB integration from Level 3; `k6` thresholds from Level 4). Show the counts, not just "passes".
3. A runbook exists in the repo (`docs/`) for start, stop, rollback, and health check, and a matching `SOP-NN` item exists in `Historias y tareas`.
4. Environment variables, secrets handling, and backup/restore (Level 3+) are documented, without secret values.

## Phase 6 - Operación

### Deploy decision (check in this order)
1. **Freeze:** is a live event scheduled within 24h? The hook `hooks/sdlc_gates.py` enforces it from the file `.sdlc-freeze` at the project root (`event_start: <ISO datetime with offset>`, optional `event_end:`); create it when an event is scheduled and delete it after lifting the freeze. If the freeze is active, **checklist mode only**: no schema migrations, refactors, dependency upgrades, or unverified deploys. Only a pre-approved hotfix with rollback ready, and only with explicit user confirmation.
2. **Gate:** all entry-gate checks still hold on the commit to be deployed.
3. **Rollback:** the previous version and, if data changes, the pre-migration backup are identified before deploying.
4. **Confirm with the user** before any deploy to staging/production; an earlier approval does not cover a new deploy.

### Live event checklist (`SOP-NN`)
- T-72h: scope frozen for features; list the `HU-NN` in play; smoke test in the target environment.
- T-24h: **freeze starts**. Verify health check, data seeded, `postman collection run` against the target (when it is safe to write data there), `k6` baseline if Level 4+.
- T-1h: confirm monitoring/log access, rollback steps at hand, contact path.
- During: no deploys; record anomalies with timestamps.
- After: verify state, export what the event produced, lift the freeze explicitly.

### Incidents
Follow `systematic-debugging` before proposing a fix: reproduce, find root cause, then change. Under freeze, prefer rollback or a config-level mitigation over a code fix. Log each incident as an `SOP-NN` item (what happened, impact, cause, action, follow-up `HU-NN`/`TEC-NN`).

### State sync
On each milestone, update `Proyecto` phase in Notion, keep `Documentos` (Operational Checklist) current, and verify Mermaid syntax before moving a document from `Borrador` to `Aprobado`. Git holds runbooks and `CHANGELOG.md`; Notion holds status and traceability (see `NOTION_SCHEMA.md`).

## Phase 7 - Cierre

Close a level/module/project only when:
1. **Scope:** every `HU-NN`/`TEC-NN`/`SOP-NN` of the `Iteración` is `Hecho` or explicitly moved to a named next `Iteración`, with the user's agreement.
2. **Traceability:** the chain `RF → HU → BR → Caso de prueba` has no gaps for implemented rules; no `Caso de prueba` linked directly to a `Requisito`.
3. **Evidence:** final test/Postman/k6 results recorded in `Documentos` (Sprint Review), and `CHANGELOG.md` updated in the repo.
4. **Docs:** README, runbooks, ADR statuses and diagrams are current; Mermaid diagrams validated.
5. **Retrospective:** write Lessons Learned in `Documentos` (what worked, what failed, what changes in the process), and turn each action into a backlog item.
6. **Next loop:** pick the next slice and route it to Phase 1–2 (new business need) or Phase 3 (new technical decision) before any new code. The next Evolutionary Level starts only after this closure.
7. **Final sync:** set `Proyecto` phase to `7 Cierre` (or the next phase for a continuing project) in Notion.

## Gotchas
- Conversation and Notion records in Spanish; code, branches and commits in English.
- Deploys, data deletion, publishing documents, and anything visible to other people are outward-facing: confirm first.
- Never print or commit secrets or tokens (Notion, Postman, DB credentials).
- Never lift or bypass the 24h freeze without explicit user confirmation.
- Report failures as failures: a closure with a failing check stays open and lists what is missing.
