#!/usr/bin/env bash
# Empaqueta la interfaz web en dist/ (la sirve server/server.py).
set -euo pipefail
cd "$(dirname "$0")"
[ -d node_modules ] || npm install --silent
mkdir -p dist && find dist -mindepth 1 -delete
npx esbuild src/main.js --bundle --format=esm --outfile=dist/app.js --log-level=warning
cp public/index.html public/app.css dist/
mkdir -p dist/assets && cp -r node_modules/bpmn-js/dist/assets/* dist/assets/
echo "OK -> web/dist"
