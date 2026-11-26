// Genera, a partir de bpmn/*.bpmn (semántico, con subprocesos anidados), un BPMN con una vista (plano) por
// subproceso colapsado: se puede abrir en Camunda Modeler y navegar con "drill-down".
import fs from 'node:fs';
import path from 'node:path';
import { DOMParser, XMLSerializer } from '@xmldom/xmldom';
import { layoutProcess } from 'bpmn-auto-layout';
import { carriles, leerCarriles, DC, DD, BPMN, DI, kids, local } from './layout.mjs';

const model = process.argv[2];
if (!model) { console.error('uso: node build-models.mjs <modelo>   (desde la carpeta del espacio de trabajo)'); process.exit(1); }
const src = path.resolve('models'), out = path.resolve('build'); fs.mkdirSync(out, { recursive: true });
const ser = new XMLSerializer();

function scopes(proc, acc = []) {            // proceso + subprocesos, en profundidad
  acc.push(proc);
  for (const c of kids(proc)) if (local(c) === 'subProcess') scopes(c, acc);
  return acc;
}

function scopeXml(doc, scope) {
  const defs = doc.documentElement.cloneNode(false);
  const proc = doc.createElementNS(BPMN, 'bpmn:process');
  proc.setAttribute('id', 'Scope_' + scope.getAttribute('id'));
  proc.setAttribute('isExecutable', 'false');
  for (const c of kids(scope)) {
    if (local(c) === 'subProcess') {                       // hijo: solo cascarón (colapsado)
      const shell = c.cloneNode(false);
      for (const k of kids(c)) if (local(k).endsWith('LoopCharacteristics')) shell.appendChild(k.cloneNode(true));
      proc.appendChild(shell);
    } else if (!['laneSet', 'ioSpecification'].includes(local(c))) proc.appendChild(c.cloneNode(true));
  }
  defs.appendChild(proc);
  return ser.serializeToString(defs);
}

const GEO = {};
for (const f of [model + '.bpmn']) {
  const doc = new DOMParser().parseFromString(fs.readFileSync(path.join(src, f), 'utf8'), 'text/xml');
  leerCarriles(doc);
  const process = kids(doc.documentElement).find(n => local(n) === 'process');
  const all = scopes(process);
  const subIds = new Set(all.slice(1).map(s => s.getAttribute('id')));
  for (const old of kids(doc.documentElement, DI)) doc.documentElement.removeChild(old);
  for (const scope of all) {
    const id = scope.getAttribute('id');
    const laid = new DOMParser().parseFromString(await layoutProcess(scopeXml(doc, scope)), 'text/xml');
    const diagram = laid.getElementsByTagNameNS(DI, 'BPMNDiagram')[0];
    const plane = laid.getElementsByTagNameNS(DI, 'BPMNPlane')[0];
    (GEO[f.replace('.bpmn', '')] ||= {})[id] = carriles(laid, diagram, laid.getElementsByTagNameNS(BPMN, 'process')[0]);
    plane.setAttribute('bpmnElement', id);
    diagram.setAttribute('id', 'Diagram_' + id); plane.setAttribute('id', 'Plane_' + id);
    for (const sh of [...diagram.getElementsByTagNameNS(DI, 'BPMNShape')])
      if (subIds.has(sh.getAttribute('bpmnElement'))) sh.setAttribute('isExpanded', 'false');
    doc.documentElement.appendChild(doc.importNode(diagram, true));
  }
  const outFile = path.join(out, f.replace('.bpmn', '_hier.bpmn'));
  fs.writeFileSync(outFile, ser.serializeToString(doc).replace(/ cc:carril="[^"]*"/g, '').replace(/ xmlns:cc="[^"]*"/, ''));
  console.log(f, '->', path.relative('.', outFile), `(${all.length} vistas: ${all.map(s => s.getAttribute('id')).join(', ')})`);
}
fs.writeFileSync(path.join(out, model + '_lanes.json'), JSON.stringify(GEO[model]));
