import NavigatedViewer from 'bpmn-js/lib/NavigatedViewer';
import { parseModel } from './model.js';
import * as api from './api.js';

let XML_PLANO = '', XML_JER = '', BASE = null, CARRILES = {}, MODELO = 'modelo', UI = {};   // se cargan del servidor al arrancar (espacio de trabajo del proyecto)

const TIPOS = { StartEvent: 'Evento de inicio', EndEvent: 'Evento de fin', UserTask: 'Tarea de una persona', ServiceTask: 'Tarea del sistema', ManualTask: 'Tarea manual', Task: 'Tarea', ExclusiveGateway: 'Compuerta (un solo camino)', ParallelGateway: 'Compuerta paralela', SubProcess: 'Subproceso', BoundaryEvent: 'Temporizador límite', IntermediateCatchEvent: 'Espera' };
const METRICAS = { esperaTotal: ['Espera acumulada', 's'], esperaP95: ['Espera p95', 's'], colaMax: ['Cola máx.', ''], cortadas: ['Cortados', ''], entradas: ['Entradas', ''], servicioProm: ['Duración prom.', 's'] };
const PERFILES = { uniforme: 'Repartidas en la ventana', rampa: 'Aumento progresivo', pico: 'Todas a la vez', poisson: 'Aleatorias (Poisson)' };
const MODOS = { azar: 'Al azar (probabilidades del escenario)', mejor: 'Mejor caso (sin reprocesos, tiempos rápidos)', peor: 'Peor caso (todos los reprocesos, tiempos lentos)' };
const $ = id => document.getElementById(id);
const el = (tag, props = {}, ...kids) => { const n = Object.assign(document.createElement(tag), props); for (const k of kids) n.append(k); return n; };
const fmt = (v, u = '') => { if (!isFinite(v)) return '—'; const a = Math.abs(v); const s = a >= 100 ? v.toFixed(0) : a >= 10 ? v.toFixed(1) : v.toFixed(2); return s + (u ? ' ' + u : ''); };
const mmss = s => { s = Math.max(0, Math.round(s)); const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), x = s % 60; return (h ? h + ':' + String(m).padStart(2, '0') : m) + ':' + String(x).padStart(2, '0'); };
const hm = s => { const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60); return h ? `${h} h ${String(m).padStart(2, '0')} m` : `${m} m`; };
const clone = o => JSON.parse(JSON.stringify(o));
window.addEventListener('error', e => { document.title = 'ERROR ' + e.message; });
window.addEventListener('unhandledrejection', e => { document.title = 'ERROR ' + (e.reason && e.reason.message || e.reason); });

const viewer = new NavigatedViewer({ container: $('canvas') });
const canvas = viewer.get('canvas'), registry = viewer.get('elementRegistry'), overlays = viewer.get('overlays');

const S = { base: null, seqSim: 0, seqCrit: 0, busy: false, vista: 'plana', xml: null, xmlUsuario: null, model: null, sc: null, params: {}, modo: 'azar', perfil: 'uniforme', semilla: 7, forzar: {},
  res: null, metrica: 'esperaTotal', sel: null, clock: 0, playing: false, idx: 0, dots: [], lastSample: -1, overl: {}, flowLbl: [], marks: new Set(), cuellos: new Set(),
  live: null, movs: [], vel: 60, ultRefresco: 0, nRefresco: 0 };

let KEY = 'simv2';                       // se completa con el nombre del modelo al arrancar
const firma = () => JSON.stringify([Object.keys(S.base.params).sort(), Object.keys(S.base.elementos).sort()]);   // lo guardado solo vale para el escenario con que se guardó
function guardar() { localStorage.setItem(KEY, JSON.stringify({ firma: firma(), params: S.params, elementos: S.sc.elementos, modo: S.modo, perfil: S.perfil, semilla: S.semilla, forzar: S.forzar })); }
function cargarGuardado() {
  const sc = clone(S.base); const params = {}; for (const [k, d] of Object.entries(sc.params)) params[k] = d.valor;
  try { const g = JSON.parse(localStorage.getItem(KEY) || 'null'); if (g && g.firma !== firma()) { localStorage.removeItem(KEY); aviso('El escenario cambió desde la última vez: se restauraron los valores originales.'); } else if (g) { Object.assign(params, g.params); if (g.elementos) sc.elementos = g.elementos; S.modo = g.modo || 'azar'; S.perfil = g.perfil || 'uniforme'; S.semilla = g.semilla ?? 7; S.forzar = g.forzar || {}; } } catch { }
  S.sc = sc; S.params = params;
}
const opcionesSim = () => ({ modo: S.modo, perfil: S.perfil, semilla: S.semilla, forzar: S.forzar });
const peticion = (extra = {}) => ({ xml: S.xml, escenario: S.sc, params: S.params, ...opcionesSim(), ...extra });
function aviso(txt, ms = 6000) { const a = $('aviso'); a.textContent = txt; a.classList.add('on'); clearTimeout(aviso.t); aviso.t = setTimeout(() => a.classList.remove('on'), ms); }

// ---------- carriles propios (solo en la vista por subprocesos; la vista completa usa carriles BPMN reales) ----------
function dibujarCarriles() {
  const layer = canvas.getLayer('carriles', -10); layer.innerHTML = ''; if (S.vista !== 'subprocesos') return;
  const root = canvas.getRootElement(); const scope = root.id.replace(/_plane$/, ''); const g = CARRILES?.[scope]; if (!g) return;
  const ns = 'http://www.w3.org/2000/svg'; const mk = (t, a, cls, txt) => { const n = document.createElementNS(ns, t); for (const k in a) n.setAttribute(k, a[k]); if (cls) n.setAttribute('class', cls); if (txt) n.textContent = txt; return n; };
  const H = g.lanes.reduce((a, l) => a + l.h, 0);
  layer.append(mk('rect', { x: 0, y: 0, width: g.w, height: H }, 'lane-fondo'));
  g.lanes.forEach((l, i) => {
    layer.append(mk('rect', { x: 0, y: l.y, width: 30, height: l.h }, 'lane-rotulo'));
    if (i) layer.append(mk('line', { x1: 0, x2: g.w, y1: l.y, y2: l.y }, 'lane-linea'));
    layer.append(mk('text', { x: 15, y: l.y + l.h / 2, 'text-anchor': 'middle', 'dominant-baseline': 'central', transform: `rotate(-90 15 ${l.y + l.h / 2})` }, 'lane-titulo', l.n));
  });
  layer.append(mk('line', { x1: 30, x2: 30, y1: 0, y2: H }, 'lane-linea')); layer.append(mk('rect', { x: 0, y: 0, width: g.w, height: H }, 'lane-marco'));
}
function ajustarVista() {
  if (S.vista === 'plana') {                      // legible: no baja de 0,7× (si no cabe, se recorre arrastrando)
    const inner = canvas.viewbox().inner, c = canvas.getContainer(), cw = c.clientWidth || 900, ch = c.clientHeight || 600;
    const sc = Math.min(1.2, Math.max(Math.min(cw / (inner.width + 40), ch / (inner.height + 40)), 0.7));
    return canvas.viewbox({ x: inner.x - 20, y: inner.y + inner.height / 2 - ch / sc / 2, width: cw / sc, height: ch / sc });
  }
  const root = canvas.getRootElement(); const g = CARRILES?.[root.id.replace(/_plane$/, '')];
  if (!g) return canvas.zoom('fit-viewport', 'auto'); const H = g.lanes.reduce((a, l) => a + l.h, 0);
  const c = canvas.getContainer(), cw = c.clientWidth || 900, ch = c.clientHeight || 600;
  const fit = Math.min(cw / (g.w + 40), ch / (H + 82)); const sc = Math.min(1.3, Math.max(fit, 0.9));
  canvas.viewbox({ x: -20, y: -62, width: cw / sc, height: ch / sc });
}

