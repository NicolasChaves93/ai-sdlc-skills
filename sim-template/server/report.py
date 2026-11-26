"""Informe de la última simulación para que una IA (u otra herramienta) proponga mejoras.

Un solo archivo por espacio de trabajo, `reports/ultimo_resultado.json`, que se reemplaza en cada corrida. Primero se escribe
la corrida que se ve en pantalla y luego, en segundo plano, se le añade el rango de varias repeticiones al azar.
"""
import json
import os
import sys
import threading
from datetime import datetime

from simengine import Model, Scenario, Simulation, prepare

REPETITIONS = 30
HOW_TO_READ = [
    "Son resultados de una simulación, no datos reales: valen lo que valgan los tiempos y probabilidades usados.",
    "Un parámetro con origen «supuesto» es una estimación; «real» es un dato medido o confirmado (mira su «fuente»); «negocio» es una regla del producto.",
    "«corrida» es una sola ejecución (la que se vio en pantalla). Para concluir usa «repeticiones», que muestra el rango.",
    "Un camino con 0 veces en una corrida puede ocurrir en otra: mira «veces_en_promedio» en «repeticiones».",
    "Un «caso» es un recorrido completo del diagrama, no una persona. Los tiempos están en segundos.",
    "Los pasos van uno tras otro dentro de un caso: más personas solo ayudan si hay varios casos esperando.",
]


def _r(x):
    return round(float(x), 2)


def _pick(values, p):
    s = sorted(values)
    return _r(s[min(len(s) - 1, int(p * len(s)))]) if s else 0.0


def build(body, results):
    """Informe legible de una corrida: usa los nombres del diagrama, no solo los IDs."""
    model, sc = Model(body["xml"]), body["escenario"]
    nodes, flows, elements = model.nodes, model.flows, sc.get("elementos", {})
    name = lambda i: nodes.get(i, {}).get("name") or i
    where = lambda i: " > ".join(name(a) for a in reversed(model.ancestors(i)))
    used = body.get("params") or {}
    params = [{"id": k, "etiqueta": d.get("etiqueta", k), "valor": used.get(k, d.get("valor")), "valor_original": d.get("valor"),
               "origen": d.get("origen"), "grupo": d.get("grupo"), "regla": d.get("br"), "fuente": d.get("nota")} for k, d in sc.get("params", {}).items()]
    tasks = [i for i, n in nodes.items() if n["tag"] in ("task", "userTask", "serviceTask", "manualTask")]
    steps = []
    for i in tasks:
        s = results["stats"].get(i)
        if not s or not s["entradas"]:
            continue
        steps.append({"id": i, "paso": name(i), "donde": where(i), "quien": elements.get(i, {}).get("recurso"), "veces": s["entradas"],
                      "duracion_promedio": _r(s["servicioProm"]), "trabajo_total": _r(s["servicioProm"] * s["completadas"]),
                      "espera_total": _r(s["esperaTotal"]), "espera_p95": _r(s["esperaP95"]), "cola_maxima": s["colaMax"], "configurado": elements.get(i, {})})
    steps.sort(key=lambda x: -(x["trabajo_total"] + x["espera_total"]))
    decisions = []
    for g, n in nodes.items():
        outs = model.outgoing.get(g, [])
        if n["tag"] != "exclusiveGateway" or len(outs) < 2:
            continue
        decisions.append({"id": g, "decision": name(g), "donde": where(g),
                          "caminos": [{"id": f, "camino": flows[f]["name"] or name(flows[f]["target"]), "veces": results["flowCount"].get(f, 0)} for f in outs]})
    return {
        "generado": datetime.now().astimezone().isoformat(timespec="seconds"),
        "como_leer": HOW_TO_READ,
        "escenario": sc.get("nombre"),
        "parte_simulada": body.get("parte") or "todo el proceso",
        "condiciones": {"flujo": body.get("modo") or "azar", "llegada_de_casos": body.get("perfil"), "semilla": body.get("semilla"),
                        "caminos_forzados": body.get("forzar") or {}, "parametros": params},
        "corrida": {
            "casos_completados": results["ciclo"]["n"], "duracion_total": _r(results["duracion"]),
            "tiempo_por_caso": {"promedio": _r(results["ciclo"]["prom"]), "p95": _r(results["ciclo"]["p95"])},
            "recursos": [{"id": r["id"], "nombre": r["nombre"], "capacidad": r["capacidad"], "uso": _r(r["utilizacion"]),
                          "al_limite": _r(r["saturado"]), "cola_maxima": r["colaMax"]} for r in results["recursos"].values()],
            "pasos_por_tiempo": steps,
            "pasos_no_recorridos": [{"id": i, "paso": name(i), "donde": where(i)} for i in tasks if not results["stats"].get(i, {}).get("entradas")],
            "decisiones": decisions,
        },
        "repeticiones": None,
    }


