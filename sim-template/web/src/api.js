// Cliente del servidor del simulador (motor de Python). La interfaz solo dibuja; toda simulación se pide al servidor.
async function call(method, path, body) {
  const r = await fetch(path, { method, headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
  const j = (r.headers.get('content-type') || '').includes('json') ? await r.json() : await r.text();
  if (!r.ok) { const e = new Error((j && j.error) || r.statusText); e.tipo = j && j.tipo; e.status = r.status; throw e; }
  return j;
}
export const health = () => call('GET', '/api/health');
export const project = parte => call('GET', '/api/project' + (parte ? '?parte=' + encodeURIComponent(parte) : ''));
export const simulate = b => call('POST', '/api/simulate', b);
export const liveCreate = b => call('POST', '/api/live/create', b);
export const liveAdvance = (id, hasta, completo) => call('POST', '/api/live/advance', { id, hasta, completo: !!completo });
export const liveInject = (id, n, cada) => call('POST', '/api/live/inject', { id, n, cada });
export const liveForce = (id, compuerta, flujo) => call('POST', '/api/live/force', { id, compuerta, flujo });
export const liveClose = id => call('POST', '/api/live/close', { id }).catch(() => { });
export const analysis = b => call('POST', '/api/analysis', b);
export const explore = b => call('POST', '/api/explore', b);
export const savedSave = b => call('POST', '/api/saved/save', b);
export const savedList = () => call('POST', '/api/saved/list', {});
export const savedLoad = id => call('POST', '/api/saved/load', { id });
export const savedCompare = b => call('POST', '/api/saved/compare', b);
export const exportXes = b => call('POST', '/api/export/xes', b);