// ---------- carga de un modelo / cambio de vista ----------
async function abrir(vista = S.vista) {
  pausar(); cerrarVivo(); S.vista = S.xmlUsuario ? 'plana' : vista;
  S.xml = S.xmlUsuario || (S.vista === 'plana' ? XML_PLANO : XML_JER);
  S.model = await parseModel(S.xml); if (!S.sc) cargarGuardado(); S.sel = null; S.marks.clear(); S.cuellos.clear();
  await viewer.importXML(S.xml);
  const inicio = S.vista === 'subprocesos' && !S.xmlUsuario && UI.raiz && canvas.findRoot(UI.raiz + '_plane');     // una parte se abre ya por dentro
  if (inicio) canvas.setRootElement(inicio);
  dibujarCarriles(); ajustarVista();
  crearOverlays(); pintarParams(); pintarCondiciones(); pintarControles(); verPaso(null); pintarPruebas(); await simular();
}
function pintarControles() {
  const vivo = !!S.live;
  $('modoAnalisis').classList.toggle('on', !vivo); $('modoVivo').classList.toggle('on', vivo);
  $('vistaPlana').classList.toggle('on', S.vista === 'plana'); $('vistaSub').classList.toggle('on', S.vista === 'subprocesos'); $('vistaSub').disabled = !!S.xmlUsuario;
  for (const b of document.querySelectorAll('[data-vel]')) b.classList.toggle('on', Number(b.dataset.vel) === S.vel);
  $('scrub').hidden = vivo; $('etqVivo').hidden = !vivo; $('play').textContent = S.playing ? '❚❚' : '▶';
  $('modoCaso').value = S.modo; $('perfil').value = S.perfil; $('semilla').textContent = S.semilla;
  $('nombreArchivo').textContent = S.xmlUsuario ? 'importado.bpmn' : (MODELO + (S.vista === 'plana' ? '.bpmn' : '_subprocesos.bpmn'));
}

// ---------- parámetros globales ----------
function pintarParams() {
  const box = $('params'); box.innerHTML = '';
  for (const [k, d] of Object.entries(S.sc.params)) {
    const num = el('input', { type: 'number', value: S.params[k], min: d.min, max: d.max, step: d.paso });
    const rng = el('input', { type: 'range', value: S.params[k], min: d.min, max: d.max, step: d.paso });
    const set = v => { v = Number(v); if (!isFinite(v)) return; S.params[k] = v; num.value = v; rng.value = v; cambio(); };
    num.oninput = () => set(num.value); rng.oninput = () => set(rng.value);
    box.append(el('div', { className: 'prm' },
      el('div', { className: 'l' }, el('b', { textContent: d.etiqueta }), el('span', { className: 'tag ' + d.origen, textContent: d.origen }), ...(d.br ? [el('span', { className: 'tag br', textContent: d.br })] : [])),
      el('div', { className: 'c' }, rng, num, el('span', { className: 'u', textContent: d.unidad || '' })),
      ...(d.nota ? [el('div', { className: 'n', textContent: d.nota })] : [])));
  }
}

let tmr = null; function cambio() { guardar(); $('pruebasRes')?.classList.add('viejo'); clearTimeout(tmr); tmr = setTimeout(async () => { if (S.live) iniciarVivo(true); else { await simular(); if (S.sel) verPaso(S.sel); } }, 120); }

// ---------- simulación (análisis completo) ----------
async function simular(reintento) {
  const mi = ++S.seqSim; let r;
  try { r = await api.simulate(peticion()); }
  catch (e) {
    if (mi !== S.seqSim) return;
    if (e.tipo === 'bucle' && !reintento && Object.keys(S.forzar).length) { aviso('Ese camino forzado crea un bucle sin fin (el caso nunca termina). Quité los caminos forzados.'); S.forzar = {}; guardar(); if (S.sel) verPaso(S.sel); return simular(true); }
    aviso('La simulación no se pudo completar: ' + e.message, 9000); return;
  }
  if (mi !== S.seqSim) return;                 // llegó tarde: ya se pidió otra con valores más nuevos
  S.res = r; S.clock = Math.min(S.clock, S.res.duracion); S.idx = 0; S.lastSample = -1;
  $('scrub').max = Math.ceil(S.res.duracion);
  pintarKpis(); pintarCalor(); actualizarVivo(true); pintarReloj(); pintarCriticos().catch(e => console.error(e));
}

// Recurso de referencia: el que se llame «sistema» o, si no hay, el más saturado.
const sist = r => { const v = Object.values(r.recursos); return v.find(x => /sistema/i.test(x.id)) || v.sort((a, b) => b.saturado - a.saturado)[0] || { nombre: 'Sin recursos', colaMax: 0, saturado: 0 }; };
const totalCasos = () => { const x = S.sc.raiz?.instancias ?? 1; return S.params[x] ?? x; };
// Indicadores propios del proyecto (workspace.json → ui.indicadores). «{A+B}» = veces que se pasó por A y B.
const cuenta = (r, expr) => String(expr).split('+').reduce((a, id) => a + (r.stats[id.trim()]?.entradas || 0), 0);
const plantilla = (r, txt) => String(txt || '').replace(/\{([^}]+)\}/g, (_, e) => cuenta(r, e));
function pintarKpis() {
  const r = S.res, k = $('kpis'); k.innerHTML = ''; const g = el('div', { className: 'kg' });
  const add = (t, v, sub) => g.append(el('div', { className: 'kp' }, el('small', { textContent: t }), el('b', { textContent: v }), ...(sub ? [el('em', { textContent: sub })] : [])));
  const x = sist(r);
  add('Casos completados', String(r.ciclo.n), 'de ' + totalCasos()); add('Duración total', mmss(r.duracion));
  add('Tiempo medio por caso', mmss(r.ciclo.prom), 'p95 ' + mmss(r.ciclo.p95));
  for (const i of UI.indicadores || []) add(i.titulo, String(cuenta(r, i.valor)), plantilla(r, i.detalle));
  add(x.nombre.split(' (')[0] + ' al límite', (x.saturado * 100).toFixed(1) + ' %', 'cola máx. ' + x.colaMax);
  k.append(g);
}

// ---------- mapa de calor ----------
const valor = (s, m) => s ? (s[m] || 0) : 0;
function descendientes(id) { const e = S.model.els[id]; if (!e || e.type !== 'SubProcess') return []; const out = []; for (const n of S.model.scopes[id].nodes) { out.push(n); out.push(...descendientes(n)); } return out; }
function metricaDe(id, m) {
  const e = S.model.els[id]; if (!e) return 0;
  if (e.type !== 'SubProcess') return valor(S.res.stats[id], m);
  const ds = descendientes(id).filter(d => !/Event|Gateway/.test(S.model.els[d].type) || S.model.els[d].type === 'BoundaryEvent');
  const vs = ds.map(d => valor(S.res.stats[d], m));
  if (m === 'esperaTotal') return vs.reduce((a, b) => a + b, 0);
  if (m === 'cortadas') return valor(S.res.stats[id], m);
  if (m === 'entradas' || m === 'servicioProm') return valor(S.res.stats[id], m);
  return Math.max(0, ...vs);
}
function pintarCalor() {
  for (const [id, cls] of S.marks) canvas.removeMarker(id, cls); S.marks.clear();
  const m = S.metrica, [nom, u] = METRICAS[m]; const vals = {}; let max = 0;
  for (const id of Object.keys(S.model.els)) { const e = S.model.els[id]; if (/Event|Gateway/.test(e.type) && e.type !== 'BoundaryEvent') continue; const v = metricaDe(id, m); vals[id] = v; if (v > max) max = v; }
  for (const id of Object.keys(S.model.els)) {
    const o = S.overl[id]; if (!o) continue; const v = vals[id] || 0;
    if (v > 0 && max > 0) { const lvl = Math.max(1, Math.ceil(5 * v / max)); const cls = 'heat-' + lvl; canvas.addMarker(id, cls); S.marks.add([id, cls]); o.m.textContent = fmt(v, u); o.m.parentElement.style.display = ''; }
    else o.m.parentElement.style.display = 'none';
  }
}
$('verTodo').onclick = () => { try { canvas.zoom('fit-viewport', 'auto'); } catch { } };
$('metrica').onchange = e => { S.metrica = e.target.value; pintarCalor(); };

