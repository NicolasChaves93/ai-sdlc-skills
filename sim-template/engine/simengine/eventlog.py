"""Registro de eventos con el contrato de trazabilidad (ADR-001) y análisis con PM4Py.

Contrato: por cada paso, `case_id`, `activity_id` (= ID del elemento del BPMN), `lifecycle` (schedule/start/complete),
`timestamp` y `resource`. PM4Py es AGPL: uso interno; se importa solo al analizar (tarda unos segundos la primera vez).
"""
import os
import tempfile
import warnings
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)
CASE, ACT, TS, LC, RES = "case:concept:name", "concept:name", "time:timestamp", "lifecycle:transition", "org:resource"
BPMN = "{http://www.omg.org/spec/BPMN/20100524/MODEL}"


def _pm4py():
    os.environ.setdefault("PM4PY_SHOW_PROGRESS_BAR", "False")
    warnings.filterwarnings("ignore")
    import pandas as pd
    import pm4py
    return pd, pm4py


def frame(log):
    """DataFrame de eventos (tres por actividad: schedule, start, complete), en el orden en que ocurrieron en cada caso."""
    pd, _ = _pm4py()
    rows = [{CASE: f"caso-{e['case']}", ACT: e["activity_id"], LC: stage, TS: BASE + timedelta(seconds=e[stage]), RES: e["resource"] or "persona"}
            for e in log for stage in ("schedule", "start", "complete")]
    return pd.DataFrame(rows).sort_values([CASE, TS], kind="stable").reset_index(drop=True)


def to_xes(log):
    """Registro en formato XES (bytes)."""
    _, pm = _pm4py()
    df = pm.format_dataframe(frame(log), case_id=CASE, activity_key=ACT, timestamp_key=TS)
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "log.xes")
        pm.write_xes(df, path)
        return open(path, "rb").read()


def id_labelled_copy(xml):
    """Copia del BPMN con el ID como etiqueta de cada tarea, para que modelo y registro hablen el mismo idioma."""
    root = ET.fromstring(xml.encode("utf-8") if isinstance(xml, str) else xml)
    for tag in ("userTask", "serviceTask", "manualTask", "task"):
        for e in root.iter(BPMN + tag):
            e.set("name", e.get("id"))
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def analyze(log, flat_xml, top=5):
    """Conformidad contra el BPMN (token replay) y cuellos de botella leídos del registro. `flat_xml`: BPMN sin subprocesos."""
    pd, pm = _pm4py()
    df = frame(log)
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "model.bpmn")
        open(path, "wb").write(id_labelled_copy(flat_xml))
        net, im, fm = pm.convert_to_petri_net(pm.read_bpmn(path))
    comp = df[df[LC] == "complete"]
    fit = pm.fitness_token_based_replay(comp, net, im, fm, activity_key=ACT, case_id_key=CASE, timestamp_key=TS)
    waits, pending = {}, {}
    for _, f in df.iterrows():
        k = (f[CASE], f[ACT])
        if f[LC] == "schedule":
            pending[k] = f[TS]
        elif f[LC] == "start":
            waits.setdefault(f[ACT], []).append((f[TS] - pending.pop(k)).total_seconds())
    bottlenecks = sorted(({"actividad": a, "espera_total": sum(w), "espera_prom": sum(w) / len(w), "veces": len(w)} for a, w in waits.items() if sum(w) > 0),
                         key=lambda x: -x["espera_total"])[:top]
    labels = {t.label for t in net.transitions if t.label}
    return {"casos": int(df[CASE].nunique()), "eventos": int(len(df)), "actividades": int(df[ACT].nunique()),
            "conformidad": {"fitness": float(fit["log_fitness"]), "porcentaje_ajustan": float(fit["percentage_of_fitting_traces"])},
            "cuellos": bottlenecks, "sin_registro": sorted(labels - set(df[ACT])), "fuera_del_modelo": sorted(set(df[ACT]) - labels)}