def repeat(body, lock, cancelled, n=REPETITIONS):
    """Rango de `n` corridas al azar con las mismas condiciones. Devuelve None si llegó una corrida más nueva."""
    spec = prepare(body["xml"])
    durations, cycles, flows, spent, waits, queues = [], [], {}, {}, {}, {}
    for i in range(n):
        if cancelled():
            return None
        with lock:
            r = Simulation(spec, Scenario(body["escenario"], body.get("params") or {}), mode=body.get("modo") or "azar", profile=body.get("perfil"),
                           seed=1000 + i, forced=body.get("forzar") or {}, record_samples=False).run().results(with_samples=False)
        durations.append(r["duracion"])
        cycles.append(r["ciclo"]["prom"])
        for k, v in r["flowCount"].items():
            flows[k] = flows.get(k, 0) + v
        for k, s in r["stats"].items():
            spent[k] = spent.get(k, 0) + s["servicioProm"] * s["completadas"] + s["esperaTotal"]
            waits[k] = waits.get(k, 0) + s["esperaTotal"]
        for k, res in r["recursos"].items():
            queues[k] = max(queues.get(k, 0), res["colaMax"])
    model = Model(body["xml"])
    name = lambda i: model.nodes.get(i, {}).get("name") or i
    tasks = [i for i, node in model.nodes.items() if node["tag"] in ("task", "userTask", "serviceTask", "manualTask")]
    rng = lambda v: {"minimo": _pick(v, 0), "mediana": _pick(v, .5), "p90": _pick(v, .9), "maximo": _pick(v, 1)}
    return {"corridas": n, "duracion_total": rng(durations), "tiempo_por_caso": rng(cycles), "cola_maxima_por_recurso": queues,
            "pasos_por_tiempo": sorted(({"id": i, "paso": name(i), "tiempo_promedio": _r(spent.get(i, 0) / n), "espera_promedio": _r(waits.get(i, 0) / n)}
                                        for i in tasks), key=lambda x: -x["tiempo_promedio"]),
            "caminos": [{"id": f, "de": name(d["source"]), "camino": d["name"] or name(d["target"]), "veces_en_promedio": _r(flows.get(f, 0) / n)}
                        for f, d in model.flows.items() if len(model.outgoing.get(d["source"], [])) > 1]}


class Reporter:
    def __init__(self, root, lock):
        self.path, self.lock = os.path.join(root, "reports", "ultimo_resultado.json"), lock
        self.latest, self.writing = 0, threading.Lock()

    def save(self, name, data):
        """Otro informe del mismo tipo (un archivo por nombre, se reemplaza)."""
        try:
            with self.writing:
                self._dump(os.path.join(os.path.dirname(self.path), name), data)
        except OSError as e:
            print(f"no se pudo guardar {name}: {e}", file=sys.stderr)

    def _dump(self, path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path + ".tmp", "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
        os.replace(path + ".tmp", path)      # quien lo lea ve el anterior o el nuevo, nunca a medias

    def submit(self, body, results):
        """No debe tumbar la simulación: cualquier fallo se avisa en la consola del servidor."""
        try:
            self.latest += 1
            mine, report = self.latest, build(body, results)
            self._write(mine, report)
            threading.Thread(target=self._complete, args=(mine, body, report), daemon=True).start()
        except Exception as e:   # noqa: BLE001
            print(f"no se pudo guardar el informe: {e}", file=sys.stderr)

    def _complete(self, mine, body, report):
        try:
            runs = repeat(body, self.lock, lambda: mine != self.latest)
            if runs:
                self._write(mine, {**report, "repeticiones": runs})
        except Exception as e:   # noqa: BLE001
            print(f"no se pudo completar el informe: {e}", file=sys.stderr)

    def _write(self, mine, report):
        with self.writing:
            if mine != self.latest:
                return
            self._dump(self.path, report)
