"""«Buscar N aciertos» (tipo «exitos»): nunca menos de N intentos y la variación de una binomial negativa."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))
from simengine import Scenario, Simulation, prepare  # noqa: E402

NS = 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"'


def flow(i, a, b):
    return f'<bpmn:sequenceFlow id="{i}" sourceRef="{a}" targetRef="{b}"/>'


# dos vueltas de «buscar 5»: la cuenta debe reiniciarse al salir
XML = (f'<bpmn:definitions {NS} id="d" targetNamespace="x"><bpmn:process id="p"><bpmn:startEvent id="s"/><bpmn:exclusiveGateway id="r"/><bpmn:exclusiveGateway id="m"/>'
       '<bpmn:userTask id="T"/><bpmn:exclusiveGateway id="g"/><bpmn:exclusiveGateway id="more"/><bpmn:endEvent id="e"/>'
       + flow("f0", "s", "r") + flow("f1", "r", "m") + flow("f2", "m", "T") + flow("f3", "T", "g") + flow("again", "g", "m")
       + flow("done", "g", "more") + flow("next", "more", "r") + flow("end", "more", "e") + "</bpmn:process></bpmn:definitions>")


def tries(p, seed, rounds=1):
    sc = {"params": {"N": {"valor": 5}, "P": {"valor": p}, "V": {"valor": rounds}}, "raiz": {}, "recursos": {},
          "elementos": {"T": {"dur": 1}, "g": {"tipo": "exitos", "veces": "N", "prob": "P", "flujo": "again"}, "more": {"tipo": "contador", "veces": "V", "flujo": "next"}}}
    return Simulation(prepare(XML), Scenario(sc, {}), seed=seed, record_samples=False).run().results(False)["stats"]["T"]["entradas"]


class Successes(unittest.TestCase):
    def test_con_acierto_seguro_son_exactamente_n(self):
        self.assertEqual(tries(1.0, 1), 5)
        self.assertEqual(tries(1.0, 1, rounds=3), 15)

    def test_media_y_variacion(self):
        runs = [tries(0.25, s) for s in range(400)]
        mean = sum(runs) / len(runs)
        sd = (sum((x - mean) ** 2 for x in runs) / len(runs)) ** 0.5
        self.assertGreaterEqual(min(runs), 5)
        self.assertAlmostEqual(mean, 20, delta=1.2)       # N / P
        self.assertAlmostEqual(sd, 7.75, delta=1.2)       # raíz(N·(1-P)) / P


if __name__ == "__main__":
    unittest.main()
