// Dibuja un .bpmn como imagen PNG con el visor estándar de bpmn.io (Edge sin ventana).
// Uso (desde el espacio de trabajo): node <plantilla>/web/tools/render-png.mjs build/sorteo_flat.bpmn reports/sorteo/diagrama.png
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
const file = path.resolve(process.argv[2]); const dir = path.dirname(file);
const { w, h } = JSON.parse(fs.readFileSync(file.replace('_flat.bpmn', '_size.json'), 'utf8'));
const tmp = path.resolve('render'); fs.rmSync(tmp, { recursive: true, force: true }); fs.mkdirSync(tmp + '/assets', { recursive: true });
execFileSync(path.join(path.dirname(new URL(import.meta.url).pathname), '..', 'node_modules', '.bin', 'esbuild'), [path.join(path.dirname(new URL(import.meta.url).pathname), 'render-entry.js'), '--bundle', `--outfile=${tmp}/app.js`, '--log-level=warning'], { stdio: 'inherit' });
fs.cpSync(path.join(path.dirname(new URL(import.meta.url).pathname), '..', 'node_modules/bpmn-js/dist/assets'), tmp + '/assets', { recursive: true });
const xml = fs.readFileSync(file, 'utf8').replace(/<\/script/gi, '<\\/script');
fs.writeFileSync(tmp + '/index.html', `<!DOCTYPE html><html><head><meta charset="utf-8"><link rel="stylesheet" href="assets/diagram-js.css"><link rel="stylesheet" href="assets/bpmn-js.css">
<style>html,body{margin:0;height:100%;background:#fff}#c{width:100%;height:100%}.bjs-powered-by{display:none!important}</style></head><body><div id="c"></div><script id="xml" type="text/plain">${xml}</script><script src="app.js"></script></body></html>`);
const win = (p) => execFileSync('wslpath', ['-w', p]).toString().trim();
const png = path.resolve(process.argv[3] || file.replace('.bpmn', '.png')); fs.mkdirSync(path.dirname(png), { recursive: true }); const tmpWin = 'C:\\Windows\\Temp\\render-sorteo.png';
const W = Math.ceil(w + 60), H = Math.ceil(h + 60);
execFileSync('/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', ['--headless=new', '--disable-gpu', '--no-first-run', `--window-size=${W},${H}`, '--force-device-scale-factor=1.5', '--virtual-time-budget=6000', '--user-data-dir=C:\\Windows\\Temp\\edge-sim-test', `--screenshot=${tmpWin}`, 'file://wsl.localhost' + win(tmp + '/index.html').replace(/^\\\\wsl\.localhost/, '').replace(/\\/g, '/')], { stdio: 'ignore', timeout: 90000 });
fs.copyFileSync('/mnt/c/Windows/Temp/render-sorteo.png', png);
console.log('->', path.relative('.', png), `(${W}x${H} @1.5)`);
