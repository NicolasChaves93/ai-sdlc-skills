"""Servidor local del simulador: sirve la interfaz web y expone el motor (simengine) por HTTP/JSON.

Solo biblioteca estándar. Escucha únicamente en 127.0.0.1, sin CORS abierto y validando la cabecera Host: ninguna página web
externa puede leer el proyecto ni lanzar simulaciones. Las simulaciones se ejecutan de una en una (candado global: el reloj
simulado de los temporizadores de SpiffWorkflow es global).

Uso: python server/server.py --workspace <espacio-de-trabajo> [--port 8099]
"""
import argparse
import json
import mimetypes
import os
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))
from simengine import Scenario, Simulation, SimulationTooLong, prepare  # noqa: E402

LOCK = threading.RLock()
SESSIONS = {}        # id -> {"sim": Simulation, "t": último uso}
MAX_BODY = 8 * 1024 * 1024
MAX_SESSIONS = 8


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class Workspace:
    """Carpeta de un proyecto: workspace.json, scenarios/ y build/ (generado por las herramientas del visor)."""

    def __init__(self, root):
        self.root = os.path.abspath(root)
        cfg = json.loads(_read(os.path.join(self.root, "workspace.json")))
        self.cfg = cfg

    def project(self):
        m, b = self.cfg["model"], os.path.join(self.root, "build")
        lanes = os.path.join(b, f"{m}_lanes.json")
        return {"nombre": self.cfg.get("name", m), "escenario": json.loads(_read(os.path.join(self.root, self.cfg["scenario"]))),
                "modelos": {"plana": _read(os.path.join(b, f"{m}_flat.bpmn")), "subprocesos": _read(os.path.join(b, f"{m}_hier.bpmn"))},
                "carriles": json.loads(_read(lanes)) if os.path.exists(lanes) else {},
                "modelo": m, "ui": self.cfg.get("ui", {})}


def _build_sim(body, live=False, on_move=None):
    xml, esc = body.get("xml"), body.get("escenario")
    if not isinstance(xml, str) or not isinstance(esc, dict):
        raise ValueError("faltan 'xml' (BPMN) o 'escenario'")
    params = body.get("params") or {}
    if not all(isinstance(v, (int, float)) for v in params.values()):
        raise ValueError("'params' debe contener solo números")
    return Simulation(prepare(xml), Scenario(esc, params), mode=body.get("modo") or "azar", profile=body.get("perfil"), seed=int(body.get("semilla", 7)),
                      forced=body.get("forzar") or {}, record_samples=not live and not body.get("sinMuestras"), on_move=on_move,
                      max_case_steps=int(body.get("maxPasosCaso", 5000)))


def api_simulate(body, ws):
    with LOCK:
        return _build_sim(body).run().results(with_samples=not body.get("sinMuestras"))


def _gc():
    now = time.time()
    for k in [k for k, v in SESSIONS.items() if now - v["t"] > 1800]:
        SESSIONS.pop(k)
    while len(SESSIONS) >= MAX_SESSIONS:
        SESSIONS.pop(min(SESSIONS, key=lambda k: SESSIONS[k]["t"]))


def api_live_create(body, ws):
    with LOCK:
        _gc()
        sim = _build_sim(body, live=True)
        sim.start()
        sid = uuid.uuid4().hex[:12]
        SESSIONS[sid] = {"sim": sim, "t": time.time()}
        return {"id": sid, "t": sim.env.now}


def _session(body):
    s = SESSIONS.get(body.get("id"))
    if not s:
        raise KeyError("sesión en vivo no encontrada o vencida")
    s["t"] = time.time()
    return s["sim"]


def api_live_advance(body, ws):
    with LOCK:
        sim = _session(body)
        sim.advance(float(body["hasta"]))
        out = {"t": sim.env.now, "activos": sim.active, "pendiente": sim.pending, "snapshot": sim.snapshot(), "movs": sim.drain_moves()[:120]}
        if body.get("completo"):
            out["resultados"] = sim.results(with_samples=False)
        return out


def api_live_inject(body, ws):
    with LOCK:
        sim = _session(body)
        sim.inject(max(1, min(int(body.get("n", 1)), 500)), float(body.get("cada", 0)))
        return {"activos": sim.active}