// ---------- overlays (cifra del mapa de calor y contador en vivo) ----------
function crearOverlays() {
  for (const o of Object.values(S.overl)) { overlays.remove(o.mid); overlays.remove(o.lid); } S.overl = {};
  for (const l of S.flowLbl) overlays.remove(l); S.flowLbl = [];
  for (const id of Object.keys(S.model.els)) {
    if (!registry.get(id)) continue;
    const mt = el('span', { className: 'ov-m' }), lv = el('span', { className: 'ov-l' });
    const mw = el('div', {}, mt), lw = el('div', {}, lv); lw.style.display = 'none';
    const mid = overlays.add(id, 'm', { position: { bottom: -9, left: 0 }, html: mw }), lid = overlays.add(id, 'l', { position: { top: -9, right: 0 }, html: lw });
    S.overl[id] = { m: mt, l: lv, lw, mid, lid };
  }
}

function pintarSnapshot(s, activos) {
  for (const [id, o] of Object.entries(S.overl)) {
    const c = s[id];
    if (c && (c[0] || c[1] || c[2])) { const t = []; if (c[0]) t.push('⏳' + c[0]); if (c[1]) t.push('⚙' + c[1]); if (c[2]) t.push('▣' + c[2]); o.l.textContent = t.join(' '); o.lw.style.display = ''; } else o.lw.style.display = 'none';
    const cuello = !!(c && c[0] >= 3);                       // 3 o más esperando = cuello de botella en vivo
    if (cuello && !S.cuellos.has(id)) { canvas.addMarker(id, 'cuello'); S.cuellos.add(id); } else if (!cuello && S.cuellos.has(id)) { canvas.removeMarker(id, 'cuello'); S.cuellos.delete(id); }
  }
  $('activos').textContent = 'En curso: ' + activos;
}
function actualizarVivo(force) {
  const r = S.res; if (!r || S.live) return; const sm = r.samples; if (!sm.length) return;
  const dt = sm.length > 1 ? sm[1].t - sm[0].t : 1; const i = Math.min(sm.length - 1, Math.floor(S.clock / dt));
  if (!force && i === S.lastSample) return; S.lastSample = i; pintarSnapshot(sm[i].s, sm[i].a);
}

// ---------- puntos críticos ----------
const esTarea = id => /Task/.test(S.model.els[id]?.type || '');
function sec(box, titulo, nota) { box.append(el('h2', { textContent: titulo, style: 'margin:14px 0 4px' })); if (nota) box.append(el('p', { className: 'hint', textContent: nota })); }
async function pintarCriticos(rapido) {
  const tok = ++S.seqCrit;
  const box = $('crit'); box.innerHTML = ''; const r = S.res; const items = [];
  const usan = rid => Object.entries(S.sc.elementos).filter(([, c]) => c.recurso === rid).map(([id]) => id);
  for (const x of Object.values(r.recursos)) {
    const tareas = usan(x.id).sort((a, b) => valor(r.stats[b], 'esperaTotal') - valor(r.stats[a], 'esperaTotal')); const peor = tareas[0];
    if (peor && (x.saturado > 0.03 || x.colaMax > x.capacidad * 2) && valor(r.stats[peor], 'esperaTotal') > 1)
      items.push({ score: valor(r.stats[peor], 'esperaTotal'), sev: x.saturado > 0.2 || x.colaMax > x.capacidad * 10 ? 'alto' : 'medio', id: peor,
        t: `Cuello de botella: ${x.nombre.split(' (')[0]}`, d: `Capacidad ${x.capacidad}. Cola máxima ${x.colaMax}; al límite el ${(x.saturado * 100).toFixed(1)} % del tiempo. El paso que más espera acumula es «${S.model.els[peor].name}» (${fmt(valor(r.stats[peor], 'esperaTotal'), 's')} en total, p95 ${fmt(valor(r.stats[peor], 'esperaP95'), 's')}).` });
  }
  for (const s of Object.values(r.stats)) { const e = S.model.els[s.id]; if (e?.type === 'SubProcess' && s.cortadas > 0) {
      const hijos = S.model.scopes[s.id].nodes.find(n => S.model.els[n].type === 'StartEvent'); const lleg = hijos ? valor(r.stats[hijos], 'entradas') : 0; const pct = lleg ? ` (${(100 * s.cortadas / lleg).toFixed(1)} % de los ${lleg} que empezaron)` : '';
      items.push({ score: 1e6 + s.cortadas, sev: s.cortadas / (lleg || 1) > 0.1 ? 'alto' : 'medio', id: s.id, t: 'Pasos cortados por vencer el tiempo', d: `${s.cortadas} instancias de «${e.name}» se cortaron${pct}. Puede ser falta de capacidad o un plazo demasiado corto.` }); } }
  const ya = new Set(items.map(i => i.id));
  for (const s of Object.values(r.stats)) { if (esTarea(s.id) && !ya.has(s.id) && s.esperaP95 > 3) items.push({ score: s.esperaTotal, sev: 'bajo', id: s.id, t: `Espera alta en «${S.model.els[s.id].name}»`, d: `La espera p95 es ${fmt(s.esperaP95, 's')} y la máxima ${fmt(s.esperaMax, 's')}.` }); }
  items.sort((a, b) => b.score - a.score);

  sec(box, 'Alertas');
  if (!items.length) box.append(el('div', { className: 'card ok' }, el('b', { textContent: 'Sin alertas con estos parámetros' }), el('p', { textContent: 'No hay colas ni cortes relevantes. Mira abajo dónde se va el tiempo, y sube la carga o baja la capacidad para forzar un cuello de botella.' })));
  for (const it of items.slice(0, 6)) box.append(el('div', { className: 'card ' + it.sev, onclick: () => ir(it.id) }, el('b', { textContent: it.t }), el('p', { textContent: it.d }), el('div', { className: 'go', textContent: 'Ver en el diagrama →' })));

  // dónde se va el tiempo (trabajo + espera acumulados de todos los participantes)
  const filas = Object.values(r.stats).filter(s => esTarea(s.id)).map(s => ({ id: s.id, tot: s.servicioProm * s.completadas + s.esperaTotal, s })).filter(f => f.tot > 0).sort((a, b) => b.tot - a.tot);
  const suma = filas.reduce((a, f) => a + f.tot, 0);
  sec(box, 'Dónde se va el tiempo', 'Suma de trabajo + espera de todos los casos, por paso. Los pasos de una persona pesan mucho aunque no sean un problema.');
  for (const f of filas.slice(0, 7)) {
    const pct = 100 * f.tot / suma; const nom = S.model.els[f.id].name;
    box.append(el('div', { className: 'card bajo', style: 'padding:6px 9px;border-left-color:#8aa4d6', onclick: () => ir(f.id) },
      el('div', { style: 'display:flex;justify-content:space-between;gap:8px' }, el('b', { textContent: nom, style: 'font-weight:600' }), el('span', { textContent: pct.toFixed(0) + ' %', style: 'font-variant-numeric:tabular-nums;color:#445' })),
      el('div', { style: `height:6px;border-radius:3px;background:#e4e9f2;margin:4px 0` }, el('div', { style: `height:6px;border-radius:3px;background:#5b8def;width:${Math.max(2, pct)}%` })),
      el('div', { className: 'hint', style: 'margin:0', textContent: `${f.s.entradas} veces · trabajo ${fmt(f.s.servicioProm, 's')} + espera ${fmt(f.s.esperaProm, 's')} por vez` })));
  }

  // casos borde: caminos de compuertas poco usados o nunca usados
  const raros = [];
  for (const e of Object.values(S.model.els)) { if (e.type !== 'ExclusiveGateway' || e.outgoing.length < 2) continue; const tot = e.outgoing.reduce((a, f) => a + (r.flowCount[f] || 0), 0); if (!tot) continue;
    for (const f of e.outgoing) { const n = r.flowCount[f] || 0, sh = n / tot; if (sh < 0.1) raros.push({ gw: e, f, n, sh }); } }
  raros.sort((a, b) => a.sh - b.sh);
  sec(box, 'Casos borde a probar', 'Caminos que casi no se usan. Si salen en 0 %, con estos parámetros ese camino nunca ocurre: hay que forzarlo en las pruebas.');
  if (!raros.length) box.append(el('p', { className: 'hint', textContent: 'Todos los caminos de las compuertas se usan con frecuencia.' }));
  for (const x of raros.slice(0, 8)) box.append(el('div', { className: 'card ' + (x.n ? 'bajo' : 'medio'), style: 'padding:6px 9px', onclick: () => ir(x.gw.id) },
    el('b', { style: 'font-weight:600', textContent: `«${x.gw.name || x.gw.id}» → ${S.model.flows[x.f].name || S.model.els[S.model.flows[x.f].target].name}` }),
    el('div', { className: 'hint', style: 'margin:0', textContent: x.n ? `${(x.sh * 100).toFixed(1)} % (${x.n} veces)` : '0 % — nunca ocurre en esta simulación' })));

  if (rapido) return;
  // qué pasa si cambia la capacidad (se pide al servidor)
  for (const x of Object.values(r.recursos)) {
    const clave = String(S.sc.recursos[x.id].capacidad).trim(); const prm = S.sc.params[clave]; if (!prm || !usan(x.id).length || (x.saturado === 0 && x.colaMax <= 1)) continue;
    sec(box, `Qué pasa si cambia la capacidad: ${x.nombre.split(' (')[0]}`, 'Misma simulación con distinta capacidad (el resto igual).');
    const tab = el('table', { style: 'width:100%;border-collapse:collapse;font-size:12px;background:#fff;border:1px solid #e0e4ea;border-radius:6px' });
    tab.append(el('tr', { style: 'color:#667;text-align:right' }, ...['Capacidad', 'Cola máx.', 'Cortados', 'Espera acum.'].map((t, i) => el('th', { textContent: t, style: 'padding:4px 6px;font-weight:600;' + (i ? '' : 'text-align:left') }))));
    const cortes = rr => Object.values(rr.stats).filter(z => S.model.els[z.id]?.type === 'SubProcess').reduce((a, z) => a + z.cortadas, 0);
    for (const f of [0.5, 1, 2, 4]) { const v = Math.max(1, Math.round(S.params[clave] * f)); if (f !== 1 && v === S.params[clave]) continue; const rr = f === 1 ? r : await api.simulate(peticion({ params: { ...S.params, [clave]: v }, sinMuestras: true })); if (tok !== S.seqCrit) return;
      const esp = Object.values(rr.stats).filter(z => esTarea(z.id)).reduce((a, z) => a + z.esperaTotal, 0);
      tab.append(el('tr', { style: 'text-align:right;border-top:1px solid #eef0f4' + (f === 1 ? ';background:#f1f6ff;font-weight:600' : '') }, el('td', { textContent: v + (f === 1 ? ' (actual)' : ''), style: 'padding:4px 6px;text-align:left' }), el('td', { textContent: rr.recursos[x.id].colaMax, style: 'padding:4px 6px' }), el('td', { textContent: cortes(rr), style: 'padding:4px 6px' }), el('td', { textContent: fmt(esp, 's'), style: 'padding:4px 6px' }))); }
    box.append(tab);
  }
}

