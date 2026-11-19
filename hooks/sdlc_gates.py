#!/usr/bin/env python3
"""PreToolUse hook enforcing two SDLC gates from AGENTS.md (Zero-Skip Gates).

1. ADR before code: creating a NEW file in api-*/app-*/infra-* that has no code
   yet, and no ADR in <project>/docs/adr/, asks for confirmation.
2. 24h freeze: if <project>/.sdlc-freeze says a live event is within 24h
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
DEPLOY_RE = re.compile(
    r"\b(git\s+push|docker\s+(compose\s+)?(up|push|stack\s+deploy)|docker-compose\s+up|"
    r"alembic\s+upgrade|flyway\s+migrate|prisma\s+migrate|(fly|flyctl)\s+deploy|"
    r"render\s+deploy|kubectl\s+(apply|rollout)|terraform\s+apply|helm\s+(upgrade|install)|"
    r"supabase\s+(db\s+push|migration)|postman\s+workspace\s+push)\b")
MIGRATION_RE = re.compile(r"(^|/)(migrations?|alembic/versions)/")


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
