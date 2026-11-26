#!/usr/bin/env python3
"""Arma el modelo a simular a partir de diagramas hechos a mano, conservando su dibujo (carriles, posiciones).

Cada caja «+» (call activity) se reemplaza por el diagrama que le corresponde. Lo describe `<espacio>/compose.json`:

  {"source": "models",                                  carpeta de los diagramas, relativa al espacio de trabajo
   "diagrams": {"P": "1.0_preparacion", ...},           prefijo → archivo (el prefijo encabeza los ID: P_T_Crear)
   "calls": {"Call_Operar": "O"},                       caja «+» → prefijo del diagrama que abre
   "parts": [{"id": "preparacion", "prefix": "P", "subprocess": "SP_Preparacion", "title": "1. Preparación",
              "lane": "Administrador", "whole": true}]} lo que se puede simular; «whole» entra en «todo el proceso»

Uso: python3 compose.py <espacio-de-trabajo>      (run.sh lo llama solo si existe compose.json)
"""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import quoteattr

B = "{http://www.omg.org/spec/BPMN/20100524/MODEL}"
DI = "{http://www.omg.org/spec/BPMN/20100524/DI}"
DC = "{http://www.omg.org/spec/DD/20100524/DC}"
DD = "{http://www.omg.org/spec/DD/20100524/DI}"
NOT_SUPPORTED = ("boundaryEvent", "sendTask", "receiveTask", "scriptTask", "businessRuleTask", "conditionExpression", "standardLoopCharacteristics",
                 "multiInstanceLoopCharacteristics")
HEADER = ('<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" '
          'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" xmlns:cc="http://colombiancode.co/bpmn" '
          'id="Defs" targetNamespace="http://bpmn.io/schema/bpmn">')


def num(v):
    return str(round(float(v)))


def bounds(b, dx=0.0, dy=0.0):
    return f'<dc:Bounds x="{num(float(b.get("x")) - dx)}" y="{num(float(b.get("y")) - dy)}" width="{num(b.get("width"))}" height="{num(b.get("height"))}"/>'


def label_of(element, dx=0.0, dy=0.0):
    lab = element.find(DI + "BPMNLabel")
    lab = lab.find(DC + "Bounds") if lab is not None else None
    return f"<bpmndi:BPMNLabel>{bounds(lab, dx, dy)}</bpmndi:BPMNLabel>" if lab is not None else ""


