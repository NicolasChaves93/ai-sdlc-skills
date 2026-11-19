---
name: postman-cli
description: Use when creating, editing, linting or running Postman collections with the Postman CLI (local v3 / Native Git YAML in postman/), for API functional tests (pm.test), regression runs of Nivel 2+ endpoints, or syncing with a Postman workspace. Covers the binary location, the collection layout, safe run commands, and the rules for writing request files.
---
# Postman CLI (API functional tests, Phase 5)

## Binary
Not on PATH. Always call `/home/nicolas/.local/bin/postman` (alias `P` below). Verify with `P --version` and `P status`.

## Project layout (Native Git, local-first)
```
postman/
  collections/<name>/<Folder>/<Request>.request.yaml   # one file per request
  environments/local.environment.yaml                  # baseUrl + chained ids
  globals/  specs/  mocks/  flows/
.postman/                                              # manifest, git-ignored
```
Convention in `api-juegos`: `Endpoints base/` (one request per endpoint, happy path) and `Casos de uso/HU-XX .../{1 Preparación, 2 Sorteo, 3 Errores}` (flows per user story, tied to BR-XX rules).

## Run (needs the API running first)
```bash
P collection run "postman/collections/<name>" -e postman/environments/local.environment.yaml
```
Useful flags: `-i "Folder/Request"` (run a subset; path disambiguates), `--bail` (stop on first failure), `--output <dir>` (YAML report; use the scratchpad, not the repo), `-n`/`-d` (iterations / data file), `--env-var k=v`, `--timeout-request <ms>`, `-x` (do not fail the exit code; only for exploration, never in CI).
Run order matters: `Preparación` requests store ids with `pm.environment.set(...)` that later folders read. Running a single request out of order fails for lack of that state — run its whole folder.

## Before running: lint
```bash
P collection lint "postman/collections/<name>"
P workspace lint            # config + all entities
```
Fix lint errors before running; do not silence them.

## Writing a request file
- `url: "{{baseUrl}}/v1/..."` — never hardcode host or ports.
- `description:` in Spanish (project language), with fields table, response, and "Todavía no implementado" notes; it is the API documentation.
- Assertions go in an `afterResponse` script with `pm.test("...")`: status code, `Content-Type`, response shape (`to.have.all.keys`), and the business rule being verified (cite the BR-XX / HU-XX in the test name when one applies).
- Chain state through the environment (`pm.environment.set`) and declare every variable in `local.environment.yaml` with an empty value, so a fresh clone runs.
- Every happy path gets error siblings (422 invalid input, 404 missing resource, rule violations) in `3 Errores`. Negative tests must also assert nothing was persisted when atomicity is a rule.
- Keep `order:` values unique within a folder; `examples:` point to `.resources/`.
- Use the CLI to scaffold instead of hand-writing structure when possible: `P collection request --help`, `P collection folder --help`, `P collection example --help`, `P collection import <curl|har>`.

## Cloud sync (only on explicit request)
`P workspace diff` (read-only preview) → `P workspace prepare` → `P workspace push`. `P workspace pull` overwrites local files. `delete`/`share`/`publish` are outward-facing: confirm with the user first. Authentication is `P login`; never print or commit API keys.

## Gates
- Postman collections belong to Nivel 2+ (API exists, ADR approved). Do not create them before the ADR gate in `sdlc-delivery-operations`.
- A change to an endpoint or business rule is not done until its request file, its error cases, and a green `collection run` reflect it. Report the run's pass/fail counts as evidence; if anything fails, say so with the failing test names.
- Load/performance testing is `k6-load-testing`, not Postman.

## Note on `P skills` / `P init`
The CLI can generate its own agent skills into `postman/skills/` (`P skills status`, `P skills update`, `P init`). They write into the repo and get committed; run them only when the user asks.