function ir(id) {
  const e = S.model.els[id]; if (!e) return;
  if (S.vista === 'subprocesos') { const root = canvas.findRoot(e.scope === S.model.rootId ? e.scope : e.scope + '_plane'); if (root) canvas.setRootElement(root); }
  else { const sh = registry.get(id); if (sh) canvas.scrollToElement(sh); }
  verPaso(id); mostrarTab('paso');
}

// ---------- propiedades del paso ----------
function mostrarTab(t) { for (const b of document.querySelectorAll('.tabs2 button')) b.classList.toggle('on', b.dataset.tab === t); $('crit').hidden = t !== 'crit'; $('paso').hidden = t !== 'paso'; $('pruebas').hidden = t !== 'pruebas'; }
for (const b of document.querySelectorAll('.tabs2 button')) b.onclick = () => mostrarTab(b.dataset.tab);
const setPath = (o, p, v) => { const a = p.split('.'); let c = o; for (const k of a.slice(0, -1)) c = c[k] ||= {}; if (v === '' || v == null) delete c[a.at(-1)]; else c[a.at(-1)] = v; };
const getPath = (o, p) => p.split('.').reduce((c, k) => c?.[k], o);
const parse = v => { v = String(v).trim(); return v !== '' && isFinite(Number(v)) ? Number(v) : v; };
const DIST = { const: [['valor', 'Valor (s)']], uniforme: [['min', 'Mínimo (s)'], ['max', 'Máximo (s)']], exp: [['media', 'Media (s)']], lognormal: [['media', 'Media (s)'], ['cv', 'Variación (cv)']], triangular: [['min', 'Mínimo (s)'], ['moda', 'Más probable (s)'], ['max', 'Máximo (s)']] };

function campo(id, etiqueta, path, opts = {}) {
  const cfg = (S.sc.elementos[id] ||= {}); const v = getPath(cfg, path);
  const inp = el('input', { type: 'text', value: v ?? '', placeholder: opts.ph || '' });
  inp.onchange = () => { setPath(cfg, path, parse(inp.value)); cambio(); verPaso(id); };
  const w = el('div', { className: 'f' }, el('label', { textContent: etiqueta }), inp);
  const p = typeof v === 'string' ? S.sc.params[v.trim()] : null;
  if (p) w.append(el('div', { className: 'lig', textContent: `↳ ligado al parámetro «${p.etiqueta}» (${p.origen}${p.br ? ', ' + p.br : ''}). Se cambia en el panel Escenario.` }));
  else if (opts.supuesto !== false && v != null && v !== '') w.append(el('div', { className: 'hint', textContent: 'Supuesto de simulación (no es una regla del negocio).' }));
  return w;
}
function editorDur(id, etiqueta, path) {
  const cfg = (S.sc.elementos[id] ||= {}); const d = getPath(cfg, path) || { tipo: 'const', valor: 0 };
  const w = el('div', {}); const sel = el('select', {}); for (const t of Object.keys(DIST)) sel.append(el('option', { value: t, textContent: { const: 'Fijo', uniforme: 'Uniforme', exp: 'Exponencial', lognormal: 'Lognormal (humano)', triangular: 'Triangular' }[t], selected: t === d.tipo }));
  sel.onchange = () => { setPath(cfg, path, { tipo: sel.value, ...Object.fromEntries(DIST[sel.value].map(([k], i) => [k, i ? 1 : 1])) }); cambio(); verPaso(id); };
  w.append(el('div', { className: 'f' }, el('label', { textContent: etiqueta }), sel));
  const g = el('div', { className: 'row2' }); for (const [k, l] of DIST[d.tipo] || []) g.append(campo(id, l, path + '.' + k)); w.append(g); return w;
}

