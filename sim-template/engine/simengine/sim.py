"""Simulación de eventos discretos: SpiffWorkflow decide el flujo, SimPy pone el reloj, las colas y la capacidad.

La forma del resultado (`results()`) es el contrato con la interfaz web; las claves en español son las del formato de
escenarios y de la interfaz. Mismas reglas de tiempos, recursos y compuertas que el prototipo en JavaScript (ver tests).
"""
import hashlib
import math
import random
from dataclasses import dataclass, field

import simpy
from SpiffWorkflow.bpmn import BpmnWorkflow
from SpiffWorkflow.bpmn.parser import BpmnParser
from SpiffWorkflow.util.task import TaskState

from .model import Model, executable_xml
from .scenario import Scenario

ACTIVITIES = {"ManualTask", "UserTask", "ServiceTask", "Task"}
_PREPARED = {}


class SimulationTooLong(RuntimeError):
    pass


@dataclass
class Prepared:
    model: Model
    spec: object
    subprocess_specs: dict = field(default_factory=dict)


def prepare(xml):
    """Lee el BPMN y construye la especificación ejecutable (en caché por contenido)."""
    key = hashlib.sha1(xml.encode("utf-8") if isinstance(xml, str) else xml).hexdigest()
    if key not in _PREPARED:
        model = Model(xml)
        parser = BpmnParser()
        parser.add_bpmn_str(executable_xml(xml))
        _PREPARED[key] = Prepared(model, parser.get_spec(model.process_id), parser.get_subprocess_specs(model.process_id))
        if len(_PREPARED) > 16:
            _PREPARED.pop(next(iter(_PREPARED)))
    return _PREPARED[key]


class _Resource:
    def __init__(self, env, rid, name, cap):
        self.id, self.name, self.cap = rid, name, cap
        self.res = simpy.Resource(env, cap)
        self.saturated, self.last, self.full, self.maxq, self.busy = 0.0, 0.0, False, 0, 0.0

    def touch(self, now):
        if self.full:
            self.saturated += now - self.last
        self.last, self.full = now, self.res.count >= self.cap


@dataclass
class _Stat:
    entries: int = 0
    done: int = 0
    waits: list = field(default_factory=list)
    svc: list = field(default_factory=list)
    wait_total: float = 0.0
    maxq: int = 0
    w: int = 0      # esperando en cola ahora
    s: int = 0      # ejecutándose ahora
    sub: int = 0    # dentro de este subproceso ahora


def _pct(a, p):
    if not a:
        return 0.0
    b = sorted(a)
    return b[min(len(b) - 1, int(p * len(b)))]


def _avg(a):
    return sum(a) / len(a) if a else 0.0


