#!/usr/bin/env bash
# Uso:
#   ./setup.sh                      enlaza skills, agentes y NOTION_SCHEMA.md en ~/.claude y ~/.gemini
#   ./setup.sh <proyecto> [sub...]  además copia AGENTS.template.md en cada carpeta indicada
# Nada se borra: lo que se reemplaza se mueve a ~/.sdlc-backup/<fecha>/.
set -euo pipefail

REPO="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
BACKUP="$HOME/.sdlc-backup/$(date +%Y%m%d-%H%M%S)"
CLAUDE_ONLY="propuesta-comercial"

keep() { # mueve $1 al respaldo conservando su ruta relativa a $HOME
  local dest="$BACKUP/${1#"$HOME"/}"
  mkdir -p "$(dirname "$dest")"
  mv "$1" "$dest"
  echo "respaldo: $1 -> $dest"
}

link() { # link <origen> <destino>
  if [ -L "$2" ]; then
    [ "$(readlink "$2")" = "$1" ] && return 0
    rm "$2"
  elif [ -e "$2" ]; then
    keep "$2"
  fi
  ln -s "$1" "$2"
  echo "enlace: $2 -> $1"
}

mkdir -p "$HOME/.claude/skills" "$HOME/.claude/agents" "$HOME/.gemini/skills"
for dir in "$REPO"/skills/*/; do
  dir="${dir%/}"; name="$(basename "$dir")"
  link "$dir" "$HOME/.claude/skills/$name"
  case " $CLAUDE_ONLY " in *" $name "*) continue ;; esac
  link "$dir" "$HOME/.gemini/skills/$name"
done
for f in "$REPO"/agents/*.md; do link "$f" "$HOME/.claude/agents/$(basename "$f")"; done
link "$REPO/NOTION_SCHEMA.md" "$HOME/.claude/skills/NOTION_SCHEMA.md"
link "$REPO/NOTION_SCHEMA.md" "$HOME/.gemini/skills/NOTION_SCHEMA.md"

for target in "$@"; do
  [ -d "$target" ] || { echo "no existe: $target" >&2; exit 1; }
  f="$target/AGENTS.md"
  if [ -L "$f" ]; then
    rm "$f"
  elif [ -f "$f" ] && ! cmp -s "$REPO/AGENTS.template.md" "$f"; then
    keep "$(readlink -f "$f")"
  fi
  cp "$REPO/AGENTS.template.md" "$f"
  [ -e "$target/CLAUDE.md" ] || [ -L "$target/CLAUDE.md" ] || ln -s AGENTS.md "$target/CLAUDE.md"
  echo "reglas: $f"
done
