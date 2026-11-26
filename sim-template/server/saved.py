"""Escenarios guardados: «esto pasó tal día», para volver a cargarlo, ajustarlo y comparar antes contra después.

Un archivo por escenario en `<espacio-de-trabajo>/escenarios_guardados/`. Guarda los valores usados y el resultado de
ese momento (rango de varias corridas con las mismas semillas), así que cargar y comparar sin cambios da lo mismo.
"""
import hashlib
import json
import os
import re
import unicodedata
from datetime import datetime

from report import repeat

FOLDER = "escenarios_guardados"
KEPT = ("modo", "perfil", "semilla", "forzar")


def _folder(root):
    return os.path.join(root, FOLDER)


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _files(root):
    folder = _folder(root)
    return sorted((f for f in os.listdir(folder) if f.endswith(".json")), reverse=True) if os.path.isdir(folder) else []


def _find(root, ident):
    if f"{ident}.json" not in _files(root):          # solo nombres que ya están en la carpeta: el pedido no elige rutas
        raise KeyError(f"no existe el escenario guardado «{ident}»")
    return _read(os.path.join(_folder(root), f"{ident}.json"))


def _summary(stats):
    return {"duracion_total": stats["duracion_total"], "cola_maxima_por_recurso": stats["cola_maxima_por_recurso"], "pasos_por_tiempo": stats["pasos_por_tiempo"][:8]}


def _values(body):
    return {k: (body.get("params") or {}).get(k, d.get("valor")) for k, d in body["escenario"].get("params", {}).items()}


def _fingerprint(xml):
    return hashlib.sha1(xml.encode("utf-8")).hexdigest()[:12]


def save(root, body, lock):
    name = str(body.get("nombre") or "").strip()
    if not name:
        raise ValueError("ponle un nombre al escenario")
    now = datetime.now().astimezone()
    slug = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", name.lower()).encode("ascii", "ignore").decode()).strip("-")[:50] or "escenario"
    ident, n = f"{now:%Y%m%d-%H%M%S}-{slug}", 2
    while f"{ident}.json" in _files(root):
        ident, n = f"{now:%Y%m%d-%H%M%S}-{slug}-{n}", n + 1
    data = {"id": ident, "nombre": name, "nota": str(body.get("nota") or "").strip(), "fecha": now.isoformat(timespec="seconds"),
            "parte_id": body.get("parte_id"), "parte": body.get("parte") or "todo el proceso", "diagrama": _fingerprint(body["xml"]),
            "params": _values(body), "elementos": body["escenario"].get("elementos", {}), **{k: body.get(k) for k in KEPT},
            "resultado": _summary(repeat(body, lock, lambda: False))}
    os.makedirs(_folder(root), exist_ok=True)
    with open(os.path.join(_folder(root), f"{ident}.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    return data


def listing(root):
    out = []
    for f in _files(root):
        try:
            d = _read(os.path.join(_folder(root), f))
            out.append({k: d.get(k) for k in ("id", "nombre", "nota", "fecha", "parte", "parte_id")} | {"duracion_total": d["resultado"]["duracion_total"]})
        except (OSError, ValueError, KeyError):
            continue          # un archivo dañado no esconde los demás
    return out


def load(root, ident):
    return _find(root, ident)


def compare(root, body, lock):
    """Lo guardado contra lo que está en pantalla: qué se cambió y qué pasó con el resultado."""
    before = _find(root, body.get("id"))
    if before.get("parte_id") != body.get("parte_id"):
        raise ValueError(f"ese escenario es de «{before['parte']}»: cárgalo primero para comparar sobre la misma parte")
    labels = {k: d.get("etiqueta", k) for k, d in body["escenario"].get("params", {}).items()}
    now_values = _values(body)
    changed = [{"que": labels.get(k, k), "antes": before["params"].get(k), "ahora": v} for k, v in now_values.items() if before["params"].get(k) != v]
    elements = body["escenario"].get("elementos", {})
    steps = [i for i in sorted(set(elements) | set(before["elementos"]))
             if {k: v for k, v in elements.get(i, {}).items() if k != "detalle"} != {k: v for k, v in before["elementos"].get(i, {}).items() if k != "detalle"}]
    if (body.get("forzar") or {}) != (before.get("forzar") or {}):
        changed.append({"que": "Caminos forzados", "antes": len(before.get("forzar") or {}), "ahora": len(body.get("forzar") or {})})
    return {"nombre": before["nombre"], "fecha": before["fecha"], "antes": before["resultado"], "ahora": _summary(repeat(body, lock, lambda: False)),
            "valores_cambiados": changed, "pasos_cambiados": steps, "diagrama_cambio": before["diagrama"] != _fingerprint(body["xml"])}