class Simulation:
    def __init__(self, prepared, scenario, params=None, mode="azar", profile=None, seed=7, forced=None,
                 record_samples=True, on_move=None, max_steps=None, max_case_steps=5000):
        self.model, self.spec, self.sub_specs = prepared.model, prepared.spec, prepared.subprocess_specs
        self.sc = scenario if isinstance(scenario, Scenario) else Scenario(scenario, params)
        self.mode, self.profile = mode, profile or self.sc.root.get("perfil") or "uniforme"
        self.rnd = random.Random(seed)
        self.forced = dict(forced or {})
        self.env = simpy.Environment()
        self.res = {rid: _Resource(self.env, rid, r.get("nombre", rid), max(1, round(self.sc.ev(r["capacidad"])))) for rid, r in self.sc.resources.items()}
        self.stats, self.flow_count, self.moves = {}, {}, []
        self.cycles, self.log, self.samples = [], [], []
        self.on_move, self.max_steps, self.max_case_steps, self.steps = on_move, max_steps, max_case_steps, 0
        self.scheduled = self.finished = self.next_case = 0
        self._moves_out = []
        self._flow_by_pair = {}
        for f in self.model.flows.values():
            self._flow_by_pair.setdefault((f["source"], f["target"]), f["id"])
        if record_samples:
            self.env.process(self._sampler())

    # ---------- utilidades ----------
    def st(self, node_id):
        return self.stats.setdefault(node_id, _Stat())

    @property
    def active(self):
        return self.scheduled - self.finished

    def _sample(self, d, random_arrival=False):
        """Muestrea una duración. En mejor/peor caso se usan los percentiles 10/90 (salvo en las llegadas)."""
        if d is None:
            return 0.0
        if isinstance(d, (int, float, str)):
            return max(0.0, self.sc.ev(d))
        q = None if random_arrival else (0.1 if self.mode == "mejor" else 0.9 if self.mode == "peor" else None)
        U = (lambda: q) if q is not None else self.rnd.random
        Z = (lambda: -1.2816 if q < 0.5 else 1.2816) if q is not None else (lambda: self.rnd.gauss(0, 1))
        ev, t = self.sc.ev, d["tipo"]
        if t == "const":
            return ev(d["valor"])
        if t == "uniforme":
            a, b = ev(d["min"]), ev(d["max"])
            return a + (b - a) * U()
        if t == "exp":
            return -ev(d["media"]) * math.log(1 - U())
        if t == "triangular":
            a, c, b, u = ev(d["min"]), ev(d["moda"]), ev(d["max"]), U()
            f = (c - a) / (b - a)
            return a + math.sqrt(u * (b - a) * (c - a)) if u < f else b - math.sqrt((1 - u) * (b - a) * (b - c))
        if t == "lognormal":
            m, cv = ev(d["media"]), ev(d.get("cv", 0.5))
            s2 = math.log(1 + cv * cv)
            return math.exp(math.log(m) - s2 / 2 + math.sqrt(s2) * Z())
        raise ValueError("distribución desconocida: " + t)

    def _choose(self, gid, counters):
        cfg, outs, ev = self.sc.cfg(gid), self.model.outgoing[gid], self.sc.ev
        if self.forced.get(gid) in outs:
            return self.forced[gid]
        if cfg.get("tipo") == "exitos":                  # repite «flujo» hasta juntar N aciertos de probabilidad «prob»; al salir se reinicia
            n = counters.get(gid, 0) + (self.rnd.random() < ev(cfg["prob"]))
            if n < ev(cfg["veces"]):
                counters[gid] = n
                return cfg["flujo"]
            counters[gid] = 0
            return next(f for f in outs if f != cfg["flujo"])
        counter_gw = cfg.get("tipo") == "contador"
        if not counter_gw and self.mode == "mejor" and cfg.get("caminoMejor"):
            return cfg["caminoMejor"]
        if not counter_gw and self.mode == "peor" and cfg.get("caminoPeor"):
            k = "peor_" + gid
            n = counters.get(k, 0) + 1
            if n <= cfg.get("repPeor", 2):
                counters[k] = n
                return cfg["caminoPeor"]
            counters[k] = 0
            return next(f for f in outs if f != cfg["caminoPeor"])
        if counter_gw:                                   # repite el camino «flujo» hasta la N-ésima visita; al salir se reinicia (así vale igual en cada ronda)
            n = counters.get(gid, 0) + 1
            if n < ev(cfg["veces"]):
                counters[gid] = n
                return cfg["flujo"]
            counters[gid] = 0
            return next(f for f in outs if f != cfg["flujo"])
        pm = cfg.get("prob", {})
        fixed = sum(ev(pm[f]) for f in outs if f in pm)
        free = [f for f in outs if f not in pm]
        u, acc = self.rnd.random(), 0.0
        for f in outs:
            acc += ev(pm[f]) if f in pm else max(0.0, 1 - fixed) / (len(free) or 1)
            if u < acc:
                return f
        return outs[-1]

    def _move(self, flow_id, case):
        self.flow_count[flow_id] = self.flow_count.get(flow_id, 0) + 1
        if self.on_move:
            self.on_move(self.env.now, flow_id, case)
        elif len(self.moves) < 60000:
            self.moves.append((self.env.now, flow_id, case))
        self._moves_out.append(flow_id)

    # ---------- un caso (p. ej. un sorteo) ----------
    def _flow_into(self, cs, target):
        """Flecha por la que se llegó a `target`: la que eligió la compuerta o, si no, la que sale del paso anterior."""
        if cs["chosen"] and self.model.flows[cs["chosen"]]["target"] == target:
            return cs["chosen"]
        chain = [cs["prev"]] + (self.model.ancestors(cs["prev"]) if cs["prev"] else [])
        return next((f for f in self.model.incoming.get(target, []) if self.model.flows[f]["source"] in chain), None)

    def _arrive(self, cs, bid, case):
        """Registra la llegada a un elemento: recorrido por la flecha, entradas y apertura/cierre de subprocesos.

        SpiffWorkflow solo entrega la tarea de un subproceso cuando este TERMINA (al entrar, arranca solo su interior);
        por eso el subproceso se abre al llegar su primer elemento interno y se cierra cuando se entrega su tarea."""
        required = set(self.model.ancestors(bid))
        for sp in [x for x in cs["open"] if x not in required and x != bid]:
            self._close_subprocess(cs, sp)
        if bid in self.model.subprocesses:                  # el subproceso terminó
            if bid in cs["open"]:
                self._close_subprocess(cs, bid)
            cs["prev"], cs["chosen"] = bid, None
            return
        for sp in reversed(self.model.ancestors(bid)):      # entra a subprocesos (el más externo primero)
            if sp not in cs["open"]:
                cs["open"][sp] = self.env.now
                self.st(sp).entries += 1
                flow = self._flow_into(cs, sp)
                if flow:
                    self._move(flow, case)
                    cs["chosen"] = None
        self.st(bid).entries += 1
        flow = self._flow_into(cs, bid)
        if flow:
            self._move(flow, case)
        cs["prev"], cs["chosen"] = bid, None

    def _close_subprocess(self, cs, sp):
        t0 = cs["open"].pop(sp)
        s = self.st(sp)
        s.done += 1
        s.svc.append(self.env.now - t0)

    def _activity(self, cs, bid, case):
        cfg, env = self.sc.cfg(bid), self.env
        dur = self._sample(cfg.get("dur")) * (self.sc.ev(cfg["escala"]) if cfg.get("escala") is not None else 1)
        scheduled, st, anc = env.now, self.st(bid), self.model.ancestors(bid)
        for a in anc:
            self.st(a).sub += 1
        if cfg.get("recurso"):
            r = self.res[cfg["recurso"]]
            rq = r.res.request()
            r.maxq = max(r.maxq, len(r.res.queue))
            st.maxq = max(st.maxq, len(r.res.queue))
            st.w += 1
            yield rq
            r.touch(env.now)
            start = env.now
            wait = start - scheduled
            st.waits.append(wait)
            st.wait_total += wait
            st.w -= 1
            st.s += 1
            yield env.timeout(dur)
            r.res.release(rq)
            r.touch(env.now)
            r.busy += dur
        else:
            start = env.now
            st.s += 1
            yield env.timeout(dur)
        st.s -= 1
        for a in anc:
            self.st(a).sub -= 1
        st.svc.append(dur)
        st.done += 1
        self.log.append({"case": case, "activity_id": bid, "resource": cfg.get("recurso") or "", "schedule": scheduled, "start": start, "complete": env.now})

    def _case(self, case, delay):
        if delay:
            yield self.env.timeout(delay)
        t0 = self.env.now
        wf = BpmnWorkflow(self.spec, self.sub_specs)
        counters = {}
        cs = {"prev": None, "chosen": None, "open": {}, "n": 0}
        deep = 10 ** 7      # SpiffWorkflow busca tareas con profundidad máxima 1000 por defecto: más allá, el flujo parece terminado en silencio
        while True:
            ready = wf.get_tasks(state=TaskState.READY, max_depth=deep)
            if not ready:
                started = wf.get_tasks(state=TaskState.STARTED, max_depth=deep)
                if not started:
                    break
                started[0].complete()
                continue
            t = ready[0]
            kind, bid = type(t.task_spec).__name__, t.task_spec.bpmn_id
            if bid is None or bid not in self.model.nodes:
                t.run()
                continue
            self.steps += 1
            cs["n"] += 1
            if cs["n"] > self.max_case_steps or (self.max_steps and self.steps > self.max_steps):
                raise SimulationTooLong(f"un caso superó {self.max_case_steps} pasos: ¿hay un bucle sin fin (p. ej. un camino forzado)?")
            self._arrive(cs, bid, case)
            for other in self.sc.cfg(bid).get("reinicia", []):      # p. ej. cerrar un sorteo antes: la cuenta de la vuelta se pierde
                counters.pop(other, None)
            if kind == "ExclusiveGateway" and len(self.model.outgoing.get(bid, [])) > 1:
                cs["chosen"] = self._choose(bid, counters)
                t.data["ruta_" + bid] = cs["chosen"]
                t.run()
            elif kind in ACTIVITIES:
                if kind == "ServiceTask":                 # las tareas del sistema quedan «iniciadas»; se completan desde fuera
                    t.run()
                    yield from self._activity(cs, bid, case)
                    t.complete()
                else:
                    yield from self._activity(cs, bid, case)
                    t.run()
            else:
                t.run()
        if cs["prev"] is None or self.model.nodes[cs["prev"]]["tag"] != "endEvent":
            raise RuntimeError(f"el caso {case} terminó sin llegar a un evento de fin (último paso: {cs['prev']})")
        for sp in list(cs["open"]):
            self._close_subprocess(cs, sp)
        self.cycles.append(self.env.now - t0)
        self.finished += 1

    def _sampler(self):
        dt = 1.0
        while True:
            self.samples.append({"t": self.env.now, "a": self.active, "s": self.snapshot()})
            yield self.env.timeout(dt)
            if len(self.samples) >= 3000:
                self.samples = self.samples[::2]
                dt *= 2

    # ---------- ejecución ----------
    def _spawn(self, delay):
        case = self.next_case
        self.next_case += 1
        self.scheduled += 1
        return self.env.process(self._case(case, delay))

    def _arrival_times(self, k):
        root, ev = self.sc.root, self.sc.ev
        window = ev(root["ventana"] if "ventana" in root else (root.get("llegadas") or {}).get("max", 0)) or 0
        out, acc = [], 0.0
        for _ in range(k):
            if self.profile == "rampa":
                out.append(window * math.sqrt(self.rnd.random()))
            elif self.profile == "pico":
                out.append(0.0)
            elif self.profile == "poisson":
                acc += -(window / k) * math.log(1 - self.rnd.random())
                out.append(acc)
            else:
                out.append(self._sample(root.get("llegadas"), random_arrival=True) if root.get("llegadas") else 0.0)
        return out

    def start(self):
        k = max(1, round(self.sc.ev(self.sc.root.get("instancias", 1))))
        self._procs = [self._spawn(t) for t in self._arrival_times(k)]

    def run(self):
        """Corre todo el evento hasta que terminan todos los casos."""
        self.start()
        self.env.run(until=self.env.all_of(self._procs))
        return self

    # ---------- modo en vivo ----------
    def advance(self, until):
        if until > self.env.now:
            self.env.run(until=until)

    def inject(self, n=1, every=0.0):
        for i in range(n):
            self._spawn(i * every)

    def force(self, gateway, flow=None):
        if flow:
            self.forced[gateway] = flow
        else:
            self.forced.pop(gateway, None)

    @property
    def pending(self):
        return self.active > 0

    def snapshot(self):
        return {k: [s.w, s.s, s.sub] for k, s in self.stats.items() if s.w or s.s or s.sub}

    def drain_moves(self):
        out, self._moves_out = self._moves_out, []
        return out

    # ---------- resultados (contrato con la interfaz) ----------
    def results(self, with_samples=True):
        T = self.env.now
        stats = {}
        for k, s in self.stats.items():
            stats[k] = {"id": k, "entradas": s.entries, "completadas": s.done, "cortadas": 0, "esperaProm": _avg(s.waits), "esperaP95": _pct(s.waits, .95),
                        "esperaMax": max(s.waits, default=0.0), "esperaTotal": s.wait_total, "servicioProm": _avg(s.svc), "servicioP95": _pct(s.svc, .95), "colaMax": s.maxq}
        resources = {}
        for r in self.res.values():
            r.touch(T)
            resources[r.id] = {"id": r.id, "nombre": r.name, "capacidad": r.cap, "utilizacion": r.busy / (r.cap * T) if T else 0.0,
                               "saturado": r.saturated / T if T else 0.0, "colaMax": r.maxq}
        total = sum(self.flow_count.values())
        stride = max(1, math.ceil(total / 3000))
        log = [[t, f, c] for (t, f, c) in self.moves if c % stride == 0][:20000]
        return {"params": self.sc.P, "duracion": T, "stats": stats, "flowCount": dict(self.flow_count), "recursos": resources,
                "samples": ([*self.samples, {"t": T, "a": self.active, "s": self.snapshot()}] if with_samples else []), "log": log,
                "ciclo": {"n": len(self.cycles), "prom": _avg(self.cycles), "p95": _pct(self.cycles, .95)}, "pasos": self.steps, "activos": self.active}


def simulate(xml, scenario, params=None, mode="azar", profile=None, seed=7, forced=None, with_samples=True, max_steps=None, max_case_steps=5000):
    """Atajo: corre un evento completo y devuelve los resultados."""
    sim = Simulation(prepare(xml), scenario, params, mode, profile, seed, forced, record_samples=with_samples, max_steps=max_steps, max_case_steps=max_case_steps)
    return sim.run().results(with_samples)
