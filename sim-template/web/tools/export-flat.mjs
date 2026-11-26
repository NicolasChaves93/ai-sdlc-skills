// Exporta un BPMN "plano" (sin subprocesos) con piscina y carriles reales, listo para Camunda Modeler y para
// el documento de Notion. Parte del mismo modelo que usa el simulador (bpmn/<modelo>.bpmn).
// Uso (desde la carpeta del espacio de trabajo): node <plantilla>/web/tools/export-flat.mjs sorteo "Título del proceso" v3
import fs from 'node:fs';
import path from 'node:path';
import { DOMParser, XMLSerializer } from '@xmldom/xmldom';
import { layoutProcess } from 'bpmn-auto-layout';
import { carriles, leerCarriles, DC, DD, BPMN, DI, kids, local } from './layout.mjs';

const [modelo = 'sorteo', titulo = 'Proceso', ver = 'v3'] = process.argv.slice(2);
const CC = 'http://colombiancode.co/bpmn';
const doc = new DOMParser().parseFromString(fs.readFileSync(`models/${modelo}.bpmn`, 'utf8'), 'text/xml');
leerCarriles(doc);
const proc = kids(doc.documentElement).find(n => local(n) === 'process');

// ---- 1. leer todo el árbol en estructuras simples
const nodes = {}, flows = {}, subs = {};
(function walk(scope, depth, parent) {
  for (const c of kids(scope)) {
    const t = local(c), id = c.getAttribute('id');
    if (/^(laneSet|textAnnotation|association|documentation|extensionElements|ioSpecification|dataObject|dataObjectReference|dataStoreReference|property)$/.test(t)) continue;
    if (t === 'sequenceFlow') flows[id] = { id, name: c.getAttribute('name') || '', s: c.getAttribute('sourceRef'), t: c.getAttribute('targetRef') };
    else { nodes[id] = { id, tag: t, name: c.getAttribute('name') || '', carril: c.getAttributeNS(CC, 'carril') || '', scope: parent, el: c };
      if (t === 'subProcess') { subs[id] = { id, depth, parent }; walk(c, depth + 1, id); } }
  }
})(proc, 0, null);

// ---- 2. aplanar: del subproceso más interno al más externo
for (const sp of Object.values(subs).sort((a, b) => b.depth - a.depth)) {
  const inner = Object.values(nodes).filter(n => n.scope === sp.id);
  const start = inner.find(n => n.tag === 'startEvent'), end = inner.find(n => n.tag === 'endEvent');
  if (!start || !end) throw new Error('subproceso sin inicio o fin: ' + sp.id);
  const entradas = Object.values(flows).filter(f => f.s === start.id).map(f => f.t);
  for (const f of Object.values(flows)) if (f.s === start.id) delete flows[f.id];
  const entrantes = Object.values(flows).filter(f => f.t === sp.id), salientes = Object.values(flows).filter(f => f.s === sp.id);
  if (entradas.length !== 1 || salientes.length !== 1) throw new Error('caso no soportado en ' + sp.id);
  for (const f of entrantes) f.t = entradas[0];
  const sal = salientes[0]; delete flows[sal.id];
  for (const f of Object.values(flows)) if (f.t === end.id) { f.t = sal.t; if (!f.name) f.name = sal.name; }
  for (const n of inner) if (n.scope === sp.id) n.scope = sp.parent;
  delete nodes[start.id]; delete nodes[end.id]; delete nodes[sp.id];
}

// ---- 3. semántica plana (sin carriles aún) con el atributo cc:carril para trazar
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
const orden = Object.values(nodes);
const procId = `Process_ToBe_${modelo[0].toUpperCase() + modelo.slice(1)}_${ver}`;
const cuerpo = orden.map(n => `    <bpmn:${n.tag} id="${n.id}"${n.name ? ` name="${esc(n.name)}"` : ''}${n.carril ? ` cc:carril="${esc(n.carril)}"` : ''}/>`).join('\n')
  + '\n' + Object.values(flows).map(f => `    <bpmn:sequenceFlow id="${f.id}"${f.name ? ` name="${esc(f.name)}"` : ''} sourceRef="${f.s}" targetRef="${f.t}"/>`).join('\n');
