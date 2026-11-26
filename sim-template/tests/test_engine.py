import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))
from simengine import Simulation, SimulationTooLong, prepare, simulate  # noqa: E402

F = os.path.join(os.path.dirname(__file__), "fixtures")
def read(n):
    with open(os.path.join(F, n), encoding="utf-8") as fh:
        return fh.read()
FLAT, HIER = read("sorteo_flat.bpmn"), read("sorteo_hier.bpmn")
SC = json.loads(read("sorteo.json"))
REF = json.loads(read("js_reference.json"))
avg = lambda a: sum(a) / len(a)
counts = lambda r: {k: v["entradas"] for k, v in r["stats"].items()}


class Parity(unittest.TestCase):
    """Mismos resultados que el prototipo JavaScript (criterios S2 y S3 del ADR-001)."""

    def test_best_and_worst_case_counts_are_identical(self):
        for mode in ("mejor", "peor"):
            ref = REF["s2"][mode]
            r = simulate(FLAT, SC, ref["params"], mode=mode, with_samples=False)
            got = counts(r)
            for k, v in ref["conteos"].items():
                self.assertEqual(got.get(k, 0), v, f"{mode} {k}")
            self.assertEqual(r["ciclo"]["n"], ref["params"]["K"])

    def test_capacity_close_to_reference(self):
        for name in ("estres", "tipico"):
            ref = REF["s3"][name]
            rs = [simulate(FLAT, SC, ref["params"], seed=100 + i, with_samples=False) for i in range(ref["semillas"])]
            cycle = avg([r["ciclo"]["prom"] for r in rs])
            self.assertLess(abs(cycle - ref["ciclo_prom"]) / ref["ciclo_prom"], 0.15, name)
            sat = avg([r["recursos"]["sistema"]["saturado"] for r in rs])
            self.assertLess(abs(sat - ref["saturado"]) * 100, 10, name)

    def test_hierarchical_diagram_behaves_like_flat(self):
        for mode in ("mejor", "peor"):
            a = counts(simulate(FLAT, SC, {"K": 2, "RONDAS": 3}, mode=mode, with_samples=False))
            b = counts(simulate(HIER, SC, {"K": 2, "RONDAS": 3}, mode=mode, with_samples=False))
            for k in ("T_Corregir", "T_Rechazar", "T_Ajustar", "T_Seleccionar", "T_Operar", "G_Valida"):
                self.assertEqual(a.get(k, 0), b.get(k, 0), f"{mode} {k}")


class Behaviour(unittest.TestCase):
    def test_every_case_finishes_and_rounds_match(self):
        r = simulate(FLAT, SC, {"K": 4, "RONDAS": 3, "P_INVALIDA": 0, "P_NOALCANZA": 0, "P_MOD": 0, "P_RECHAZO": 0}, with_samples=False)
        self.assertEqual(r["ciclo"]["n"], 4)
        self.assertEqual(r["stats"]["T_Seleccionar"]["entradas"], 12)

    def test_arrival_profiles(self):
        p = {"K": 20, "B": 30000, "CAP": 2, "VENTANA": 3600}
        peak = simulate(FLAT, SC, p, profile="pico", with_samples=False)
        even = simulate(FLAT, SC, p, profile="uniforme", with_samples=False)
        self.assertGreater(peak["recursos"]["sistema"]["colaMax"], even["recursos"]["sistema"]["colaMax"])
        a = simulate(FLAT, SC, p, profile="poisson", seed=5, with_samples=False)
        b = simulate(FLAT, SC, p, profile="poisson", seed=5, with_samples=False)
        c = simulate(FLAT, SC, p, profile="poisson", seed=6, with_samples=False)
        self.assertEqual(a["duracion"], b["duracion"])
        self.assertNotEqual(a["duracion"], c["duracion"])
        for prof in ("rampa", "pico", "uniforme", "poisson"):
            self.assertEqual(simulate(FLAT, SC, p, profile=prof, with_samples=False)["ciclo"]["n"], 20)

    def test_results_shape(self):
        r = simulate(FLAT, SC, {"K": 3})
        for k in ("params", "duracion", "stats", "flowCount", "recursos", "samples", "log", "ciclo"):
            self.assertIn(k, r)
        s = r["stats"]["T_Seleccionar"]
        for k in ("entradas", "completadas", "esperaProm", "esperaP95", "esperaMax", "esperaTotal", "servicioProm", "servicioP95", "colaMax"):
            self.assertIn(k, s)
        self.assertEqual(set(r["recursos"]["sistema"]), {"id", "nombre", "capacidad", "utilizacion", "saturado", "colaMax"})
        self.assertTrue(r["samples"] and r["log"])
        self.assertTrue(all(len(m) == 3 and m[1] in r["flowCount"] for m in r["log"]))
        self.assertLessEqual(r["recursos"]["sistema"]["utilizacion"], 1.0001)

    def test_hierarchical_stats_include_subprocesses(self):
        r = simulate(HIER, SC, {"K": 3, "RONDAS": 2})
        self.assertEqual(r["stats"]["SP_Ronda"]["entradas"], 3 * 2)
        self.assertGreater(r["stats"]["SP_Ronda"]["servicioProm"], 0)
        self.assertEqual(r["stats"]["SP_Prep"]["entradas"], 3)

    def test_forced_loop_is_detected(self):
        with self.assertRaises(SimulationTooLong):
            simulate(FLAT, SC, {"K": 1}, forced={"G_Valida": "F_val_no"}, with_samples=False, max_case_steps=3000)


    def test_long_case_beyond_spiffworkflow_default_depth(self):
        # un caso legítimo con más de 1000 tareas no debe truncarse en silencio (SpiffWorkflow limita la profundidad a 1000 por defecto)
        r = simulate(FLAT, SC, {"K": 1, "RONDAS": 120, "P_INVALIDA": 0, "P_NOALCANZA": 0, "P_MOD": 0, "P_RECHAZO": 0}, with_samples=False, max_case_steps=20000)
        self.assertEqual(r["stats"]["T_Seleccionar"]["entradas"], 120)
        self.assertEqual(r["stats"]["End_Sorteo"]["entradas"], 1)


