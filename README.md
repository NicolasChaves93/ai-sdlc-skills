# ai-sdlc-skills

Skills, reglas, subagentes y compuertas de una fábrica de software en 7 fases, compartidas entre Claude Code y Gemini CLI.

## Estructura

| Ruta | Contenido |
|---|---|
| `skills/` | Todas las skills propias. |
| `agents/` | Subagentes de Claude Code (`code-reviewer`, `test-runner`). |
| `hooks/` | `sdlc_gates.py` y sus pruebas. |
| `AGENTS.template.md` | Reglas base de cada proyecto. |
| `agents-registry.yaml` | Qué agente ejecuta cada fase. |
| `NOTION_SCHEMA.md` | IDs, propiedades y valores de las bases de Notion. |
| `setup.sh` | Instala enlaces y copia las reglas. |

## Flujo

Gemini hace las fases 0–3 y deja la salida en `docs/specs/` y `docs/adr/` del proyecto; Claude hace las fases 4–7.

## Instalación

```bash
git clone <url-del-repo> ~/proyectos/ai-sdlc-skills
cd ~/proyectos/ai-sdlc-skills
./setup.sh                                   # enlaces en ~/.claude y ~/.gemini
./setup.sh ../mi-proyecto ../mi-proyecto/api-x   # además copia AGENTS.md
```

La ruta `~/proyectos/ai-sdlc-skills` es fija: las reglas la referencian. `propuesta-comercial` solo se enlaza en Claude.

El hook se activa a mano en `~/.claude/settings.json`:

```json
{"hooks": {"PreToolUse": [{"matcher": "Write|Edit|MultiEdit|Bash",
  "hooks": [{"type": "command", "command": "python3 -I $HOME/proyectos/ai-sdlc-skills/hooks/sdlc_gates.py"}]}]}}
```

## Incremento por proyecto
`./setup.sh --init internal|client <proyecto>` crea `.sdlc/` y activa las compuertas del incremento (estas bloquean). Sin `.sdlc/state.json` no se aplican. Son de Claude Code: Gemini no ejecuta el hook.

## Compuertas del hook

Estas cuatro piden confirmación.

- Negocio antes que tecnología.
- ADR aceptado en `docs/adr/` antes del primer código.
- Niveles en orden, según `.sdlc/state.json` (o `.sdlc-state.json`).
- Freeze de 24 h, según `.sdlc-freeze`.

Pruebas: `python3 -m unittest hooks/test_sdlc_gates.py`

## Cambiar las reglas

Edita `AGENTS.template.md` y ejecuta `./setup.sh <proyecto> <subcarpetas>`. No edites las copias: se reemplazan (queda respaldo en `~/.sdlc-backup/`).
