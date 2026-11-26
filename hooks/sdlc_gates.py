#!/usr/bin/env python3
"""PreToolUse hook enforcing two SDLC gates from AGENTS.md (Zero-Skip Gates).

1. ADR before code: creating a NEW file in api-*/app-*/infra-* that has no code
   yet, and no accepted ADR in <project>/docs/adr/, asks for confirmation.
2. Pure business before technology: writing frameworks, endpoints or SQL types into
   business artifacts (RF/RNF, BPMN, DMN/BR-XX, use cases, state machines, stories)
   asks for confirmation. Only the text being written is scanned, never the rest of the file.
3. 24h freeze: if <project>/.sdlc-freeze says a live event is within 24h
   (or running), deploy/migration commands and migration files ask for confirmation.

4. Levels in order: <project>/.sdlc-state.json ({"level": 2}) says the current level;
   writing code that belongs to a later level asks for confirmation. No file, no check.

5. Increment state, only when <project>/.sdlc/state.json exists (these BLOCK):
   client proposal not approved; src/ or tests/ without closed stories (and, from
   level 2, an approved and accepted ADR); git commit/push with pending doc sync or
   untested increment; deploy before "freeze_until". Editing state.json asks, so
   approvals stay with the user. Bash redirections are not inspected.

Gates 1-4 only "ask" (never silent deny): Notion ADRs can't be checked from here,
and the 24h freeze may be lifted only with explicit user confirmation.
No-op outside a project whose AGENTS.md contains "Zero-Skip Gates".

.sdlc-freeze format (at the project root, next to AGENTS.md):
    event_start: 2026-12-05T18:00:00-05:00
    event_end:   2026-12-05T23:00:00-05:00   # optional, default start + 12h
"""
import json, os, re, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

CODE_EXT = {".tf", ".py", ".go", ".java", ".kt", ".cs", ".js", ".jsx", ".ts", ".tsx", ".sql",
            ".rs", ".rb", ".php", ".vue", ".svelte", ".html", ".css", ".toml", ".gradle"}
CODE_DIR_RE = re.compile(r"^(api|app|infra)-[^/]+$")
# Global options may sit between the tool and its subcommand (git -C . push,
# docker compose -f x.yml up). Each option may take one value argument.
OPTS = r"(?:\s+-\S+(?:\s+[^\s-]\S*)?)*"
DEPLOY_RE = re.compile(
    r"\b(git" + OPTS + r"\s+push|docker(?:\s+compose)?" + OPTS + r"\s+(?:up|push|stack\s+deploy)|"
    r"docker-compose" + OPTS + r"\s+up|"
    r"alembic\s+upgrade|flyway\s+migrate|prisma\s+migrate|(fly|flyctl)\s+deploy|"
    r"render\s+deploy|kubectl\s+(apply|rollout)|terraform\s+apply|helm\s+(upgrade|install)|"
    r"supabase\s+(db\s+push|migration)|postman\s+workspace\s+push)\b")
GIT_WRITE_RE = re.compile(r"\bgit" + OPTS + r"\s+(commit|push)\b")
MIGRATION_RE = re.compile(r"(^|/)(migrations?|alembic/versions)/")


# Business-pure artifacts: *.bpmn / *.dmn anywhere, docs/<business dir>/**, or RF-/RNF-/BR-/UC-/... files.
BUSINESS_EXT = {".bpmn", ".dmn"}
BUSINESS_DIRS = {"negocio", "requisitos", "requerimientos", "bpmn", "dmn", "casos-de-uso", "casos_de_uso",
                 "historias", "user-stories", "maquinas-de-estado", "estados", "business"}
BUSINESS_NAME_RE = re.compile(r"^(RF|RNF|BR|UC|HU|DMN|BPMN)[-_]", re.I)
BUSINESS_TEXT_EXT = {".md", ".mmd", ".mermaid", ".txt", ".feature", ".yaml", ".yml", ".json", ".bpmn", ".dmn", ""}
# Case-sensitive on purpose: avoids "react", "express", "text", "date" as plain words.
TECH_RE = re.compile(
    r"\b(FastAPI|Django|Flask|Spring(?:\s+Boot)?|Express\.js|NestJS|Laravel|Rails|React|Angular|Vue(?:\.js)?|"
    r"Next\.js|Svelte|Hibernate|SQLAlchemy|Prisma|PostgreSQL|Postgres|MySQL|MongoDB|SQLite|Redis|Kafka|"
    r"RabbitMQ|Docker|Kubernetes|GraphQL|JWT|ORM|VARCHAR|NVARCHAR|BIGINT|SMALLINT|TIMESTAMPTZ|JSONB|BYTEA|SERIAL)\b"
    r"|\b(?:GET|POST|PUT|PATCH|DELETE)\s+/\S*|(?<![\w.])/api/\S*|\bINT\(\d+\)")

# Accepted ADR: a line such as "- **Estado:** Aceptada".
ADR_OK_RE = re.compile(r"^[\s>*-]*(Estado|Status)\**\s*:\**\s*(Aceptad[oa]|Aprobad[oa]|Accepted|Approved)\b",
                       re.I | re.M)