class Live(unittest.TestCase):
    P = {"K": 2, "RONDAS": 2, "P_INVALIDA": 0, "P_NOALCANZA": 0, "P_MOD": 0, "P_RECHAZO": 0}

    def test_chunked_advance_equals_batch(self):
        whole = simulate(FLAT, SC, self.P, with_samples=False)
        sim = Simulation(prepare(FLAT), SC, self.P, record_samples=False)
        sim.start()
        for t in range(0, 20000, 137):
            sim.advance(t)
        r = sim.results(False)
        self.assertEqual(r["ciclo"]["n"], whole["ciclo"]["n"])
        self.assertAlmostEqual(r["ciclo"]["prom"], whole["ciclo"]["prom"], places=6)

    def test_inject_and_force_and_snapshot(self):
        sim = Simulation(prepare(FLAT), SC, self.P, record_samples=False)
        sim.start()
        sim.advance(100)
        self.assertTrue(sim.snapshot() or sim.active)
        sim.inject(3)
        sim.advance(1e9)
        self.assertEqual(sim.results(False)["ciclo"]["n"], 5)
        self.assertEqual(sim.active, 0)
        f = Simulation(prepare(FLAT), SC, self.P, record_samples=False)
        f.force("G_Mod", "F_mod_si")
        f.run()
        self.assertEqual(f.results(False)["stats"]["T_Operar"]["entradas"], 2 * 2)
        self.assertTrue(f.drain_moves())


class Clock(unittest.TestCase):
    """Reloj simulado para temporizadores (S4): el temporizador no dispara antes y sí después."""

    def test_timer_uses_simulated_clock(self):
        from SpiffWorkflow.bpmn import BpmnWorkflow
        from SpiffWorkflow.bpmn.parser import BpmnParser
        from SpiffWorkflow.util.task import TaskState
        from simengine import vclock
        vclock.install()
        p = BpmnParser()
        p.add_bpmn_str(read("timer.bpmn").encode())
        spec = p.get_spec("Process_Timer")
        vclock.Clock.seconds = 0.0
        wf = BpmnWorkflow(spec)
        wf.do_engine_steps()
        wf.refresh_timers()
        vclock.Clock.seconds = 29.9
        wf.refresh_timers()
        self.assertIn("B_Tiempo", [t.task_spec.bpmn_id for t in wf.get_tasks(state=TaskState.WAITING)])
        vclock.Clock.seconds = 30.0 + vclock.fire_epsilon * 2
        wf.refresh_timers()
        wf.do_engine_steps()
        self.assertIn("T_Vencio", [t.task_spec.bpmn_id for t in wf.get_tasks(state=TaskState.READY)])


if __name__ == "__main__":
    unittest.main()