class Composer:
    def __init__(self, source, diagrams, calls):
        self.calls = calls
        self.roots = {}
        for prefix, name in diagrams.items():
            path = source / f"{name}.bpmn"
            root = ET.parse(path).getroot()
            proc = root.find(B + "process")
            bad = [e for e in proc.iter() if e.tag.split("}")[-1] in NOT_SUPPORTED or e.tag.endswith("EventDefinition")
                   or (e.tag == B + "callActivity" and e.get("id") not in calls)]
            if bad:
                raise SystemExit(f"{path.name}: el simulador no admite " + ", ".join(sorted({f'{e.tag.split("}")[-1]} {e.get("id") or ""}'.strip() for e in bad})))
            if root.find(".//" + DI + "BPMNShape") is None:
                raise SystemExit(f"{path.name}: no trae el dibujo del diagrama")
            self.roots[prefix] = root

    def content(self, prefix, ind):
        proc = self.roots[prefix].find(B + "process")
        lane = {r.text.strip(): l.get("name") for l in proc.iter(B + "lane") for r in l.findall(B + "flowNodeRef")}
        out = []
        for e in proc:
            tag, ident = e.tag.replace(B, ""), e.get("id")
            if tag == "laneSet":
                continue
            name = f' name={quoteattr(e.get("name"))}' if e.get("name") else ""
            new = f"{prefix}_{ident}"
            if tag == "sequenceFlow":
                out.append(f'{ind}<bpmn:sequenceFlow id="{new}"{name} sourceRef="{prefix}_{e.get("sourceRef")}" targetRef="{prefix}_{e.get("targetRef")}"/>')
                continue
            carril = f' cc:carril={quoteattr(lane[ident])}' if ident in lane else ""
            if tag == "callActivity":
                out.append(f'{ind}<bpmn:subProcess id="{new}"{carril}{name}>')
                out += self.content(self.calls[ident], ind + "  ")
                out.append(f"{ind}</bpmn:subProcess>")
            else:
                out.append(f"{ind}<bpmn:{tag} id=\"{new}\"{carril}{name}/>")
        return out

    def planes(self, prefix, scope, planes, lanes_geometry):
        root = self.roots[prefix]
        proc = root.find(B + "process")
        nodes = {e.get("id"): e.tag.replace(B, "") for e in proc}
        lanes = {l.get("id"): l.get("name") for l in proc.iter(B + "lane")}
        shapes = {s.get("bpmnElement"): s for s in root.iter(DI + "BPMNShape")}
        pool = next((s for k, s in shapes.items() if k not in nodes and k not in lanes), None)
        dx = dy = 0.0
        if pool is not None and lanes:                      # el carril que dibuja el visor empieza en 0,0
            box = pool.find(DC + "Bounds")
            dx, dy = float(box.get("x")), float(box.get("y"))
            rows = ({"n": n, "y": round(float(shapes[k].find(DC + "Bounds").get("y")) - dy), "h": round(float(shapes[k].find(DC + "Bounds").get("height")))} for k, n in lanes.items())
            lanes_geometry[scope] = {"lanes": sorted(rows, key=lambda x: x["y"]), "w": round(float(box.get("width")))}
        out = []
        for ident, shape in shapes.items():
            if ident not in nodes:
                continue
            extra = ' isMarkerVisible="true"' if nodes[ident] == "exclusiveGateway" else ' isExpanded="false"' if nodes[ident] in ("callActivity", "subProcess") else ""
            out.append(f'<bpmndi:BPMNShape id="{prefix}_{ident}_di" bpmnElement="{prefix}_{ident}"{extra}>{bounds(shape.find(DC + "Bounds"), dx, dy)}'
                       + label_of(shape, dx, dy) + "</bpmndi:BPMNShape>")
        for edge in root.iter(DI + "BPMNEdge"):
            ident = edge.get("bpmnElement")
            points = "".join(f'<di:waypoint x="{num(float(w.get("x")) - dx)}" y="{num(float(w.get("y")) - dy)}"/>' for w in edge.findall(DD + "waypoint"))
            out.append(f'<bpmndi:BPMNEdge id="{prefix}_{ident}_di" bpmnElement="{prefix}_{ident}">{points}' + label_of(edge, dx, dy) + "</bpmndi:BPMNEdge>")
        planes.append((scope, out))
        for ident, tag in nodes.items():
            if tag == "callActivity":
                self.planes(self.calls[ident], f"{prefix}_{ident}", planes, lanes_geometry)

    def write(self, parts, destination, model, process_id, title):
        body, ids = [], []
        for p in parts:
            body += [f'    <bpmn:subProcess id="{p["subprocess"]}" cc:carril={quoteattr(p["lane"])} name={quoteattr(p["title"])}>', *self.content(p["prefix"], "      "), "    </bpmn:subProcess>"]
            ids.append(p["subprocess"])
        chain = ["Ini", *ids, "Fin"]
        pairs = list(enumerate(zip(chain, chain[1:]), 1))
        flows = [f'    <bpmn:sequenceFlow id="G{n}" sourceRef="{a}" targetRef="{b}"/>' for n, (a, b) in pairs]
        box, x = {}, 80                                     # plano general: una fila, sin cruces
        for n in chain:
            w, h = (100, 80) if n in ids else (36, 36)
            box[n] = (x, 120 - h // 2, w, h)
            x += w + 70
        top = [f'<bpmndi:BPMNShape id="{n}_di" bpmnElement="{n}"' + (' isExpanded="false"' if n in ids else "") + f'><dc:Bounds x="{a}" y="{b}" width="{c}" height="{d}"/></bpmndi:BPMNShape>'
               for n, (a, b, c, d) in box.items()]
        top += [f'<bpmndi:BPMNEdge id="G{n}_di" bpmnElement="G{n}"><di:waypoint x="{box[a][0] + box[a][2]}" y="120"/><di:waypoint x="{box[b][0]}" y="120"/></bpmndi:BPMNEdge>' for n, (a, b) in pairs]
        planes, lanes_geometry = [], {}
        for p in parts:
            self.planes(p["prefix"], p["subprocess"], planes, lanes_geometry)
        lane = quoteattr(parts[0]["lane"])
        xml = ['<?xml version="1.0" encoding="UTF-8"?>', HEADER, f'  <bpmn:process id="{process_id}" name={quoteattr(title)} isExecutable="false">',
               f'    <bpmn:startEvent id="Ini" cc:carril={lane} name="Inicio"/>', *body, f'    <bpmn:endEvent id="Fin" cc:carril={lane} name="Fin"/>', *flows, "  </bpmn:process>"]
        for scope, shapes in [(process_id, top)] + planes:
            xml.append(f'  <bpmndi:BPMNDiagram id="Diagram_{scope}"><bpmndi:BPMNPlane id="Plane_{scope}" bpmnElement="{scope}">' + "".join(shapes) + "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram>")
        text = "\n".join(xml + ["</bpmn:definitions>", ""])
        (destination / "build").mkdir(parents=True, exist_ok=True)
        (destination / "models").mkdir(exist_ok=True)
        (destination / f"models/{model}.bpmn").write_text(text, encoding="utf-8")
        for kind in ("flat", "hier"):
            (destination / f"build/{model}_{kind}.bpmn").write_text(text, encoding="utf-8")
        (destination / f"build/{model}_lanes.json").write_text(json.dumps(lanes_geometry, ensure_ascii=False), encoding="utf-8")


def compose(workspace):
    home = Path(workspace).resolve()
    cfg = json.loads((home / "compose.json").read_text(encoding="utf-8"))
    base = json.loads((home / "workspace.json").read_text(encoding="utf-8"))
    model, title = base["model"], base.get("process_title") or base["model"]
    process_id = cfg.get("process_id") or f"Process_{model}"
    composer = Composer(home / cfg.get("source", "models"), cfg["diagrams"], cfg.get("calls", {}))
    parts = cfg["parts"]
    composer.write([p for p in parts if p.get("whole")] or parts[:1], home, model, process_id, title)
    base["partes"] = [{"id": p["id"], "nombre": p["title"], "carpeta": f"partes/{p['id']}"} for p in parts]
    base.setdefault("ui", {})["vista"] = "subprocesos"
    (home / "workspace.json").write_text(json.dumps(base, ensure_ascii=False, indent=2), encoding="utf-8")
    base.pop("partes")
    scenario = (home / base["scenario"]).read_text(encoding="utf-8")
    for p in parts:                                          # cada parte por separado, con el mismo escenario
        folder = home / "partes" / p["id"]
        composer.write([p], folder, model, process_id, title)
        (folder / base["scenario"]).parent.mkdir(parents=True, exist_ok=True)
        (folder / base["scenario"]).write_text(scenario, encoding="utf-8")
        (folder / "workspace.json").write_text(json.dumps({**base, "name": p["title"], "ui": {**base["ui"], "raiz": p["subprocess"]}}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: {len(parts)} partes compuestas desde {len(cfg['diagrams'])} diagramas")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("uso: compose.py <espacio-de-trabajo>")
    compose(sys.argv[1])