function verPaso(id) {
  if (S.sel) canvas.removeMarker(S.sel, 'sel'); S.sel = id; const box = $('paso'); box.innerHTML = '';
  if (!id) { box.append(el('p', { className: 'hint', textContent: 'Haz clic en un paso del diagrama para ver su descripción, sus tiempos y poder cambiarlos.' })); return; }
  const e = S.model.els[id]; if (!e) { S.sel = null; return; } canvas.addMarker(id, 'sel'); const cfg = (S.sc.elementos[id] ||= {});
  box.append(el('p', { className: 'tit', textContent: e.name || '(sin nombre)' }), el('p', { className: 'sub', textContent: (TIPOS[e.type] || e.type) + ' · ' + id }));
  const ta = el('textarea', { value: cfg.detalle || '', placeholder: 'Describe qué pasa en este paso y qué es configurable…' }); ta.onchange = () => { cfg.detalle = ta.value; guardar(); };
  box.append(el('div', { className: 'f' }, el('label', { textContent: 'Descripción del paso' }), ta));
  const s = S.res.stats[id];
  if (s) { const g = el('div', { className: 'stat' }); const add = (a, b) => g.append(el('span', { textContent: a }), el('b', { textContent: b }));
    add('Veces que pasa', s.entradas); if (s.cortadas) add('Cortadas por tiempo', s.cortadas); if (s.esperaTotal > 0) { add('Espera promedio', fmt(s.esperaProm, 's')); add('Espera p95', fmt(s.esperaP95, 's')); add('Espera máxima', fmt(s.esperaMax, 's')); add('Cola máxima', s.colaMax); } if (s.servicioProm > 0) { add('Duración promedio', fmt(s.servicioProm, 's')); add('Duración p95', fmt(s.servicioP95, 's')); } box.append(g); }
  const t = e.type;
  if (/Task/.test(t) || t === 'IntermediateCatchEvent') {
    box.append(editorDur(id, 'Cuánto tarda este paso', 'dur'));
    if (/Task/.test(t)) {
      const sel = el('select', {}, el('option', { value: '', textContent: 'Nadie (sin límite de capacidad)' })); for (const [rid, r] of Object.entries(S.sc.recursos)) sel.append(el('option', { value: rid, textContent: r.nombre, selected: cfg.recurso === rid }));
      sel.onchange = () => { setPath(cfg, 'recurso', sel.value); cambio(); verPaso(id); }; box.append(el('div', { className: 'f' }, el('label', { textContent: 'Quién lo ejecuta (recurso con cola)' }), sel));
      if (cfg.recurso) box.append(campo(id, 'Multiplicador del tiempo (puede usar parámetros, ej. N*0.005)', 'escala'));
    }
  }
  if (t === 'BoundaryEvent') box.append(editorDur(id, 'Cuándo vence el temporizador', 'dur'));
  if (t === 'ExclusiveGateway' && e.outgoing.length > 1) {
    if (cfg.tipo === 'contador') { box.append(el('p', { className: 'hint', textContent: 'Esta compuerta repite el camino «' + (S.model.flows[cfg.flujo]?.name || cfg.flujo) + '» el número de veces indicado y luego sigue por el otro.' }), campo(id, 'Número de repeticiones', 'veces')); }
    else { box.append(el('p', { className: 'hint', textContent: 'Probabilidad de cada camino (0 a 1). Si dejas uno vacío, recibe lo que sobre.' }));
      for (const fid of e.outgoing) { const f = S.model.flows[fid]; box.append(campo(id, `→ ${f.name || ''} ${S.model.els[f.target].name ? '(' + S.model.els[f.target].name + ')' : ''}`.trim(), 'prob.' + fid, { ph: 'resto' })); } }
    const fz = el('select', {}, el('option', { value: '', textContent: 'Automático (según probabilidades o modo)' }));
    for (const fid of e.outgoing) { const f = S.model.flows[fid]; fz.append(el('option', { value: fid, selected: S.forzar[id] === fid, textContent: 'Siempre → ' + (f.name || '') + ' (' + (S.model.els[f.target].name || f.target) + ')' })); }
    fz.onchange = () => { if (fz.value) S.forzar[id] = fz.value; else delete S.forzar[id]; if (S.live) api.liveForce(S.live.id, id, fz.value || null).catch(e => aviso(e.message)); cambio(); };
    box.append(el('div', { className: 'f' }, el('label', { textContent: 'Forzar camino (activar un camino alterno)' }), fz));
    const c = S.res.flowCount; box.append(el('p', { className: 'hint', textContent: 'Caminos tomados: ' + e.outgoing.map(f => `${S.model.flows[f].name || f}: ${c[f] || 0}`).join(' · ') }));
  }
  if (t === 'SubProcess') {
    box.append(el('p', { className: 'hint', textContent: e.mi ? 'Se repite en paralelo (multi-instancia). Para ver su interior, haz clic en el «+».' : 'Haz clic en el «+» para ver su interior.' }));
    if (e.mi) { box.append(campo(id, 'Cuántos entran (instancias)', 'instancias')); box.append(editorDur(id, 'Cómo llegan (retraso de cada uno)', 'llegadas')); }
  }
  box.append(el('button', { textContent: 'Restablecer este paso', onclick: () => { S.sc.elementos[id] = clone(S.base.elementos[id] || {}); cambio(); verPaso(id); } }));
}
viewer.on('element.click', ev => { const id = ev.element.id; if (S.model?.els[id]) { verPaso(id); mostrarTab('paso'); } });

// ---------- reproducción (análisis) y modo en vivo ----------
function pausar() { S.playing = false; $('play').textContent = '▶'; }
function reproducir() {
  if (!S.live && S.clock >= S.res.duracion) { S.clock = 0; S.idx = 0; limpiarDots(); }
  S.playing = true; $('play').textContent = '❚❚'; S.t0 = performance.now(); requestAnimationFrame(tick);
}
$('play').onclick = () => S.playing ? pausar() : reproducir();
$('scrub').oninput = e => { S.clock = Number(e.target.value); S.idx = 0; limpiarDots(); actualizarVivo(true); pintarReloj(); };
const pintarReloj = () => { $('reloj').textContent = mmss(S.clock); if (!S.live) $('scrub').value = S.clock; };
function limpiarDots() { for (const d of S.dots) d.node.remove(); S.dots = []; }
function tick(now) {
  if (!S.playing) return; const dt = Math.min(0.1, (now - S.t0) / 1000); S.t0 = now; S.clock += dt * S.vel;
  if (S.live) {
    let n = 0; for (const fid of S.movs) if (S.dots.length < 160 && n++ < 60) lanzarDot(fid, now); S.movs.length = 0;
    if (!S.busy) {                              // una petición a la vez: el reloj sigue avanzando mientras el servidor responde
      S.busy = true; const vivo = S.live, completo = now - S.ultRefresco > 500;
      api.liveAdvance(vivo.id, S.clock, completo).then(r => { if (S.live === vivo) aplicarVivo(r, now, completo); }).catch(e => { pausar(); aviso('Modo en vivo: ' + e.message, 9000); }).finally(() => { S.busy = false; });
    }
  } else {
    const r = S.res; if (S.clock >= r.duracion) { S.clock = r.duracion; pausar(); }
    const log = r.log; if (S.idx && log[S.idx - 1] && log[S.idx - 1][0] > S.clock) S.idx = 0;
    while (S.idx < log.length && log[S.idx][0] <= S.clock) { if (S.dots.length < 160) lanzarDot(log[S.idx][1], now); S.idx++; }
    actualizarVivo();
  }
  S.dots = S.dots.filter(d => { const k = (now - d.t) / 650; if (k >= 1) { d.node.remove(); return false; } const p = punto(d.pts, k); d.node.setAttribute('cx', p[0]); d.node.setAttribute('cy', p[1]); return true; });
  pintarReloj(); if (S.playing) requestAnimationFrame(tick);
}
function lanzarDot(fid, now) {
  const f = registry.get(fid); if (!f || !f.waypoints || canvas.findRoot(f) !== canvas.getRootElement()) return;
  const layer = canvas.getLayer('tokens', 3000); const node = document.createElementNS('http://www.w3.org/2000/svg', 'circle'); node.setAttribute('r', 5.5); node.setAttribute('class', 'dot'); layer.appendChild(node);
  S.dots.push({ node, t: now, pts: f.waypoints.map(p => [p.x, p.y]) });
}
function punto(pts, k) { let tot = 0; const seg = []; for (let i = 1; i < pts.length; i++) { const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(l); tot += l; } let d = k * tot; for (let i = 0; i < seg.length; i++) { if (d <= seg[i] || i === seg.length - 1) { const u = seg[i] ? Math.min(1, d / seg[i]) : 0; return [pts[i][0] + (pts[i + 1][0] - pts[i][0]) * u, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * u]; } d -= seg[i]; } return pts[0]; }
viewer.on('root.set', () => { limpiarDots(); if (!S.model) return; setTimeout(() => { try { dibujarCarriles(); ajustarVista(); } catch (e) { console.error(e); } }, 30); });

