// Un PNG por subproceso (vista jerárquica con carriles). Uso (desde el espacio de trabajo):
//   node <plantilla>/web/tools/render-planes.mjs build/sorteo_hier.bpmn reports/sorteo/vistas [Scope1 Scope2 ...]
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
const T = path.dirname(new URL(import.meta.url).pathname), file = path.resolve(process.argv[2]), out = path.resolve(process.argv[3]);
const lanes = JSON.parse(fs.readFileSync(file.replace('_hier.bpmn', '_lanes.json'), 'utf8')); const rootId = Object.keys(lanes)[0];
const scopes = process.argv.length > 4 ? process.argv.slice(4) : Object.keys(lanes);
const tmp = path.resolve('render'); fs.rmSync(tmp, { recursive: true, force: true }); fs.mkdirSync(tmp + '/assets', { recursive: true }); fs.mkdirSync(out, { recursive: true });
execFileSync(path.join(T, '..', 'node_modules', '.bin', 'esbuild'), [path.join(T, 'render-planes-entry.js'), '--bundle', `--outfile=${tmp}/app.js`, '--log-level=warning'], { stdio: 'inherit' });
fs.cpSync(path.join(T, '..', 'node_modules/bpmn-js/dist/assets'), tmp + '/assets', { recursive: true });
const css = fs.readFileSync(path.join(T, '..', 'public/app.css'), 'utf8').split('\n').filter((l) => l.startsWith('.lane-')).join('\n');
const xml = fs.readFileSync(file, 'utf8').replace(/<\/script/gi, '<\\/script'); const win = (p) => execFileSync('wslpath', ['-w', p]).toString().trim();
for (const scope of scopes) {
  const g = lanes[scope]; const H = g.lanes.reduce((a, l) => a + l.h, 0); const W = Math.ceil(g.w + 60), HH = Math.ceil(H + 60);
  fs.writeFileSync(tmp + '/index.html', `<!DOCTYPE html><html><head><meta charset="utf-8"><link rel="stylesheet" href="assets/diagram-js.css"><link rel="stylesheet" href="assets/bpmn-js.css"><style>html,body{margin:0;height:100%;background:#fff}#c{width:100%;height:100%}.bjs-powered-by,.bjs-breadcrumbs,.bjs-drilldown{display:none!important}.djs-element.djs-shape:not([data-element-id^="G_"]) .djs-visual>text{transform:translateY(6px)}${css}</style></head><body><div id="c"></div><script id="cfg" type="application/json">${JSON.stringify({ scope, rootId, lanes: g })}</script><script id="xml" type="text/plain">${xml}</script><script src="app.js"></script></body></html>`);
  const png = path.join(out, scope + '.png'), tmpWin = 'C:\\Windows\\Temp\\render-plane.png';
  execFileSync('/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', ['--headless=new', '--disable-gpu', '--no-first-run', `--window-size=${W},${HH}`, '--force-device-scale-factor=1.5', '--virtual-time-budget=6000', '--user-data-dir=C:\\Windows\\Temp\\edge-sim-test', `--screenshot=${tmpWin}`, 'file://wsl.localhost' + win(tmp + '/index.html').replace(/^\\\\wsl\.localhost/, '').replace(/\\/g, '/')], { stdio: 'ignore', timeout: 90000 });
  fs.copyFileSync('/mnt/c/Windows/Temp/render-plane.png', png); console.log('->', path.relative('.', png), `${W}x${HH}`);
}
