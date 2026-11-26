"""Recorrido completo con un flujo ajeno al sorteo, con carriles dibujados como en Camunda Modeler."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

T = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(T, "engine"))
from simengine import Simulation, prepare  # noqa: E402


@unittest.skipUnless(os.path.isdir(os.path.join(T, "web", "node_modules")), "falta npm install en web/")
class Preparar(unittest.TestCase):
    def test_ejemplo_permisos(self):
        for rol in ("Jefe", "Jefe de área"):
            with self.subTest(rol), tempfile.TemporaryDirectory() as d:
                w = os.path.join(d, "ws")
                shutil.copytree(os.path.join(T, "examples", "permisos"), w, ignore=shutil.ignore_patterns("build"))
                model = os.path.join(w, "models", "permiso.bpmn")
                with open(model, encoding="utf-8") as fh:
                    xml = fh.read().replace('name="Jefe"', f'name="{rol}"')
                with open(model, "w", encoding="utf-8") as fh:
                    fh.write(xml)
                r = subprocess.run([os.path.join(T, "prepare.sh"), w], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                with open(os.path.join(w, "build", "permiso_lanes.json"), encoding="utf-8") as fh:
                    self.assertEqual([x["n"] for x in json.load(fh)["Proc_Permiso"]["lanes"]], ["Empleado", rol, "Sistema"])
                with open(os.path.join(w, "scenarios", "permiso.json"), encoding="utf-8") as fh:
                    sc = json.load(fh)
                for name in ("flat", "hier"):
                    with open(os.path.join(w, "build", f"permiso_{name}.bpmn"), encoding="utf-8") as fh:
                        out = Simulation(prepare(fh.read()), sc).run().results(False)
                    self.assertEqual(out["ciclo"]["n"], 40)

    def test_no_descarta_en_silencio(self):
        casos = {"temporizador": ('<bpmn:endEvent id="Fin" name="Respuesta enviada"/>',
                                  '<bpmn:endEvent id="Fin" name="Respuesta enviada"/><bpmn:intermediateCatchEvent id="Espera" name="Esperar"><bpmn:timerEventDefinition/></bpmn:intermediateCatchEvent>', "Espera"),
                 "tarea de script": ('<bpmn:serviceTask id="T_Registrar" name="Registrar permiso"/>',
                                     '<bpmn:scriptTask id="T_Registrar" name="Registrar permiso"/>', "T_Registrar")}
        for caso, (old, new, ident) in casos.items():
            with self.subTest(caso), tempfile.TemporaryDirectory() as d:
                w = os.path.join(d, "ws")
                shutil.copytree(os.path.join(T, "examples", "permisos"), w, ignore=shutil.ignore_patterns("build"))
                model = os.path.join(w, "models", "permiso.bpmn")
                with open(model, encoding="utf-8") as fh:
                    xml = fh.read()
                self.assertIn(old, xml)
                with open(model, "w", encoding="utf-8") as fh:
                    fh.write(xml.replace(old, new))
                r = subprocess.run([os.path.join(T, "prepare.sh"), w], capture_output=True, text=True)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn(ident, r.stderr)
                self.assertFalse(os.path.exists(os.path.join(w, "build", "permiso_flat.bpmn")))


if __name__ == "__main__":
    unittest.main()