// modo en vivo: el motor (servidor) avanza con el reloj; se pueden inyectar eventos y forzar caminos mientras corre
function aplicarVivo(r, now, completo) {
  S.live.activos = r.activos; S.live.pendiente = r.pendiente; S.movs.push(...r.movs); if (S.movs.length > 400) S.movs.splice(0, S.movs.length - 400);
  pintarSnapshot(r.snapshot, r.activos);
  if (completo && r.resultados) { S.ultRefresco = now; S.res = r.resultados; S.nRefresco++; pintarKpis(); pintarCalor(); if (S.nRefresco % 6 === 0) pintarCriticos(true); }
  if (!r.pendiente && S.playing) { pausar(); aviso('Todos los casos terminaron. Inyecta más o reinicia.'); }
}
function cerrarVivo() { if (S.live) api.liveClose(S.live.id); S.live = null; }
async function iniciarVivo(mantener) {
  const seguia = S.playing; pausar(); limpiarDots(); S.movs = []; cerrarVivo();
  try {
    const c = await api.liveCreate(peticion({ sinMuestras: true })); S.live = { id: c.id, activos: 0, pendiente: true };
    S.clock = 0; S.ultRefresco = 0; S.nRefresco = 0; const r = await api.liveAdvance(c.id, 0, true);
    S.res = r.resultados; pintarControles(); pintarSnapshot(r.snapshot, r.activos); pintarKpis(); pintarCalor(); pintarCriticos(true); pintarReloj();
  } catch (e) { S.live = null; pintarControles(); aviso('No se pudo iniciar el modo en vivo: ' + e.message, 9000); return; }
  if (mantener && seguia) reproducir();
}
function salirVivo() { if (!S.live) return; pausar(); limpiarDots(); cerrarVivo(); for (const id of S.cuellos) canvas.removeMarker(id, 'cuello'); S.cuellos.clear(); S.clock = 0; pintarControles(); simular(); }
$('modoAnalisis').onclick = salirVivo; $('modoVivo').onclick = () => { if (!S.live) iniciarVivo(); };
for (const b of document.querySelectorAll('[data-vel]')) b.onclick = () => { S.vel = Number(b.dataset.vel); pintarControles(); };
const inyectar = async (n, cada) => { if (!S.live) await iniciarVivo(); if (!S.live) return; try { await api.liveInject(S.live.id, n, cada); } catch (e) { aviso(e.message); return; } if (!S.playing) reproducir(); aviso(`${n} caso${n > 1 ? 's' : ''} inyectado${n > 1 ? 's' : ''} en el reloj ${mmss(S.clock)}.`, 2500); };
$('btnInyectar').onclick = () => inyectar(1, 0); $('btnRafaga').onclick = () => inyectar(10, 3);
$('vistaPlana').onclick = () => { if (S.vista !== 'plana') abrir('plana'); }; $('vistaSub').onclick = () => { if (S.vista !== 'subprocesos' && !S.xmlUsuario) abrir('subprocesos'); };

// condiciones de la prueba: modo del flujo, perfil de llegadas, semilla
function pintarCondiciones() {
  const m = $('modoCaso'), p = $('perfil'); m.innerHTML = ''; p.innerHTML = '';
  for (const [k, v] of Object.entries(MODOS)) m.append(el('option', { value: k, textContent: v })); for (const [k, v] of Object.entries(PERFILES)) p.append(el('option', { value: k, textContent: v }));
  m.value = S.modo; p.value = S.perfil;
  m.onchange = () => { S.modo = m.value; cambio(); }; p.onchange = () => { S.perfil = p.value; cambio(); };
  $('btnSemilla').onclick = () => { S.semilla = 1 + Math.floor(Math.random() * 9000); $('semilla').textContent = S.semilla; cambio(); };
}

