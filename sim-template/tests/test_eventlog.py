import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))
from simengine import Simulation, prepare  # noqa: E402
from simengine import eventlog  # noqa: E402

F = os.path.join(os.path.dirname(__file__), "fixtures")
with open(os.path.join(F, "sorteo_flat.bpmn"), encoding="utf-8") as fh:
    FLAT = fh.read()
with open(os.path.join(F, "sorteo.json"), encoding="utf-8") as fh:
    SC = json.load(fh)
P = {"K": 20, "RONDAS": 3, "P_INVALIDA": 0.5, "P_MOD": 0.7, "P_RECHAZO": 0.4, "P_NOALCANZA": 0.3, "CAP": 1, "B": 20000}


class EventLog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim = Simulation(prepare(FLAT), SC, P, seed=11, record_samples=False).run()

    def test_xes_roundtrip(self):
        _, pm = eventlog._pm4py()
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "x.xes")
            with open(path, "wb") as fh:
                fh.write(eventlog.to_xes(self.sim.log))
            back = pm.read_xes(path)
        self.assertEqual(back[eventlog.CASE].nunique(), 20)
        self.assertEqual(len(back), len(self.sim.log) * 3)

    def test_conformance_is_perfect_and_detects_tampering(self):
        a = eventlog.analyze(self.sim.log, FLAT)
        self.assertAlmostEqual(a["conformidad"]["fitness"], 1.0, places=4)
        self.assertEqual(a["conformidad"]["porcentaje_ajustan"], 100.0)
        self.assertEqual(a["fuera_del_modelo"], [])
        bad = [dict(e) for e in self.sim.log if not (e["case"] == 0 and e["activity_id"] == "T_Cargar")]   # a un caso le falta un paso
        b = eventlog.analyze(bad, FLAT)
        self.assertLess(b["conformidad"]["porcentaje_ajustan"], 100.0)

    def test_bottlenecks_come_from_the_log(self):
        a = eventlog.analyze(self.sim.log, FLAT, top=3)
        self.assertTrue(a["cuellos"])
        sim_waits = {k: v["esperaTotal"] for k, v in self.sim.results(False)["stats"].items() if v["esperaTotal"] > 0}
        top = a["cuellos"][0]
        self.assertAlmostEqual(top["espera_total"], sim_waits[top["actividad"]], delta=0.01 * sim_waits[top["actividad"]])


if __name__ == "__main__":
    unittest.main()