def api_live_force(body, ws):
    with LOCK:
        _session(body).force(body["compuerta"], body.get("flujo"))
        return {"ok": True}


def api_live_close(body, ws):
    with LOCK:
        SESSIONS.pop(body.get("id"), None)
        return {"ok": True}


def api_analysis(body, ws):
    from simengine import eventlog
    with LOCK:
        sim = _build_sim({**body, "sinMuestras": True}).run()
        out = eventlog.analyze(sim.log, body["xml"])
        out["resultados"] = sim.results(with_samples=False)["ciclo"]
        return out


def api_export_xes(body, ws):
    from simengine import eventlog
    with LOCK:
        return eventlog.to_xes(_build_sim({**body, "sinMuestras": True}).run().log)


ROUTES = {"/api/simulate": api_simulate, "/api/live/create": api_live_create, "/api/live/advance": api_live_advance, "/api/live/inject": api_live_inject,
          "/api/live/force": api_live_force, "/api/live/close": api_live_close, "/api/analysis": api_analysis, "/api/export/xes": api_export_xes}


def make_handler(ws, web_dir, port):
    allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body, ctype="application/json; charset=utf-8"):
            data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _host_ok(self):
            if self.headers.get("Host", "") in allowed_hosts:
                return True
            self._send(403, {"error": "Host no permitido"})
            return False

        def do_GET(self):
            if not self._host_ok():
                return
            path = urlparse(self.path).path
            if path == "/api/health":
                import importlib.metadata as md
                return self._send(200, {"ok": True, "motor": "python", "versiones": {p: md.version(p) for p in ("simpy", "SpiffWorkflow")}})
            if path == "/api/project":
                try:
                    return self._send(200, ws.project())
                except (OSError, KeyError, ValueError) as e:
                    return self._send(500, {"error": f"el espacio de trabajo no está listo ({e}); ejecuta la preparación de modelos"})
            if path.startswith("/api/"):
                return self._send(404, {"error": "no existe"})
            rel = "index.html" if path in ("", "/") else path.lstrip("/")
            full = os.path.realpath(os.path.join(web_dir, rel))
            if not full.startswith(os.path.realpath(web_dir) + os.sep) or not os.path.isfile(full):
                return self._send(404, {"error": "no encontrado"})
            with open(full, "rb") as fh:
                self._send(200, fh.read(), mimetypes.guess_type(full)[0] or "application/octet-stream")

        def do_POST(self):
            if not self._host_ok():
                return
            fn = ROUTES.get(urlparse(self.path).path)
            if not fn:
                return self._send(404, {"error": "no existe"})
            try:
                n = int(self.headers.get("Content-Length", 0))
                if n > MAX_BODY:
                    return self._send(413, {"error": "petición demasiado grande"})
                body = json.loads(self.rfile.read(n) or b"{}")
                out = fn(body, ws)
                if isinstance(out, bytes):
                    return self._send(200, out, "application/xml; charset=utf-8")
                self._send(200, out)
            except SimulationTooLong as e:
                self._send(422, {"error": str(e), "tipo": "bucle"})
            except KeyError as e:
                self._send(404, {"error": str(e)})
            except NameError as e:   # el escenario usa un parámetro que no existe (p. ej. un escenario guardado de una versión anterior)
                self._send(400, {"error": f"el escenario usa algo que no está definido: {e}", "tipo": "escenario"})
            except (ValueError, TypeError, NotImplementedError, json.JSONDecodeError) as e:
                self._send(400, {"error": str(e)})
            except Exception as e:   # noqa: BLE001 - el servidor local no debe caerse por un modelo raro
                self._send(500, {"error": f"{type(e).__name__}: {e}"})

    return Handler


def serve(workspace, port=8099, web_dir=None):
    ws = Workspace(workspace)
    web_dir = web_dir or os.path.join(HERE, "..", "web", "dist")
    srv = ThreadingHTTPServer(("127.0.0.1", port), make_handler(ws, web_dir, port))
    return srv


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--port", type=int, default=8099)
    a = ap.parse_args()
    s = serve(a.workspace, a.port)
    print(f"Simulador en http://127.0.0.1:{a.port}  (espacio de trabajo: {a.workspace})  — Ctrl+C para salir")
    try:
        s.serve_forever()
    except KeyboardInterrupt:
        pass