// ---------- pruebas: comparar casos y aumento de usuarios ----------
let VARS = {};
function variables() {
  if (UI.crecimiento) return UI.crecimiento;
  const out = {};
  for (const [k, d] of Object.entries(S.sc.params)) {
    const vals = [...new Set([0.5, 1, 2, 4, 8].map(f => Math.min(d.max ?? Infinity, Math.max(d.min ?? 0, +(d.valor * f).toPrecision(3)))))];
    if (vals.length > 1) out[k] = { etq: d.etiqueta, vals };
  }
  return out;
}
const reproc = r => (UI.reprocesos || []).reduce((a, id) => a + cuenta(r, id), 0);
function tabla(cab, filas) {
  const t = el('table', { className: 'tbl' }); t.append(el('tr', {}, ...cab.map((c, i) => el('th', { textContent: c, className: i ? 'num' : '' }))));
  for (const f of filas) t.append(el('tr', { className: f.cls || '' }, ...f.c.map((c, i) => el('td', { textContent: c, className: i ? 'num' : '' })))); return t;
}
function pintarPruebas() {
  const box = $('pruebas'); box.innerHTML = ''; VARS = variables();
  box.append(el('h2', { textContent: 'Comparar casos' }), el('p', { className: 'hint', textContent: 'Corre el mismo escenario en mejor caso, al azar y peor caso, y 30 veces al azar con distintas semillas.' }),
    el('button', { className: 'primario', textContent: 'Comparar mejor / azar / peor', onclick: comparar }), el('div', { id: 'resComparar' }),
    el('h2', { textContent: 'Aumento de carga', style: 'margin-top:20px' }), el('p', { className: 'hint', textContent: 'Sube la carga paso a paso (el resto del escenario queda igual) y busca el punto donde el sistema se quiebra.' }));
  const sel = el('select', { id: 'varCrec' }); for (const [k, v] of Object.entries(VARS)) sel.append(el('option', { value: k, textContent: v.etq }));
  box.append(el('div', { className: 'fila' }, sel, el('button', { className: 'primario', textContent: 'Probar aumento', onclick: crecimiento })), el('div', { id: 'resCrecim' }));
  box.append(el('h2', { textContent: 'Análisis con PM4Py', style: 'margin-top:20px' }), el('p', { className: 'hint', textContent: 'Genera el registro de eventos del escenario actual (con el contrato de trazabilidad), lo compara con el BPMN y busca los cuellos de botella. Es el mismo análisis que se hará con los registros reales.' }),
    el('div', { className: 'fila' }, el('button', { className: 'primario', textContent: 'Analizar escenario', onclick: analizar }), el('button', { textContent: '⤓ Registro XES', onclick: exportarXes })), el('div', { id: 'resAnalisis' }));
  box.append(el('div', { id: 'pruebasRes' }));
}
async function comparar() {
  const dest = $('resComparar'); dest.innerHTML = ''; const prog = el('p', { className: 'hint', textContent: 'Calculando…' }); dest.append(prog);
  const sim = (extra) => api.simulate(peticion({ sinMuestras: true, ...extra }));
  try {
    const filas = [];
    for (const [n, m] of [['Mejor caso', 'mejor'], ['Al azar', 'azar'], ['Peor caso', 'peor']]) { const r = await sim({ modo: m }); filas.push({ r, c: [n, hm(r.ciclo.prom), hm(r.ciclo.p95), hm(r.duracion), String(sist(r).colaMax), ...(UI.reprocesos ? [String(reproc(r))] : [])], cls: m === 'peor' ? 'peor' : m === 'mejor' ? 'mejor' : '' }); }
    const mc = []; for (let i = 0; i < 30; i++) { prog.textContent = `Calculando… corrida al azar ${i + 1} de 30`; mc.push((await sim({ modo: 'azar', semilla: 1000 + i })).ciclo.prom); } mc.sort((a, b) => a - b);
    prog.remove(); dest.append(tabla(['Caso', 'Medio', 'p95', 'Total', 'Cola', ...(UI.reprocesos ? ['Repr.'] : [])], filas));
    const q = p => mc[Math.min(mc.length - 1, Math.floor(p * mc.length))];
    dest.append(el('p', { className: 'hint', style: 'margin-top:8px', textContent: `30 corridas al azar · tiempo medio por caso: mínimo ${hm(mc[0])} · mediana ${hm(q(.5))} · p95 ${hm(q(.95))} · máximo ${hm(mc.at(-1))}.` }));
    const d = (filas[2].r.ciclo.prom / filas[0].r.ciclo.prom); dest.append(el('p', { className: 'hint', textContent: `El peor caso tarda ${d.toFixed(1)}× el mejor caso. La diferencia son los reprocesos y los tiempos lentos.` }));
  } catch (e) { prog.textContent = 'No se pudo calcular: ' + e.message; }
}
function grafico(f, v) {
  const W = 330, H = 190, m = { l: 38, r: 38, t: 14, b: 38 }, iw = W - m.l - m.r, ih = H - m.t - m.b; const ns = 'http://www.w3.org/2000/svg';
  const mk = (t, a, txt) => { const n = document.createElementNS(ns, t); for (const k in a) n.setAttribute(k, a[k]); if (txt != null) n.textContent = txt; return n; };
  const svg = mk('svg', { viewBox: `0 0 ${W} ${H}`, width: '100%' }); const maxP = Math.max(...f.map(x => x.prom)) || 1; const bw = iw / f.length;
  svg.append(mk('line', { x1: m.l, x2: W - m.r, y1: m.t + ih, y2: m.t + ih, stroke: '#9aa1ab' }));
  f.forEach((x, i) => { const h = ih * x.prom / maxP, cx = m.l + bw * (i + 0.5);
    svg.append(mk('rect', { x: cx - bw * 0.32, y: m.t + ih - h, width: bw * 0.64, height: h, fill: '#8fb0f4', rx: 3 }));
    svg.append(mk('text', { x: cx, y: m.t + ih + 14, 'text-anchor': 'middle', 'font-size': 10, fill: '#444' }, x.x >= 1000 ? (x.x / 1000) + ' k' : x.x));
    svg.append(mk('text', { x: cx, y: m.t + ih - h - 3, 'text-anchor': 'middle', 'font-size': 9, fill: '#2a4a8a' }, hm(x.prom).replace(' h ', 'h').replace(' m', '')));
  });
  const pts = f.map((x, i) => [m.l + bw * (i + 0.5), m.t + ih - ih * Math.min(1, x.sat)]); svg.append(mk('polyline', { points: pts.map(p => p.join(',')).join(' '), fill: 'none', stroke: '#e0803a', 'stroke-width': 2 }));
  pts.forEach(p => svg.append(mk('circle', { cx: p[0], cy: p[1], r: 3, fill: '#e0803a' })));
  svg.append(mk('text', { x: W - m.r + 4, y: m.t + 4, 'font-size': 9, fill: '#c0651c' }, '100 %')); svg.append(mk('text', { x: W - m.r + 4, y: m.t + ih, 'font-size': 9, fill: '#c0651c' }, '0 %'));
  svg.append(mk('text', { x: 4, y: m.t + 4, 'font-size': 9, fill: '#2a4a8a' }, 'tiempo')); svg.append(mk('text', { x: W / 2, y: H - 6, 'text-anchor': 'middle', 'font-size': 10, fill: '#444' }, VARS[v].etq));
  const q = f.findIndex((x, i) => i > 0 && (x.prom > 1.5 * f[0].prom || x.sat > 0.2));
  if (q >= 0) { const cx = m.l + bw * q; svg.append(mk('line', { x1: cx, x2: cx, y1: m.t, y2: m.t + ih, stroke: '#c62828', 'stroke-dasharray': '4 3' })); svg.append(mk('text', { x: cx + 3, y: m.t + 10, 'font-size': 9, fill: '#c62828' }, 'quiebre')); }
  return { svg, q };
}
async function crecimiento() {
  const v = $('varCrec').value; const dest = $('resCrecim'); dest.innerHTML = ''; const prog = el('p', { className: 'hint', textContent: 'Calculando…' }); dest.append(prog);
  try {
    const f = []; for (const x of VARS[v].vals) { prog.textContent = `Calculando… ${VARS[v].etq.toLowerCase()} = ${x.toLocaleString('es')}`; const r = await api.simulate(peticion({ params: { ...S.params, [v]: x }, sinMuestras: true })); const s = sist(r); f.push({ x, prom: r.ciclo.prom, p95: r.ciclo.p95, cola: s.colaMax, sat: s.saturado }); }
    prog.remove(); const { svg, q } = grafico(f, v); dest.append(svg);
    dest.append(el('p', { className: 'hint', textContent: q > 0 ? `Punto de quiebre: con ${VARS[v].etq.toLowerCase()} = ${f[q].x.toLocaleString('es')} el tiempo medio por caso pasa de ${hm(f[0].prom)} a ${hm(f[q].prom)} y el recurso de referencia queda al límite el ${(f[q].sat * 100).toFixed(0)} % del tiempo.` : 'Sin punto de quiebre en este rango: el sistema aguanta toda la prueba con la capacidad actual.' }));
    dest.append(tabla([VARS[v].etq.split(' ')[0], 'Medio/caso', 'p95', 'Cola máx.', 'Al límite'], f.map((x, i) => ({ c: [x.x.toLocaleString('es'), hm(x.prom), hm(x.p95), String(x.cola), (x.sat * 100).toFixed(0) + ' %'], cls: i === q ? 'peor' : '' }))));
  } catch (e) { prog.textContent = 'No se pudo calcular: ' + e.message; }
}

