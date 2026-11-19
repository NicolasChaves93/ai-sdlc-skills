#!/usr/bin/env python3
"""PreToolUse hook enforcing two SDLC gates from AGENTS.md (Zero-Skip Gates).

1. ADR before code: creating a NEW file in api-*/app-*/infra-* that has no code
   yet, and no ADR in <project>/docs/adr/, asks for confirmation.
2. Pure business before technology: writing frameworks, endpoints or SQL types into
   business artifacts (RF/RNF, BPMN, DMN/BR-XX, use cases, state machines, stories)
   asks for confirmation. Only the text being written is scanned, never the rest of the file.
3. 24h freeze: if <project>/.sdlc-freeze says a live event is within 24h
   (or running), deploy/migration commands and migration files ask for confirmation.

Decision is always "ask" (never silent deny): Notion ADRs can't be checked from
here, and the freeze may be lifted only with explicit user confirmation.
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
        if adr.is_dir() and any(adr.glob("*.md")):
            return
    ask(f"Compuerta 'ADR aprobado antes de código': {code_dir.name} aún no tiene código ni docs/adr/*.md. "
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
            or bool(BUSINESS_NAME_RE.match(path.name)))


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
        root = project_root(path.parent if path.parent.exists() else cwd)
        if not root:
            return
        check_adr(root, path)
        check_business(root, path, written_text(tool, inp))
        fr = freeze_state(root, now)
        if fr and MIGRATION_RE.search(str(path).replace(os.sep, "/")):
            ask(f"Freeze 24h activo (evento {fr[0].isoformat()}): no se permiten migraciones de esquema. "
                "Solo con confirmación explícita del usuario.")
    elif tool == "Bash":
        cmd = inp.get("command", "")
        root = project_root(cwd)
        if not root or not DEPLOY_RE.search(cmd):
            return
        fr = freeze_state(root, now)
        if fr:
            ask(f"Freeze 24h activo (evento {fr[0].isoformat()} a {fr[1].isoformat()}): "
                "este comando despliega o migra. Solo con confirmación explícita del usuario.")


if __name__ == "__main__":
    main()
