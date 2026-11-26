"""Lectura del BPMN de negocio y generación de la copia ejecutable para SpiffWorkflow."""
import xml.etree.ElementTree as ET

BPMN = "http://www.omg.org/spec/BPMN/20100524/MODEL"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
for _p, _u in [("bpmn", BPMN), ("bpmndi", "http://www.omg.org/spec/BPMN/20100524/DI"), ("dc", "http://www.omg.org/spec/DD/20100524/DC"),
               ("di", "http://www.omg.org/spec/DD/20100524/DI"), ("xsi", XSI)]:
    ET.register_namespace(_p, _u)

_SKIP = {"laneSet", "ioSpecification", "documentation", "extensionElements", "textAnnotation", "association", "dataObject", "dataObjectReference",
         "dataStoreReference", "property", "multiInstanceLoopCharacteristics", "standardLoopCharacteristics"}


def _local(el):
    return el.tag.rsplit("}", 1)[-1]


class Model:
    """Estructura del BPMN: nodos, flujos (en orden del documento) y pertenencia a subprocesos."""

    def __init__(self, xml):
        raw = xml.encode("utf-8") if isinstance(xml, str) else xml
        root = ET.fromstring(raw)
        proc = next((e for e in root.iter() if _local(e) == "process"), None)
        if proc is None:
            raise ValueError("el BPMN no tiene ningún proceso")
        self.process_id = proc.get("id")
        self.nodes, self.flows, self.outgoing, self.incoming, self.container = {}, {}, {}, {}, {}
        self.subprocesses = set()
        self._walk(proc)
        for f in self.flows.values():
            self.outgoing.setdefault(f["source"], []).append(f["id"])
            self.incoming.setdefault(f["target"], []).append(f["id"])

    def _walk(self, container):
        cid = container.get("id")
        for ch in container:
            tag = _local(ch)
            if tag == "sequenceFlow":
                self.flows[ch.get("id")] = {"id": ch.get("id"), "name": ch.get("name") or "", "source": ch.get("sourceRef"), "target": ch.get("targetRef")}
            elif tag in _SKIP or ch.get("id") is None:
                continue
            else:
                self.nodes[ch.get("id")] = {"id": ch.get("id"), "tag": tag, "name": ch.get("name") or ""}
                self.container[ch.get("id")] = cid
                if tag == "subProcess":
                    self.subprocesses.add(ch.get("id"))
                    self._walk(ch)

    def ancestors(self, node_id):
        """Subprocesos que contienen al elemento, del más interno al más externo."""
        out, cur = [], self.container.get(node_id)
        while cur in self.subprocesses:
            out.append(cur)
            cur = self.container.get(cur)
        return out


def executable_xml(xml):
    """Copia ejecutable: añade a cada camino de una compuerta exclusiva la condición `ruta_<compuerta> == '<flujo>'`.
    El BPMN de negocio no se toca; el motor decide la ruta (probabilidades del escenario) antes de ejecutar la compuerta."""
    raw = xml.encode("utf-8") if isinstance(xml, str) else xml
    root = ET.fromstring(raw)
    flows = {f.get("id"): f for f in root.iter("{%s}sequenceFlow" % BPMN)}
    out = {}
    for f in flows.values():
        out.setdefault(f.get("sourceRef"), []).append(f.get("id"))
    for g in root.iter("{%s}exclusiveGateway" % BPMN):
        gid = g.get("id")
        if len(out.get(gid, [])) < 2:
            continue
        for fid in out[gid]:
            if flows[fid].find("{%s}conditionExpression" % BPMN) is None:
                c = ET.SubElement(flows[fid], "{%s}conditionExpression" % BPMN)
                c.set("{%s}type" % XSI, "bpmn:tFormalExpression")
                c.text = f"ruta_{gid} == '{fid}'"
    for p in root.iter("{%s}process" % BPMN):
        p.set("isExecutable", "true")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)
