"""Escenarios aleatorios: varía solo lo que es «supuesto» (lo «real» y «negocio» queda fijo) y mira qué resultados salen.

Cada escenario sortea los parámetros supuestos alrededor de su valor actual y, si se pide, alarga o acorta cada tarea
(sus tiempos también son supuestos). Se corre varias veces con distinto azar y se promedia.
"""
import random

from simengine import Model, Scenario, Simulation, prepare

SEEDS = 3
TASKS = ("task", "userTask", "serviceTask", "manualTask")


def _sample(rnd, definition, current, spread):
    low, high = current * (1 - spread), current * (1 + spread)
    low, high = max(low, definition.get("min", low)), min(high, definition.get("max", high))
    value = rnd.uniform(low, high) if high > low else current
    step = definition.get("paso")
    if step:
        value = round(value / step) * step
        value = min(max(value, definition.get("min", value)), definition.get("max", value))
    return round(value, 6)


def explore(body, lock, scenarios=100, spread=0.5, vary_times=True, goal=None, seed=1):
    """`goal`: duración máxima deseada (segundos). Devuelve rango, supuestos que más pesan, y los mejores y peores casos."""
    scenarios, spread = max(10, min(int(scenarios), 300)), max(0.05, min(float(spread), 0.9))
    spec, model, sc = prepare(body["xml"]), Model(body["xml"]), body["escenario"]
    current = {k: (body.get("params") or {}).get(k, d["valor"]) for k, d in sc.get("params", {}).items()}
    free = {k: d for k, d in sc.get("params", {}).items() if d.get("origen") == "supuesto"}
    tasks = [i for i, n in model.nodes.items() if n["tag"] in TASKS and sc.get("elementos", {}).get(i, {}).get("dur") is not None]
    rnd, rows = random.Random(seed), []
    for _ in range(scenarios):
        params = {**current, **{k: _sample(rnd, d, current[k], spread) for k, d in free.items()}}
        factors = {i: round(rnd.uniform(1 - spread, 1 + spread), 3) for i in tasks} if vary_times else {}
        elements = {i: dict(c) for i, c in sc.get("elementos", {}).items()}
        for i, f in factors.items():
            base = elements[i].get("escala")
            elements[i]["escala"] = f if base is None else f"({base})*{f}"
        total, spent = 0.0, {}
        for n in range(SEEDS):
            with lock:
                r = Simulation(spec, Scenario({**sc, "elementos": elements}, params), mode="azar", profile=body.get("perfil"), seed=1000 + n,
                               forced=body.get("forzar") or {}, record_samples=False).run().results(with_samples=False)
            total += r["duracion"] / SEEDS
            for i in tasks:
                s = r["stats"].get(i)
                if s:
                    spent[i] = spent.get(i, 0) + (s["servicioProm"] * s["completadas"] + s["esperaTotal"]) / SEEDS
        rows.append({"duracion": total, "params": {k: params[k] for k in free}, "factores": factors, "pesos": spent})
    rows.sort(key=lambda r: r["duracion"])
    durations = [r["duracion"] for r in rows]
    pick = lambda p: round(durations[min(len(durations) - 1, int(p * len(durations)))], 1)
    name = lambda i: model.nodes[i]["name"] or i
    third = max(1, len(rows) // 3)

    def influence(label, key, value):
        ordered = sorted(rows, key=value)
        if value(ordered[0]) == value(ordered[-1]):
            return None
        mean = lambda part, f: sum(f(r) for r in part) / len(part)
        low, high = ordered[:third], ordered[-third:]
        return {"id": key, "nombre": label, "valor_bajo": round(mean(low, value), 3), "valor_alto": round(mean(high, value), 3),
                "duracion_con_bajo": round(mean(low, lambda r: r["duracion"]), 1), "duracion_con_alto": round(mean(high, lambda r: r["duracion"]), 1)}

    weights = [influence(d.get("etiqueta", k), k, lambda r, k=k: r["params"][k]) for k, d in free.items()]
    if vary_times:                       # solo las tareas que de verdad ocupan tiempo: el resto daría diferencias por puro azar
        mean_total = sum(durations) / len(durations)
        weights += [influence("Tiempo de «" + name(i) + "»", i, lambda r, i=i: r["factores"][i]) for i in tasks
                    if sum(r["pesos"].get(i, 0) for r in rows) / len(rows) > 0.03 * mean_total]
    weights = sorted((w for w in weights if w), key=lambda w: -abs(w["duracion_con_alto"] - w["duracion_con_bajo"]))[:6]
    result = {"escenarios": scenarios, "variacion": spread, "tiempos_variados": vary_times,
              "fijos": [d.get("etiqueta", k) for k, d in sc.get("params", {}).items() if k not in free],
              "duracion": {"minimo": pick(0), "mediana": pick(.5), "p90": pick(.9), "maximo": pick(1)},
              "supuestos_que_mas_pesan": weights, "meta": None,
              "mejores": [{k: r[k] for k in ("duracion", "params", "factores")} for r in rows[:3]],
              "peores": [{k: r[k] for k in ("duracion", "params", "factores")} for r in rows[:-4:-1]]}
    if goal:
        ok = [r for r in rows if r["duracion"] <= float(goal)]
        typical = lambda part, w: sorted((r["params"].get(w["id"], r["factores"].get(w["id"])) for r in part))[len(part) // 2]
        result["meta"] = {"duracion_maxima": float(goal), "cumplen": len(ok), "porcentaje": round(100 * len(ok) / len(rows), 1),
                          "valores_tipicos_al_cumplir": [{"id": w["id"], "nombre": w["nombre"], "valor": round(typical(ok, w), 3)} for w in weights] if ok else []}
    return result
