import json
import os
import shutil
import sys
import tempfile
import threading
import time
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

    def test_informe_se_reemplaza(self):
        path = os.path.join(self.tmp, "reports", "ultimo_resultado.json")

        def wait_for(seed):
            for _ in range(600):
                if os.path.exists(path):
                    with open(path, encoding="utf-8") as fh:
                        data = json.load(fh)
                    if data["condiciones"]["semilla"] == seed and data["repeticiones"]:
                        return data
                time.sleep(0.1)
            self.fail("no se completó el informe")

        for seed in (11, 12):
            self.assertEqual(self.call("/api/simulate", self.sim_body(semilla=seed, parte="Una parte"))[0], 200)
            data = wait_for(seed)
        self.assertEqual([f for f in os.listdir(os.path.dirname(path)) if f.startswith("ultimo")], ["ultimo_resultado.json"])
        self.assertEqual((data["parte_simulada"], data["repeticiones"]["corridas"]), ("Una parte", 30))
        self.assertTrue(data["corrida"]["pasos_por_tiempo"] and data["corrida"]["decisiones"] and data["repeticiones"]["caminos"])
        self.call("/api/simulate", self.sim_body(semilla=99, sinMuestras=True))          # las comparaciones no lo tocan
        with open(path, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["condiciones"]["semilla"], 12)

    def test_escenarios_aleatorios_no_tocan_lo_real(self):
        sc = json.loads(json.dumps(self.sc))
        first, *rest = sc["params"]
        sc["params"][first]["origen"] = "real"
        code, out = self.call("/api/explore", self.sim_body(escenario=sc, cuantos=12, meta=10 ** 9))
        self.assertEqual((code, out["escenarios"], out["meta"]["porcentaje"]), (200, 12, 100.0))
        self.assertIn(sc["params"][first]["etiqueta"], out["fijos"])
        for row in out["mejores"] + out["peores"]:
            self.assertNotIn(first, row["params"])
            for k, v in row["params"].items():
                self.assertEqual(sc["params"][k]["origen"], "supuesto")
                self.assertTrue(sc["params"][k].get("min", v) <= v <= sc["params"][k].get("max", v), (k, v))
        self.assertTrue(out["duracion"]["minimo"] <= out["duracion"]["maximo"])
        with open(os.path.join(self.tmp, "reports", "exploracion.json"), encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["escenarios"], 12)

    def test_escenarios_guardados(self):
        body = self.sim_body(nombre="Evento 28/10: se alargó", nota="prueba", parte_id=None)
        code, first = self.call("/api/saved/save", body)
        self.assertEqual(code, 200, first)
        self.assertRegex(first["id"], r"^\d{8}-\d{6}-evento-28-10-se-alargo$")
        code, out = self.call("/api/saved/list", {})
        self.assertIn(first["id"], [x["id"] for x in out["escenarios"]])
        code, again = self.call("/api/saved/load", {"id": first["id"]})
        self.assertEqual((again["nota"], again["params"]), ("prueba", first["params"]))
        code, same = self.call("/api/saved/compare", self.sim_body(id=first["id"], parte_id=None))
        self.assertEqual((same["antes"], same["valores_cambiados"], same["pasos_cambiados"]), (same["ahora"], [], []))
        code, other = self.call("/api/saved/compare", self.sim_body(id=first["id"], parte_id=None, params={"K": 1, "RONDAS": 2}))
        self.assertTrue(other["valores_cambiados"])
        self.assertEqual(self.call("/api/saved/compare", self.sim_body(id=first["id"], parte_id="otra"))[0], 400)
        self.assertEqual(self.call("/api/saved/load", {"id": "../../workspace"})[0], 404)
        self.assertEqual(self.call("/api/saved/save", self.sim_body(nombre="  "))[0], 400)

    def test_planeado_lo_real_y_eliminar(self):
        code, plan = self.call("/api/saved/save", self.sim_body(nombre="por venir", tipo="planeado", fecha_evento="2027-01-15", parte_id=None))
        self.assertEqual((code, plan["tipo"], plan["fecha_evento"], plan["real"]), (200, "planeado", "2027-01-15", None))
        self.assertEqual(self.call("/api/saved/real", {"id": plan["id"], "minutos": 0})[0], 400)
        self.assertEqual(self.call("/api/saved/real", {"id": plan["id"], "minutos": 95, "nota": "n"})[0], 200)
        row = next(x for x in self.call("/api/saved/list", {})[1]["escenarios"] if x["id"] == plan["id"])
        self.assertEqual((row["tipo"], row["real"]["duracion_min"]), ("planeado", 95.0))
        self.assertEqual(self.call("/api/saved/delete", {"id": "../workspace"})[0], 404)
        self.assertEqual(self.call("/api/saved/delete", {"id": plan["id"]})[0], 200)
        self.assertNotIn(plan["id"], [x["id"] for x in self.call("/api/saved/list", {})[1]["escenarios"]])
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "escenarios_guardados", "eliminados", plan["id"] + ".json")))

    def test_los_eliminados_se_borran_a_los_30_dias(self):
        ids = [self.call("/api/saved/save", self.sim_body(nombre=n, parte_id=None))[1]["id"] for n in ("viejo", "reciente")]
        trash = os.path.join(self.tmp, "escenarios_guardados", "eliminados")
        original = os.path.join(self.tmp, "escenarios_guardados", ids[0] + ".json")
        os.utime(original, (1, 1))                      # guardado hace años: cuenta la fecha en que se elimina, no la de creación
        for i in ids:
            self.assertEqual(self.call("/api/saved/delete", {"id": i})[0], 200)
        self.assertTrue(os.path.exists(os.path.join(trash, ids[0] + ".json")))
        old = time.time() - 31 * 86400
        os.utime(os.path.join(trash, ids[0] + ".json"), (old, old))
        self.call("/api/saved/list", {})
        self.assertEqual([os.path.exists(os.path.join(trash, i + ".json")) for i in ids], [False, True])

    def test_otra_pagina_no_puede_escribir(self):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/api/saved/list", data=b"{}", headers={"Origin": "http://ejemplo.invalid"})
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 403)

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
