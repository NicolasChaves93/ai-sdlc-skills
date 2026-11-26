// Valida un .bpmn: lectura sin advertencias, cada flujo con su dibujo, cada nodo en un carril y dentro de la piscina.
import fs from 'node:fs';
import { BpmnModdle } from 'bpmn-moddle';
const file = process.argv[2]; const { rootElement, warnings } = await new BpmnModdle().fromXML(fs.readFileSync(file, 'utf8'));
const errs = [...warnings.map(w => 'advertencia: ' + w.message)];
const proc = rootElement.rootElements.find(r => r.$type === 'bpmn:Process');
const nodos = proc.flowElements.filter(f => f.$type !== 'bpmn:SequenceFlow'), flujos = proc.flowElements.filter(f => f.$type === 'bpmn:SequenceFlow');
const di = rootElement.diagrams[0].plane.planeElement; const dib = new Set(di.map(d => d.bpmnElement.id));
for (const f of flujos) if (!dib.has(f.id)) errs.push('flujo sin dibujo: ' + f.id);
for (const n of nodos) if (!dib.has(n.id)) errs.push('nodo sin dibujo: ' + n.id);
const enCarril = new Set(proc.laneSets.flatMap(ls => ls.lanes.flatMap(l => l.flowNodeRef.map(r => r.id))));
for (const n of nodos) if (!enCarril.has(n.id)) errs.push('nodo sin carril: ' + n.id);
const inicios = nodos.filter(n => n.$type === 'bpmn:StartEvent').length, fines = nodos.filter(n => n.$type === 'bpmn:EndEvent').length;
if (inicios !== 1 || fines < 1) errs.push(`inicios=${inicios} fines=${fines}`);
for (const n of nodos) { const ent = flujos.filter(f => f.targetRef.id === n.id).length, sal = flujos.filter(f => f.sourceRef.id === n.id).length;
  if (n.$type !== 'bpmn:StartEvent' && !ent) errs.push('sin entrada: ' + n.id); if (n.$type !== 'bpmn:EndEvent' && !sal) errs.push('sin salida: ' + n.id); }
const pool = di.find(d => d.bpmnElement.$type === 'bpmn:Participant').bounds;
for (const d of di) if (d.bounds && d.bpmnElement.$type !== 'bpmn:Participant' && d.bpmnElement.$type !== 'bpmn:Lane') { const b = d.bounds; if (b.x < pool.x + 60 || b.x + b.width > pool.x + pool.width || b.y < 0 || b.y + b.height > pool.height) errs.push('fuera de la piscina: ' + d.bpmnElement.id); }
console.log(errs.length ? 'FALLA\n' + errs.join('\n') : `OK: ${nodos.length} nodos, ${flujos.length} flujos, ${proc.laneSets[0].lanes.length} carriles`);
process.exit(errs.length ? 1 : 0);