const sem = `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" xmlns:cc="${CC}" id="Definitions_Flat" targetNamespace="http://colombiancode.co/plataforma-v2/${modelo}">
  <bpmn:process id="${procId}" name="${esc(titulo)}" isExecutable="false">
${cuerpo}
  </bpmn:process>
</bpmn:definitions>`;

// ---- 4. trazado por carriles y armado de piscina + carriles
const laid = new DOMParser().parseFromString(await layoutProcess(sem), 'text/xml');
const diagram = laid.getElementsByTagNameNS(DI, 'BPMNDiagram')[0], plane = laid.getElementsByTagNameNS(DI, 'BPMNPlane')[0];
const process_ = laid.getElementsByTagNameNS(BPMN, 'process')[0];
const geo = carriles(laid, diagram, process_);
const DX = 70, POOL_X = 0;                                  // 30 de la piscina + 30 del carril + margen
for (const b of diagram.getElementsByTagNameNS(DC, 'Bounds')) b.setAttribute('x', +b.getAttribute('x') + DX);
for (const w of diagram.getElementsByTagNameNS(DD, 'waypoint')) w.setAttribute('x', +w.getAttribute('x') + DX);
const H = geo.lanes.reduce((a, l) => a + l.h, 0), W = geo.w + DX;

const dEl = (tag, attrs, ns = BPMN, pre = 'bpmn') => { const e = laid.createElementNS(ns, `${pre}:${tag}`); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v); return e; };
const defs = laid.documentElement;
const collab = dEl('collaboration', { id: 'Collaboration_' + procId });
const pid = 'Participant_' + procId; collab.appendChild(dEl('participant', { id: pid, name: titulo, processRef: procId }));
defs.insertBefore(collab, process_);
const laneSet = dEl('laneSet', { id: 'LaneSet_' + procId });
geo.lanes.forEach((l, i) => { const lane = dEl('lane', { id: 'Lane_' + i, name: l.n }); for (const [id, ln] of Object.entries(geo.of)) if (ln === l.n) lane.appendChild(dEl('flowNodeRef', {})).textContent = id; laneSet.appendChild(lane); });
process_.insertBefore(laneSet, process_.firstChild);
plane.setAttribute('bpmnElement', collab.getAttribute('id'));
const shape = (id, x, y, w, h) => { const s = dEl('BPMNShape', { id: id + '_di', bpmnElement: id, isHorizontal: 'true' }, DI, 'bpmndi'); const b = dEl('Bounds', { x, y, width: w, height: h }, DC, 'dc'); s.appendChild(b); return s; };
const first = plane.firstChild; const ins = n => plane.insertBefore(n, first);
ins(shape(pid, POOL_X, 0, W, H)); let y = 0; for (const [i, l] of geo.lanes.entries()) { ins(shape('Lane_' + i, POOL_X + 30, y, W - 30, l.h)); y += l.h; }
// limpiar atributos auxiliares
defs.removeAttribute('xmlns:cc'); defs.setAttribute('id', `Definitions_ToBe_${modelo}_${ver}`);
for (const e of laid.getElementsByTagName('*')) for (const a of [...e.attributes]) if (a.name === 'cc:carril') e.removeAttribute(a.name);
const out = path.resolve('build'); fs.mkdirSync(out, { recursive: true });
const file = path.join(out, `${modelo}_flat.bpmn`);
fs.writeFileSync(file, new XMLSerializer().serializeToString(laid));
fs.writeFileSync(path.join(out, `${modelo}_size.json`), JSON.stringify({ w: W, h: H }));
console.log('->', path.relative('.', file), `(${orden.length} elementos, ${Object.keys(flows).length} flujos, ${geo.lanes.length} carriles, ${W}x${H})`);
