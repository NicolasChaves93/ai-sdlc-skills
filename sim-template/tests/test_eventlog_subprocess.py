import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))
from simengine import Scenario, Simulation, eventlog, prepare  # noqa: E402

NS = 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"'


def flow(i, a, b):
    return f'<bpmn:sequenceFlow id="{i}" sourceRef="{a}" targetRef="{b}"/>'


# subproceso dentro de subproceso, y el interno con dos finales distintos
XML = (f'<bpmn:definitions {NS} id="d" targetNamespace="x"><bpmn:process id="p" isExecutable="false">'
       '<bpmn:startEvent id="s"/><bpmn:subProcess id="Outer">'
       '<bpmn:startEvent id="os"/><bpmn:subProcess id="Inner">'
       '<bpmn:startEvent id="is"/><bpmn:userTask id="A"/><bpmn:exclusiveGateway id="g"/><bpmn:userTask id="B"/><bpmn:endEvent id="e1"/><bpmn:endEvent id="e2"/>'
       + flow("i1", "is", "A") + flow("i2", "A", "g") + flow("i3", "g", "B") + flow("i4", "g", "e2") + flow("i5", "B", "e1") +
       '</bpmn:subProcess><bpmn:userTask id="C"/><bpmn:endEvent id="oe"/>'
       + flow("o1", "os", "Inner") + flow("o2", "Inner", "C") + flow("o3", "C", "oe") +
       '</bpmn:subProcess><bpmn:endEvent id="e"/>' + flow("f1", "s", "Outer") + flow("f2", "Outer", "e") +
       '</bpmn:process></bpmn:definitions>')
SC = {"params": {"K": {"valor": 20}}, "raiz": {"instancias": "K", "llegadas": {"tipo": "uniforme", "min": 0, "max": 100}, "ventana": "100"},
      "recursos": {}, "elementos": {t: {"dur": {"tipo": "const", "valor": 1}} for t in "ABC"} | {"g": {"prob": {"i3": 0.5}}}}


class Subprocesses(unittest.TestCase):
    def test_analysis_with_nested_subprocesses(self):
        sim = Simulation(prepare(XML), Scenario(SC, {}), seed=3).run()
        out = eventlog.analyze(sim.log, XML)
        self.assertEqual(out["casos"], 20)
        self.assertEqual(out["conformidad"]["porcentaje_ajustan"], 100.0)
        self.assertEqual((out["fuera_del_modelo"], out["sin_registro"]), ([], []))


if __name__ == "__main__":
    unittest.main()
