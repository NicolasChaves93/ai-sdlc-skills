// Trazado por carriles compartido por build-models.mjs y export-flat.mjs
import { DOMParser, XMLSerializer } from '@xmldom/xmldom';
export const DC = 'http://www.omg.org/spec/DD/20100524/DC';
export const DD = 'http://www.omg.org/spec/DD/20100524/DI';
export const BPMN = 'http://www.omg.org/spec/BPMN/20100524/MODEL';
export const DI = 'http://www.omg.org/spec/BPMN/20100524/DI';
export const kids = (el, ns = BPMN) => [...el.childNodes].filter(n => n.nodeType === 1 && n.namespaceURI === ns);
export const local = n => n.localName;
// Trazado por carriles (izquierda → derecha): cada paso va en el carril del rol que lo ejecuta (atributo cc:carril)
// y su columna sale del orden del flujo. Devuelve la geometría de los carriles para dibujarlos en el visor.
const CC = 'http://colombiancode.co/bpmn';
const ORDEN = ['Cliente', 'Participante', 'Administrador', 'Operador', 'Sistema'];
const GAP = 62, X0 = 62, PAD = 20;
export function carriles(doc, diagram, scopeEl) {
  const sem = {}; for (const c of kids(scopeEl)) sem[c.getAttribute('id')] = c;
  const isFlow = n => local(n) === 'sequenceFlow', isB = n => local(n) === 'boundaryEvent';
  const nodes = Object.values(sem).filter(n => !isFlow(n) && !isB(n) && !/laneSet|textAnnotation|association/.test(local(n)));
  const flows = Object.values(sem).filter(isFlow).map(f => ({ id: f.getAttribute('id'), s: f.getAttribute('sourceRef'), t: f.getAttribute('targetRef') }));
  const host = id => isB(sem[id]) ? sem[id].getAttribute('attachedToRef') : id;
  const out = {}, inn = {}; for (const n of nodes) { out[n.getAttribute('id')] = []; inn[n.getAttribute('id')] = []; }
  for (const f of flows) { const s = host(f.s); if (out[s] && inn[f.t]) { out[s].push(f.t); inn[f.t].push(s); } }
  // carril de cada nodo (los eventos y compuertas sin atributo heredan del vecino)
  const lane = {}; for (const n of nodes) { const l = n.getAttributeNS(CC, 'carril'); if (l) lane[n.getAttribute('id')] = l; }
  for (let k = 0; k < 4; k++) for (const n of nodes) { const id = n.getAttribute('id'); if (lane[id]) continue;
    const t = local(n); const ref = t === 'startEvent' ? out[id].map(x => lane[x]).find(Boolean) : inn[id].map(x => lane[x]).find(Boolean) || out[id].map(x => lane[x]).find(Boolean); if (ref) lane[id] = ref; }
  for (const n of nodes) lane[n.getAttribute('id')] ||= 'Sistema';
  // columnas: camino más largo ignorando las flechas que regresan (ciclos)
  const rank = {}, state = {}, back = new Set();
  const dfs = id => { state[id] = 1; for (const t of out[id]) { if (state[t] === 1) back.add(id + '>' + t); else if (!state[t]) dfs(t); } state[id] = 2; };
  for (const n of nodes) if (local(n) === 'startEvent') dfs(n.getAttribute('id')); for (const n of nodes) if (!state[n.getAttribute('id')]) dfs(n.getAttribute('id'));
  const ord = []; const seen = {}; const topo = id => { if (seen[id]) return; seen[id] = 1; for (const t of inn[id]) if (!back.has(t + '>' + id)) topo(t); ord.push(id); };
  for (const n of nodes) topo(n.getAttribute('id'));
  for (const id of ord) rank[id] = Math.max(0, ...inn[id].filter(p => !back.has(p + '>' + id)).map(p => rank[p] + 1));
  // tamaños que dejó el auto-trazado
  const box = {}; for (const sh of diagram.getElementsByTagNameNS(DI, 'BPMNShape')) { const b = sh.getElementsByTagNameNS(DC, 'Bounds')[0]; const id = sh.getAttribute('bpmnElement'); const big = sem[id] && /task|subProcess/i.test(local(sem[id]));
    const w = big ? 120 : +b.getAttribute('width'), h = big ? 92 : +b.getAttribute('height'); b.setAttribute('width', w); b.setAttribute('height', h); box[id] = { b, w, h }; }
  for (const lab of [...diagram.getElementsByTagNameNS(DI, 'BPMNLabel')]) lab.parentNode.removeChild(lab);
  // varios pasos en el mismo carril y columna se apilan
  const cell = {}; for (const n of nodes) { const id = n.getAttribute('id'); const k = lane[id] + '|' + rank[id]; (cell[k] ||= []).push(id); }
  const names = ORDEN.filter(l => nodes.some(n => lane[n.getAttribute('id')] === l)); const stackMax = {};
  for (const [k, ids] of Object.entries(cell)) { const l = k.split('|')[0]; stackMax[l] = Math.max(stackMax[l] || 1, ids.length); }
  const geo = []; let y = 0; const top = {}, hh = {};
  for (const l of names) { hh[l] = Math.max(150, stackMax[l] * 100 + 2 * PAD + 30); top[l] = y; geo.push({ n: l, y, h: hh[l] }); y += hh[l]; }
  // columnas con ancho propio: lo que mide su elemento más ancho + un espacio fijo
  const maxR = Math.max(0, ...Object.values(rank)); const anchoCol = Array(maxR + 1).fill(40);
  for (const n of nodes) { const id = n.getAttribute('id'); anchoCol[rank[id]] = Math.max(anchoCol[rank[id]], box[id].w); }
  const centro = [X0]; for (let r = 1; r <= maxR; r++) centro[r] = centro[r - 1] + anchoCol[r - 1] / 2 + anchoCol[r] / 2 + GAP;
  let maxX = 0;
  for (const ids of Object.values(cell)) ids.forEach((id, i) => { const l = lane[id], bx = box[id]; const cy = top[l] + (i + 0.5) * hh[l] / ids.length; const cx = centro[rank[id]];
    Object.assign(bx, { x: cx - bx.w / 2, y: cy - bx.h / 2 }); maxX = Math.max(maxX, cx + bx.w / 2); });
  for (const id of Object.keys(box)) { const e = sem[id]; if (e && isB(e)) { const h = box[e.getAttribute('attachedToRef')], o = box[id]; o.x = h.x + h.w / 2 - o.w / 2; o.y = h.y + h.h - o.h / 2; } }
  for (const o of Object.values(box)) { o.b.setAttribute('x', o.x); o.b.setAttribute('y', o.y); }
  // Flechas: las normales van en codo; las que regresan o saltan pasos en el mismo carril usan un pasillo
  // reservado arriba o abajo del carril de origen, para no pasar por encima de otros pasos.
  const pasillo = {}; const usar = (l, lado) => { const k = l + lado; pasillo[k] = (pasillo[k] || 0) + 1; return lado === 'top' ? top[l] + 11 + 8 * (pasillo[k] - 1) : top[l] + hh[l] - 11 - 8 * (pasillo[k] - 1); };
  const plane = diagram.getElementsByTagNameNS(DI, 'BPMNPlane')[0];
  const usadoAbajo = new Set(), usadoArriba = new Set();
  const nodoEn = (sid, tid, x1, x2, y1, y2) => Object.entries(box).some(([k, b]) => k !== sid && k !== tid && !isB(sem[k] || sem[sid]) && b.x < Math.max(x1, x2) && b.x + b.w > Math.min(x1, x2) && b.y < Math.max(y1, y2) && b.y + b.h > Math.min(y1, y2));
  const verticalDe = {};                         // por compuerta: el único camino que sale por el vértice de arriba/abajo
  for (const n of nodes) { const id = n.getAttribute('id'); if (!/gateway/i.test(local(n))) continue; const s0 = box[id], c0 = s0.y + s0.h / 2;
    const outs = flows.filter(f => f.s === id && box[f.t] && box[f.t].x >= s0.x + s0.w + 8); if (outs.length < 2) continue;
    const dy = f => Math.abs(box[f.t].y + box[f.t].h / 2 - c0); const mejor = outs.sort((a, b) => dy(b) - dy(a))[0]; if (dy(mejor) > 1) verticalDe[id] = mejor.id; }
  for (const fl of flows) {                      // bpmn-auto-layout no dibuja flechas: se crean aquí
    const ed = doc.createElementNS(DI, 'bpmndi:BPMNEdge'); ed.setAttribute('id', fl.id + '_di'); ed.setAttribute('bpmnElement', fl.id); plane.appendChild(ed);
    const f = sem[fl.id]; if (!f) continue; const sid = f.getAttribute('sourceRef'), tid = f.getAttribute('targetRef'); const s = box[sid], t = box[tid]; if (!s || !t) continue;
    const sc = s.y + s.h / 2, tc = t.y + t.h / 2, ls = lane[host(sid)]; let pts;
    if (isB(sem[sid])) { const bx = s.x + s.w / 2, by = s.y + s.h; pts = t.x > bx ? [[bx, by], [bx, tc], [t.x, tc]] : [[bx, by], [bx, by + 30], [t.x + t.w / 2, by + 30], [t.x + t.w / 2, t.y + t.h]]; }
    else if (t.x >= s.x + s.w + 8) {
      const mx = Math.max(s.x + s.w + 12, t.x - 22);
      const estorba = Object.entries(box).some(([k, b]) => k !== sid && k !== tid && !isB(sem[k] || sem[sid]) && b.x < mx && b.x + b.w > s.x + s.w && b.y < sc && b.y + b.h > sc);
      if (estorba) { const lado = tc > sc + 1 ? 'bot' : 'top'; const yy = usar(ls, lado); pts = [[s.x + s.w, sc], [s.x + s.w + 14, sc], [s.x + s.w + 14, yy], [t.x - 14, yy], [t.x - 14, tc], [t.x, tc]]; }
      else if (verticalDe[sid] === fl.id
        && !nodoEn(sid, tid, s.x + s.w / 2 - 1, s.x + s.w / 2 + 1, Math.min(sc, tc), Math.max(sc, tc)) && !nodoEn(sid, tid, s.x + s.w / 2, t.x, tc - 1, tc + 1)) {
        const abajo = tc > sc; (abajo ? usadoAbajo : usadoArriba).add(sid); pts = [[s.x + s.w / 2, abajo ? s.y + s.h : s.y], [s.x + s.w / 2, tc], [t.x, tc]]; }
      else pts = Math.abs(sc - tc) < 1 ? [[s.x + s.w, sc], [t.x, tc]] : [[s.x + s.w, sc], [mx, sc], [mx, tc], [t.x, tc]];
    } else {                                      // regreso hacia atrás: se prueba el pasillo de abajo y el de arriba
      const libre = (x, y1, y2) => !Object.entries(box).some(([k, b]) => k !== sid && k !== tid && !isB(sem[k] || sem[sid]) && b.x < x && b.x + b.w > x && b.y < Math.max(y1, y2) && b.y + b.h > Math.min(y1, y2));
      const sx = s.x + s.w / 2, tx = t.x + t.w / 2; let elegido = null;
      for (const lado of ['bot', 'top']) {
        const yy = lado === 'top' ? top[ls] + 11 + 8 * (pasillo[ls + 'top'] || 0) : top[ls] + hh[ls] - 11 - 8 * (pasillo[ls + 'bot'] || 0);
        const sEdge = lado === 'bot' ? s.y + s.h : s.y, tEdge = yy > t.y + t.h ? t.y + t.h : yy < t.y ? t.y : null;
        if (tEdge != null && (lado === 'bot' ? yy > sEdge : yy < sEdge) && libre(sx, sEdge, yy) && libre(tx, yy, tEdge)) { elegido = { lado, sEdge, tEdge }; break; }
      }
      elegido ||= { lado: 'bot', sEdge: s.y + s.h, tEdge: t.y + t.h };
      (elegido.lado === 'bot' ? usadoAbajo : usadoArriba).add(sid);               // lados ocupados (para ubicar el nombre de las compuertas)
      (elegido.tEdge === t.y + t.h ? usadoAbajo : usadoArriba).add(tid);
      const yy = usar(ls, elegido.lado); pts = [[sx, elegido.sEdge], [sx, yy], [tx, yy], [tx, elegido.tEdge]];
    }
    for (const w of [...ed.getElementsByTagNameNS(DD, 'waypoint')]) ed.removeChild(w);
    for (const [x, yv] of pts) { const w = doc.createElementNS(DD, 'di:waypoint'); w.setAttribute('x', x); w.setAttribute('y', yv); ed.appendChild(w); }
    if (f.getAttribute('name')) {                // etiqueta Sí/No en el primer tramo largo, junto a la compuerta de origen
      let i = 0; while (i < pts.length - 2 && Math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) < 24) i++;
      const [p0, p1] = [pts[i], pts[i + 1]], horiz = Math.abs(p1[1] - p0[1]) < 1, arriba = !horiz && p1[1] < p0[1];
      const lx = horiz ? p0[0] + 8 : arriba ? p0[0] - 30 : p0[0] + 7, ly = horiz ? p0[1] - 20 : arriba ? p0[1] - 20 : p0[1] + 8;
      const lab = doc.createElementNS(DI, 'bpmndi:BPMNLabel'), bb = doc.createElementNS(DC, 'dc:Bounds');
      const lw = Math.max(24, Math.ceil(f.getAttribute('name').length * 6.8) + 4); for (const [k, v] of Object.entries({ x: arriba ? lx + 24 - lw : lx, y: ly, width: lw, height: 14 })) bb.setAttribute(k, v); lab.appendChild(bb); ed.appendChild(lab);
    }
  }
  for (const n of nodes) {                        // nombre de las compuertas: al lado opuesto de su salida vertical
    const id = n.getAttribute('id'); if (!/gateway/i.test(local(n)) || !n.getAttribute('name')) continue;
    const g = box[id], sh = g.b.parentNode, w = 96, lineas = Math.ceil(n.getAttribute('name').length * 6.4 / w), h = 14 * lineas + 4;
    const arriba = usadoAbajo.has(id) && !usadoArriba.has(id); const y = arriba ? g.y - h - 3 : g.y + g.h + 3;
    const lab = doc.createElementNS(DI, 'bpmndi:BPMNLabel'), bb = doc.createElementNS(DC, 'dc:Bounds');
    for (const [k, v] of Object.entries({ x: g.x + g.w / 2 - w / 2, y, width: w, height: h })) bb.setAttribute(k, v); lab.appendChild(bb); sh.appendChild(lab);
  }
  return { lanes: geo, w: maxX + 80, of: lane };
}

