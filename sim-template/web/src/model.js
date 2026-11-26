// Estructura del BPMN para la interfaz (pasos, flujos, subprocesos). La simulación la hace el motor de Python.
import { BpmnModdle } from 'bpmn-moddle';

export async function parseModel(xml) {
  const { rootElement } = await new BpmnModdle().fromXML(xml);
  const proc = rootElement.rootElements.find(r => r.$type === 'bpmn:Process');
  const els = {}, flows = {};
  const scopes = {};
  const walk = (container, parentId) => {
    const id = container.id;
    const scope = { id, parent: parentId, name: container.name || id, nodes: [], boundaries: [] };
    scopes[id] = scope;
    for (const fe of container.flowElements || []) {
      if (fe.$type === 'bpmn:SequenceFlow') { flows[fe.id] = { id: fe.id, name: fe.name || '', source: fe.sourceRef.id, target: fe.targetRef.id, scope: id }; continue; }
      const t = fe.$type.replace('bpmn:', '');
      const e = { id: fe.id, type: t, name: fe.name || '', scope: id, incoming: [], outgoing: [] };
      if (t === 'BoundaryEvent') { e.attachedTo = fe.attachedToRef.id; e.interrupting = fe.cancelActivity !== false; e.timer = (fe.eventDefinitions || []).some(d => d.$type === 'bpmn:TimerEventDefinition'); scope.boundaries.push(e.id); }
      if (t === 'IntermediateCatchEvent') e.timer = (fe.eventDefinitions || []).some(d => d.$type === 'bpmn:TimerEventDefinition');
      if (t === 'SubProcess') { e.mi = !!fe.loopCharacteristics; e.child = fe.id; }
      els[fe.id] = e; scope.nodes.push(fe.id);
      if (t === 'SubProcess') walk(fe, id);
    }
  };
  walk(proc, null);
  for (const f of Object.values(flows)) { els[f.source].outgoing.push(f.id); els[f.target].incoming.push(f.id); }
  return { els, flows, scopes, rootId: proc.id, rootName: proc.name || proc.id };
}