# (minimum level, path inside the project) as defined by ADR-03 / AGENTS.md levels.
LEVEL_PATHS = [
    (2, re.compile(r"(^|/)api-[^/]+/(.*/)?adapters/inbound/(http|websocket)/")),
    (3, re.compile(r"(^|/)api-[^/]+/(.*/)?adapters/outbound/sqlite/")),
    (4, re.compile(r"(^|/)api-[^/]+/(.*/)?adapters/outbound/(postgres|redis)/")),
    (5, re.compile(r"(^|/)app-[^/]+/")),
]


def ask(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": reason}}))
    sys.exit(0)


def project_root(start):
    # Outermost ancestor wins: sub-projects (api-x/) carry symlinked AGENTS.md copies.
    p = Path(start).resolve()
    found = None
    for d in [p, *p.parents]:
        f = d / "AGENTS.md"
        if f.is_file():
            try:
                if "Zero-Skip Gates" in f.read_text(errors="ignore"):
                    found = d
            except OSError:
                pass
    return found


def freeze_state(root, now):
    f = root / ".sdlc-freeze"
    if not f.is_file():
        return None
    vals = {}
    for line in f.read_text(errors="ignore").splitlines():
        m = re.match(r"\s*(event_start|event_end)\s*:\s*([^#\s]+)", line)
        if m:
            vals[m.group(1)] = m.group(2)
    try:
        start = datetime.fromisoformat(vals["event_start"])
        end = datetime.fromisoformat(vals["event_end"]) if "event_end" in vals else start + timedelta(hours=12)
    except (KeyError, ValueError):
        return None
    if start.tzinfo is None:
        start = start.astimezone()
    if end.tzinfo is None:
        end = end.astimezone()
    if start - timedelta(hours=24) <= now <= end:
        return start, end
    return None


def has_code(d):
    for dirpath, dirnames, files in os.walk(d):
        dirnames[:] = [x for x in dirnames if x not in {".git", ".venv", "node_modules", "__pycache__", "postman"}]
        if any(Path(f).suffix in CODE_EXT for f in files):
            return True
    return False


def block(reason):
    print(f"[SDLC GATE BLOCKED] {reason}", file=sys.stderr)
    sys.exit(2)


def load_state(root):
    """Increment state, or None when the project has not opted in."""
    f = root / ".sdlc" / "state.json"
    if not f.is_file():
        return None
    try:
        state = json.loads(f.read_text(encoding="utf-8"))
        assert isinstance(state, dict) and isinstance(state.get("gates", {}), dict)
        int(state.get("level", 2))
    except (OSError, ValueError, TypeError, AssertionError):
        return "invalid"
    return state


def has_accepted_adr(root, parts):
    dirs = [root.joinpath(*parts[:i], "docs", "adr") for i in range(len(parts))]
    return any(ADR_OK_RE.search(f.read_text(errors="ignore")) for d in dirs if d.is_dir() for f in d.glob("*.md"))


def check_increment_write(root, path, state):
    try:
        rel = path.resolve().relative_to(root).as_posix()
    except ValueError:
        return
    if rel == ".sdlc/state.json":
        ask("Cambio en .sdlc/state.json: las aprobaciones de compuerta las confirma el usuario.")
    if state == "invalid":
        if not rel.startswith(".sdlc/"):
            ask(".sdlc/state.json no es un JSON válido: las compuertas del incremento no se pueden comprobar.")
        return
    gates = state.get("gates", {})
    if state.get("project_type") == "client" and not gates.get("proposal_approved"):
        if not (rel == ".sdlc/00-idea-brief.md" or rel.startswith(".sdlc/proposal-")):
            block("Proyecto de cliente sin propuesta aprobada ('proposal_approved': false). Cierra la pre-venta primero.")
    parts = rel.split("/")
    if not {"src", "tests"} & set(parts[:-1]):
        return
    if not gates.get("phase_1_2_stories") or not (root / ".sdlc/active/01-stories.md").is_file():
        block("Fase 1-2 incompleta: faltan historias, reglas y Gherkin cerrados en .sdlc/active/01-stories.md.")
    level = int(state.get("level", 2))
    if level >= 2 and not (gates.get("phase_3_adr_approved") and has_accepted_adr(root, parts[:-1])):
        block(f"Nivel {level}: se necesita 'phase_3_adr_approved' y un ADR aceptado en docs/adr/ antes de tocar código.")


def check_increment_bash(state, cmd, now):
    if not isinstance(state, dict):
        return
    if GIT_WRITE_RE.search(cmd):
        if state.get("pending_doc_sync"):
            block("Zero-Drift: registra el [AMENDMENT] en .sdlc/active/01-stories.md y pon 'pending_doc_sync': false.")
        if not state.get("gates", {}).get("phase_4_5_tests_passed"):
            block("Fase 5 incompleta: ejecuta las pruebas (test-runner) antes de hacer commit o push.")
    until = state.get("freeze_until")
    if until and DEPLOY_RE.search(cmd):
        try:
            end = datetime.fromisoformat(until)
        except (ValueError, TypeError):
            ask("'freeze_until' en .sdlc/state.json no es una fecha ISO válida.")
        if now < (end if end.tzinfo else end.astimezone()):
            block(f"Freeze activo hasta {until}: despliegue bloqueado.")


def check_adr(root, path):
    try:
        rel = path.resolve().relative_to(root)
    except ValueError:
        return
    parts = rel.parts
    # project folders may sit at the root (api-x/...) or one level down
    for i, part in enumerate(parts[:-1]):
        if CODE_DIR_RE.match(part):
            code_dir = root.joinpath(*parts[: i + 1])
            break
    else:
        return
    if path.exists() or path.suffix not in CODE_EXT:
        return
    if has_code(code_dir):
        return  # already scaffolded: gate was passed earlier
    for adr in (root / "docs" / "adr", code_dir / "docs" / "adr"):
        if adr.is_dir() and any(ADR_OK_RE.search(f.read_text(errors="ignore")) for f in adr.glob("*.md")):
            return
    ask(f"Compuerta 'ADR aprobado antes de código': {code_dir.name} aún no tiene código ni un ADR aceptado en docs/adr/. "
        "Confirma que el ADR de stack está aprobado en Notion (PoCs y decisiones) antes de crear código.")


def is_business_artifact(root, path):
    try:
        parts = path.resolve().relative_to(root).parts
    except ValueError:
        return False
    if any(CODE_DIR_RE.match(x) or x in {"node_modules", ".git", "adr", "postman"} for x in parts[:-1]):
        return False
    if path.suffix.lower() not in BUSINESS_TEXT_EXT:
        return False
    return (path.suffix.lower() in BUSINESS_EXT
            or any(x.lower() in BUSINESS_DIRS for x in parts[:-1])
            or bool(BUSINESS_NAME_RE.match(path.name))
            or parts[-3:] == (".sdlc", "active", "01-stories.md"))


def check_level(root, path):
    state_file = root / ".sdlc" / "state.json"
    if not state_file.is_file():
        state_file = root / ".sdlc-state.json"      # formato anterior
    try:
        rel = path.resolve().relative_to(root).as_posix()
        level = int(json.loads(state_file.read_text())["level"])
    except (ValueError, KeyError, TypeError, OSError):
        return
    if path.suffix not in CODE_EXT:
        return
    for needed, pattern in LEVEL_PATHS:
        if level < needed and pattern.search(rel):
            ask(f"Compuerta 'Niveles evolutivos': {rel} es de Nivel {needed} y el proyecto está en Nivel {level} "
                "({state_file.name}). Cierra el nivel actual antes de avanzar.")


def written_text(tool, inp):
    if tool == "Write":
        return inp.get("content") or ""
    if tool == "Edit":
        return inp.get("new_string") or ""
    return "\n".join(e.get("new_string") or "" for e in inp.get("edits") or [])


def check_business(root, path, text):
    if not is_business_artifact(root, path):
        return
    hits = sorted({m.group(0).strip() for m in TECH_RE.finditer(text)})
    if hits:
        ask("Compuerta 'Negocio Puro antes de Tecnología': " + path.name + " es un artefacto de negocio "
            "y el texto menciona tecnología (" + ", ".join(hits[:6]) + "). "
            "Los RF/RNF, BPMN, DMN, casos de uso y máquinas de estado no deben nombrar frameworks, "
            "endpoints ni tipos SQL; eso va en arquitectura (Fase 3).")


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return
    tool = data.get("tool_name", "")
    inp = data.get("tool_input", {}) or {}
    cwd = data.get("cwd") or os.getcwd()
    now = datetime.now(timezone.utc)

    if tool in {"Write", "Edit", "MultiEdit"}:
        fp = inp.get("file_path")
        if not fp:
            return
        path = Path(fp)
        if not path.is_absolute():
            path = Path(cwd) / path
        root = project_root(next(d for d in path.parents if d.exists()))
        if not root:
            return
        state = load_state(root)
        if state is not None:
            check_increment_write(root, path, state)
        check_adr(root, path)
        check_level(root, path)
        check_business(root, path, written_text(tool, inp))
        fr = freeze_state(root, now)
        if fr and MIGRATION_RE.search(str(path).replace(os.sep, "/")):
            ask(f"Freeze 24h activo (evento {fr[0].isoformat()}): no se permiten migraciones de esquema. "
                "Solo con confirmación explícita del usuario.")
    elif tool == "Bash":
        cmd = inp.get("command", "")
        root = project_root(cwd)
        if not root:
            return
        check_increment_bash(load_state(root), cmd, now)
        if not DEPLOY_RE.search(cmd):
            return
        fr = freeze_state(root, now)
        if fr:
            ask(f"Freeze 24h activo (evento {fr[0].isoformat()} a {fr[1].isoformat()}): "
                "este comando despliega o migra. Solo con confirmación explícita del usuario.")


if __name__ == "__main__":
    main()
