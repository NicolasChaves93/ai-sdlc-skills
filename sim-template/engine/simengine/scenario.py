"""Escenario: parámetros (negocio o supuesto), recursos con capacidad y datos por paso (tiempos, probabilidades)."""
import math


class Scenario:
    def __init__(self, data, params=None):
        if data.get("contadores") or data.get("derivados"):
            raise NotImplementedError("contadores/derivados (usados por la trivia) aún no están soportados por el motor de Python")
        self.d = data
        self.P = {k: (params or {}).get(k, v["valor"]) for k, v in data.get("params", {}).items()}

    def ev(self, x):
        """Valor numérico de un número o de una expresión sobre los parámetros (p. ej. 'B*0.002')."""
        if x is None or isinstance(x, (int, float)):
            return x
        return float(eval(str(x), {"__builtins__": {}, "math": math}, dict(self.P)))

    def cfg(self, element_id):
        return self.d.get("elementos", {}).get(element_id, {})

    @property
    def resources(self):
        return self.d.get("recursos", {})

    @property
    def root(self):
        return self.d.get("raiz", {})