// análisis con PM4Py: el registro de eventos (con el contrato de trazabilidad) se compara con el BPMN
async function analizar() {
  const dest = $('resAnalisis'); dest.innerHTML = ''; dest.append(el('p', { className: 'hint', textContent: 'Analizando con PM4Py (la primera vez tarda unos segundos)…' }));
  try {
    const a = await api.analysis(peticion({ xml: S.xmlUsuario || XML_PLANO })); dest.innerHTML = '';
    const ok = a.conformidad.porcentaje_ajustan >= 100;
    dest.append(el('div', { className: 'card ' + (ok ? 'ok' : 'alto') }, el('b', { textContent: ok ? 'El registro cumple el BPMN' : 'El registro se desvía del BPMN' }),
      el('p', { textContent: `Conformidad (token replay): fitness ${a.conformidad.fitness.toFixed(4)} · ${a.conformidad.porcentaje_ajustan.toFixed(1)} % de las ${a.casos} trazas encajan · ${a.eventos} eventos · ${a.actividades} actividades.` })));
    if (a.fuera_del_modelo.length) dest.append(el('p', { className: 'hint', textContent: 'Actividades del registro que no están en el BPMN: ' + a.fuera_del_modelo.join(', ') }));
    if (a.sin_registro.length) dest.append(el('p', { className: 'hint', textContent: 'Actividades del BPMN que no aparecen en el registro (caminos que no se ejercitaron): ' + a.sin_registro.join(', ') }));
    dest.append(el('h2', { textContent: 'Cuellos de botella según el registro', style: 'margin-top:12px' }));
    if (!a.cuellos.length) dest.append(el('p', { className: 'hint', textContent: 'El registro no muestra esperas: ningún paso tuvo que hacer cola con esta capacidad y esta carga.' }));
    else dest.append(tabla(['Paso', 'Espera total', 'Espera prom.', 'Veces'], a.cuellos.map(c => ({ c: [S.model.els[c.actividad]?.name || c.actividad, hm(c.espera_total), fmt(c.espera_prom, 's'), String(c.veces)] }))));
  } catch (e) { dest.innerHTML = ''; dest.append(el('p', { className: 'hint', textContent: 'No se pudo analizar: ' + e.message })); }
}
async function exportarXes() {
  try { descargar(await api.exportXes(peticion({ xml: S.xmlUsuario || XML_PLANO })), 'registro_eventos.xes', 'application/xml'); } catch (e) { aviso('No se pudo exportar: ' + e.message); }
}

// ---------- archivos: .bpmn y escenario ----------
const descargar = (txt, nombre, tipo) => { const a = el('a', { href: URL.createObjectURL(new Blob([txt], { type: tipo })), download: nombre }); a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 2000); };
$('btnBpmn').onclick = () => descargar(S.xml, S.xmlUsuario ? 'importado.bpmn' : `${MODELO}${S.vista === 'plana' ? '' : '_subprocesos'}.bpmn`, 'application/xml');
$('fileBpmn').onchange = async e => {
  const f = e.target.files[0]; if (!f) return; e.target.value = '';
  try { const txt = await f.text(); if (!/BPMNDiagram/.test(txt)) throw new Error('el archivo no trae el dibujo del diagrama; ábrelo en Camunda Modeler y guárdalo de nuevo'); await parseModel(txt);
    S.xmlUsuario = txt; await abrir('plana'); const sin = Object.values(S.model.els).filter(x => /Task|Gateway/.test(x.type) && !S.sc.elementos[x.id]).length;
    aviso(sin ? `Importado. ${sin} pasos no tienen tiempos en el escenario: se simulan instantáneos hasta que se los asignes (clic en el paso).` : 'Importado. Todos los pasos tienen datos en el escenario.', 9000);
  } catch (x) { alert('No pude importar el .bpmn: ' + x.message); }
};
$('btnEscExport').onclick = () => { const o = clone(S.sc); for (const [k, v] of Object.entries(S.params)) o.params[k].valor = v; descargar(JSON.stringify(o, null, 2), `escenario_${MODELO}.json`, 'application/json'); };
$('fileEsc').onchange = async e => { const f = e.target.files[0]; if (!f) return; e.target.value = ''; try { S.base = JSON.parse(await f.text()); localStorage.removeItem(KEY); S.sc = null; await abrir(); } catch (x) { alert('No pude leer el escenario: ' + x.message); } };
$('btnReset').onclick = () => { localStorage.removeItem(KEY); S.sc = null; S.xmlUsuario = null; S.base = BASE; S.forzar = {}; S.modo = 'azar'; S.perfil = 'uniforme'; S.semilla = 7; abrir('plana'); };

// ---------- partes del proyecto (workspace.json → partes): se elige qué simular ----------
function pintarPartes(p) {
  const sel = $('parte'); if (!p.partes?.length) return;
  sel.innerHTML = ''; sel.append(el('option', { value: '', textContent: 'Simular: todo el proceso' }), ...p.partes.map(x => el('option', { value: x.id, textContent: 'Simular: ' + x.nombre })));
  sel.value = p.parte || ''; sel.hidden = false;
  sel.onchange = () => { location.search = sel.value ? '?parte=' + encodeURIComponent(sel.value) : ''; };
}

// ---------- arranque (con enlaces directos para pruebas) ----------
const q = new URLSearchParams(location.search);
(async function iniciar() {
  try { const h = await api.health(); const p = await api.project(q.get('parte')); pintarPartes(p); XML_PLANO = p.modelos.plana; XML_JER = p.modelos.subprocesos; BASE = p.escenario; CARRILES = p.carriles || {}; S.base = BASE; MODELO = p.modelo; UI = p.ui || {}; KEY = 'simv2:' + MODELO + (p.parte ? ':' + p.parte : ''); document.title = `${p.nombre} · Simulador de procesos`; $('motor').textContent = `Motor: Python · SimPy ${h.versiones.simpy} · SpiffWorkflow ${h.versiones.SpiffWorkflow}`; }
  catch (e) { document.body.innerHTML = `<div style="padding:40px;font:15px system-ui;max-width:640px"><h2>No hay conexión con el motor del simulador</h2><p>${e.message}</p><p>Inícialo con <code>sim-template/run.sh</code> y abre <code>http://127.0.0.1:8099</code> (no abras el archivo index.html directamente).</p></div>`; return; }
  await abrir((q.get('vista') || (UI.vista === 'subprocesos' ? 'sub' : '')) === 'sub' ? 'subprocesos' : 'plana');
  for (const [k, v] of q) if (k in S.sc.params) S.params[k] = Number(v);
  if (q.get('modo')) S.modo = q.get('modo'); if (q.get('perfil')) S.perfil = q.get('perfil'); if (q.get('semilla')) S.semilla = Number(q.get('semilla'));
  if (q.get('metrica')) { S.metrica = q.get('metrica'); $('metrica').value = S.metrica; }
  pintarParams(); pintarControles(); await simular();
  if (q.get('vivo')) { await iniciarVivo(); if (q.get('inyectar')) await api.liveInject(S.live.id, Number(q.get('inyectar')), 2); const t = Number(q.get('t') || 0); S.clock = t; const r = await api.liveAdvance(S.live.id, t, true); S.movs.length = 0; aplicarVivo(r, performance.now(), true); pintarCriticos(true); pintarReloj(); }
  else if (q.get('t')) { S.clock = Number(q.get('t')); actualizarVivo(true); pintarReloj(); }
  if (q.get('ir')) ir(q.get('ir'));
  if (q.get('tab')) mostrarTab(q.get('tab'));
  if (q.get('correr') === 'comparar') await comparar(); if (q.get('correr') === 'crecimiento') { if (q.get('var')) $('varCrec').value = q.get('var'); await crecimiento(); }
  if (q.get('correr') === 'analisis') await analizar();
  document.body.dataset.listo = '1';
})();
window.__sim = { S, viewer };
