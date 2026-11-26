import Viewer from 'bpmn-js/lib/Viewer';
const cfg = JSON.parse(document.getElementById('cfg').textContent);
const v = new Viewer({ container: '#c' });
v.importXML(document.getElementById('xml').textContent).then(() => {
  const canvas = v.get('canvas');
  if (cfg.scope !== cfg.rootId) canvas.setRootElement(canvas.findRoot(cfg.scope + '_plane'));
  const g = cfg.lanes, H = g.lanes.reduce((a, l) => a + l.h, 0), layer = canvas.getLayer('carriles', -10), ns = 'http://www.w3.org/2000/svg';
  const mk = (t, a, cls, txt) => { const n = document.createElementNS(ns, t); for (const k in a) n.setAttribute(k, a[k]); if (cls) n.setAttribute('class', cls); if (txt) n.textContent = txt; return n; };
  layer.append(mk('rect', { x: 0, y: 0, width: g.w, height: H }, 'lane-fondo'));
  g.lanes.forEach((l, i) => {
    layer.append(mk('rect', { x: 0, y: l.y, width: 30, height: l.h }, 'lane-rotulo'));
    if (i) layer.append(mk('line', { x1: 0, x2: g.w, y1: l.y, y2: l.y }, 'lane-linea'));
    layer.append(mk('text', { x: 15, y: l.y + l.h / 2, 'text-anchor': 'middle', 'dominant-baseline': 'central', transform: `rotate(-90 15 ${l.y + l.h / 2})` }, 'lane-titulo', l.n));
  });
  layer.append(mk('line', { x1: 30, x2: 30, y1: 0, y2: H }, 'lane-linea')); layer.append(mk('rect', { x: 0, y: 0, width: g.w, height: H }, 'lane-marco'));
  const c = canvas.getContainer(); canvas.viewbox({ x: -20, y: -20, width: c.clientWidth, height: c.clientHeight });
  document.title = 'LISTO';
});
