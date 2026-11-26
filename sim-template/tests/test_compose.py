import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

T = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(T / "engine"))
from simengine import Scenario, Simulation, prepare  # noqa: E402

NS = ('xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" '
      'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI"')


def diagram(task_tag, extra=""):
    """Inicio → paso → fin en un carril, dibujado a mano."""
    nodes = [("S", "startEvent", 200, 36, 36), ("T", task_tag, 300, 100, 80), ("E", "endEvent", 460, 36, 36)]
    shapes = "".join(f'<bpmndi:BPMNShape id="{i}_di" bpmnElement="{i}"><dc:Bounds x="{x}" y="{140 - h // 2}" width="{w}" height="{h}"/></bpmndi:BPMNShape>' for i, _, x, w, h in nodes)
    refs = "".join(f"<bpmn:flowNodeRef>{i}</bpmn:flowNodeRef>" for i, *_ in nodes)
    body = "".join(f'<bpmn:{tag} id="{i}" name="{i}"/>' for i, tag, *_ in nodes)
    return (f'<bpmn:definitions {NS} id="d" targetNamespace="x"><bpmn:collaboration id="C"><bpmn:participant id="Pool" processRef="P"/></bpmn:collaboration>'
            f'<bpmn:process id="P"><bpmn:laneSet id="LS"><bpmn:lane id="L" name="Operador">{refs}</bpmn:lane></bpmn:laneSet>{body}{extra}'
            '<bpmn:sequenceFlow id="F1" sourceRef="S" targetRef="T"/><bpmn:sequenceFlow id="F2" sourceRef="T" targetRef="E"/></bpmn:process>'
            '<bpmndi:BPMNDiagram id="D"><bpmndi:BPMNPlane id="Pl" bpmnElement="C">'
            '<bpmndi:BPMNShape id="Pool_di" bpmnElement="Pool"><dc:Bounds x="100" y="60" width="500" height="160"/></bpmndi:BPMNShape>'
            f'<bpmndi:BPMNShape id="L_di" bpmnElement="L"><dc:Bounds x="130" y="60" width="470" height="160"/></bpmndi:BPMNShape>{shapes}'
            '<bpmndi:BPMNEdge id="F1_di" bpmnElement="F1"><di:waypoint x="236" y="140"/><di:waypoint x="300" y="140"/></bpmndi:BPMNEdge>'
            "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram></bpmn:definitions>")


class Compose(unittest.TestCase):
    def workspace(self, first):
        w = Path(tempfile.mkdtemp())
        (w / "diagrams").mkdir()
        (w / "scenarios").mkdir()
        (w / "diagrams/1.0.bpmn").write_text(first)
        (w / "diagrams/1.1.bpmn").write_text(diagram("userTask"))
        (w / "scenarios/m.json").write_text(json.dumps({"params": {}, "raiz": {}, "recursos": {}, "elementos": {"B_T": {"dur": 5}}}))
        (w / "workspace.json").write_text(json.dumps({"name": "x", "model": "m", "scenario": "scenarios/m.json"}))
        (w / "compose.json").write_text(json.dumps({"source": "diagrams", "diagrams": {"A": "1.0", "B": "1.1"}, "calls": {"T": "B"},
                                                    "parts": [{"id": "uno", "prefix": "A", "subprocess": "SP_Uno", "title": "1. Uno", "lane": "Operador", "whole": True},
                                                              {"id": "dos", "prefix": "B", "subprocess": "SP_Dos", "title": "1.1 Dos", "lane": "Operador"}]}))
        return w

    def run_compose(self, w):
        return subprocess.run([sys.executable, str(T / "compose.py"), str(w)], capture_output=True, text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})

    def test_compone_conserva_dibujo_y_simula(self):
        w = self.workspace(diagram("callActivity"))
        out = self.run_compose(w)
        self.assertEqual(out.returncode, 0, out.stderr)
        sc = json.loads((w / "scenarios/m.json").read_text())
        for folder in (w, w / "partes/uno", w / "partes/dos"):
            xml = (folder / "build/m_flat.bpmn").read_text()
            self.assertEqual(Simulation(prepare(xml), Scenario(sc, {}), record_samples=False).run().results(False)["duracion"], 5, folder)
        lanes = json.loads((w / "build/m_lanes.json").read_text())
        self.assertEqual(lanes["SP_Uno"], {"lanes": [{"n": "Operador", "y": 0, "h": 160}], "w": 500})
        self.assertIn("A_T", lanes)                                  # la caja «+» conserva sus carriles
        self.assertIn('<dc:Bounds x="200" y="40" width="100" height="80"/>', xml)      # posición a mano, relativa al carril
        self.assertEqual([p["id"] for p in json.loads((w / "workspace.json").read_text())["partes"]], ["uno", "dos"])

    def test_rechaza_lo_que_no_se_puede_simular(self):
        w = self.workspace(diagram("callActivity", extra='<bpmn:boundaryEvent id="Reloj" attachedToRef="T"/>'))
        out = self.run_compose(w)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("Reloj", out.stderr)


if __name__ == "__main__":
    unittest.main()
