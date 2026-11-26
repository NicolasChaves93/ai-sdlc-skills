import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
import server  # noqa: E402

F = os.path.join(os.path.dirname(__file__), "fixtures")


def rd(n):
    with open(os.path.join(F, n), encoding="utf-8") as fh:
        return fh.read()


class Api(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(cls.tmp, "build"))
        os.makedirs(os.path.join(cls.tmp, "scenarios"))
        shutil.copy(os.path.join(F, "sorteo.json"), os.path.join(cls.tmp, "scenarios", "sorteo.json"))
        shutil.copy(os.path.join(F, "sorteo_flat.bpmn"), os.path.join(cls.tmp, "build", "sorteo_flat.bpmn"))
        shutil.copy(os.path.join(F, "sorteo_hier.bpmn"), os.path.join(cls.tmp, "build", "sorteo_hier.bpmn"))
        with open(os.path.join(cls.tmp, "workspace.json"), "w") as fh:
            json.dump({"name": "prueba", "model": "sorteo", "scenario": "scenarios/sorteo.json", "partes": [{"id": "una", "nombre": "Una parte", "carpeta": "partes/una"}]}, fh)
        part = os.path.join(cls.tmp, "partes", "una")
        shutil.copytree(os.path.join(cls.tmp, "build"), os.path.join(part, "build"))
        shutil.copytree(os.path.join(cls.tmp, "scenarios"), os.path.join(part, "scenarios"))
        with open(os.path.join(part, "workspace.json"), "w") as fh:
            json.dump({"name": "solo una", "model": "sorteo", "scenario": "scenarios/sorteo.json"}, fh)
        web = os.path.join(cls.tmp, "web")
        os.makedirs(web)
        with open(os.path.join(web, "index.html"), "w") as fh:
            fh.write("<html>ok</html>")
        cls.srv = server.serve(cls.tmp, 0, web)
        cls.port = cls.srv.server_address[1]
        cls.srv.RequestHandlerClass = server.make_handler(server.Workspace(cls.tmp), web, cls.port)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.xml, cls.sc = rd("sorteo_flat.bpmn"), json.loads(rd("sorteo.json"))

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def call(self, path, body=None, host=None):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=None if body is None else json.dumps(body).encode(), method="GET" if body is None else "POST",
                                     headers={"Content-Type": "application/json", "Host": host or f"127.0.0.1:{self.port}"})
        try:
            with urllib.request.urlopen(req) as r:
                raw = r.read()
                return r.status, (json.loads(raw) if "json" in r.headers["Content-Type"] else raw)
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_partes(self):
        code, whole = self.call("/api/project")
        self.assertEqual((code, whole["parte"], whole["partes"]), (200, None, [{"id": "una", "nombre": "Una parte"}]))
        code, part = self.call("/api/project?parte=una")
        self.assertEqual((code, part["nombre"], part["parte"], len(part["partes"])), (200, "solo una", "una", 1))
        for bad in ("otra", "../..", "partes/una"):
            self.assertEqual(self.call(f"/api/project?parte={bad}")[0], 500, bad)

    def sim_body(self, **kw):
        return {"xml": self.xml, "escenario": self.sc, "params": {"K": 3, "RONDAS": 2}, **kw}

    def test_health_project_and_static(self):
        code, h = self.call("/api/health")
        self.assertEqual((code, h["motor"]), (200, "python"))
        code, p = self.call("/api/project")
        self.assertEqual(code, 200)
        self.assertEqual(set(p), {"nombre", "escenario", "modelos", "carriles", "modelo", "ui", "partes", "parte"})
        self.assertIn("plana", p["modelos"])
        code, raw = self.call("/")
        self.assertEqual(code, 200)

    def test_simulate_matches_contract(self):
        code, r = self.call("/api/simulate", self.sim_body())
        self.assertEqual(code, 200)
        self.assertEqual(r["ciclo"]["n"], 3)
        self.assertIn("T_Seleccionar", r["stats"])
        self.assertTrue(r["samples"])
        code, r2 = self.call("/api/simulate", self.sim_body(sinMuestras=True))
        self.assertEqual(r2["samples"], [])

    def test_rejects_foreign_host_and_bad_input(self):
        self.assertEqual(self.call("/api/health", host="evil.example")[0], 403)
        self.assertEqual(self.call("/api/simulate", {"xml": 1})[0], 400)
        self.assertEqual(self.call("/api/simulate", self.sim_body(params={"K": "x"}))[0], 400)
        self.assertEqual(self.call("/api/nope", {})[0], 404)
        self.assertEqual(self.call("/../../etc/passwd")[0], 404)

    def test_scenario_using_an_undefined_parameter_is_a_clear_400(self):   # p. ej. un escenario guardado de una versión anterior
        import copy
        body = copy.deepcopy(self.sim_body())
        body["escenario"]["elementos"]["G_Otra"]["veces"] = "PARAMETRO_QUE_YA_NO_EXISTE"
        code, r = self.call("/api/simulate", body)
        self.assertEqual((code, r["tipo"]), (400, "escenario"))
        self.assertIn("PARAMETRO_QUE_YA_NO_EXISTE", r["error"])

    def test_forced_loop_returns_422(self):
        code, r = self.call("/api/simulate", self.sim_body(forzar={"G_Valida": "F_val_no"}, maxPasosCaso=400, sinMuestras=True))
        self.assertEqual((code, r["tipo"]), (422, "bucle"))

    def test_live_session(self):
        code, c = self.call("/api/live/create", self.sim_body(params={"K": 2, "RONDAS": 2, "P_INVALIDA": 0, "P_NOALCANZA": 0, "P_MOD": 0, "P_RECHAZO": 0}))
        self.assertEqual(code, 200)
        sid = c["id"]
        code, a = self.call("/api/live/advance", {"id": sid, "hasta": 600})
        self.assertEqual(code, 200)
        self.assertEqual(a["t"], 600)
        self.assertIn("snapshot", a)
        self.assertEqual(self.call("/api/live/inject", {"id": sid, "n": 2})[0], 200)
        self.assertEqual(self.call("/api/live/force", {"id": sid, "compuerta": "G_Mod", "flujo": "F_mod_si"})[0], 200)
        code, a = self.call("/api/live/advance", {"id": sid, "hasta": 1e7, "completo": True})
        self.assertFalse(a["pendiente"])
        self.assertEqual(a["resultados"]["ciclo"]["n"], 4)
        self.assertEqual(self.call("/api/live/close", {"id": sid})[0], 200)
        self.assertEqual(self.call("/api/live/advance", {"id": sid, "hasta": 1})[0], 404)

    def test_analysis_and_xes(self):
        code, a = self.call("/api/analysis", self.sim_body(params={"K": 6, "RONDAS": 2, "P_INVALIDA": 0.5, "P_MOD": 0.7}))
        self.assertEqual(code, 200)
        self.assertAlmostEqual(a["conformidad"]["fitness"], 1.0, places=3)
        code, x = self.call("/api/export/xes", self.sim_body())
        self.assertEqual(code, 200)
        self.assertIn(b"<log", x)


if __name__ == "__main__":
    unittest.main()
