"""Rasterizado de polígonos de IA para las máscaras de referencia A‑E0 (`AI_POLYGON_RASTER`, `NUMPY_MINIMAL`).

Convención:
- coordenadas a resolución completa, con el píxel ``(i, j)`` ocupando ``[i, i+1) × [j, j+1)``;
- un píxel está dentro si **su centro** ``(i + 0.5, j + 0.5)`` está dentro según la regla
  **par‑impar** sobre todos los anillos juntos. Un anillo dentro de otro es un agujero, sin más
  marcas;
- nada de suavizado ni de ajuste a bordes: es la derivación primaria, transparente y reproducible
  (ChatGPT 007). Cualquier refinamiento sería otra derivación, declarada aparte.
"""

from __future__ import annotations

import numpy as np


def _edges(rings):
    segs = []
    for ring in rings:
        pts = np.asarray(ring, dtype=np.float64)
        if pts.ndim != 2 or pts.shape[1] != 2 or len(pts) < 3:
            raise ValueError("cada anillo necesita al menos 3 vértices [x, y]")
        segs.append(np.concatenate([pts, np.roll(pts, -1, axis=0)], axis=1))
    return np.concatenate(segs) if segs else np.zeros((0, 4))


def rasterize(rings, shape) -> np.ndarray:
    """Máscara booleana ``shape = (alto, ancho)`` de los anillos, por regla par‑impar en el centro del píxel."""
    h, w = shape
    out = np.zeros((h, w), bool)
    e = _edges(rings)
    if not len(e):
        return out
    x0, y0, x1, y1 = e.T
    keep = y0 != y1
    x0, y0, x1, y1 = x0[keep], y0[keep], x1[keep], y1[keep]
    lo, hi = np.minimum(y0, y1), np.maximum(y0, y1)
    row_first = max(0, int(np.floor(lo.min() - 0.5)))
    row_last = min(h - 1, int(np.ceil(hi.max() - 0.5)))
    centers = np.arange(w) + 0.5
    for j in range(row_first, row_last + 1):
        yc = j + 0.5
        active = (lo <= yc) & (yc < hi)
        if not active.any():
            continue
        xs = x0[active] + (yc - y0[active]) * (x1[active] - x0[active]) / (y1[active] - y0[active])
        xs.sort()
        inside = np.searchsorted(xs, centers, side="right") % 2 == 1
        out[j] = inside
    return out


def rasterize_person(entry: dict, shape) -> dict:
    """Máscara y zona incierta de una entrada ``{"rings": [...], "uncertain_rings": [...]}``."""
    mask = rasterize(entry.get("rings", []), shape)
    uncertain_rings = entry.get("uncertain_rings") or []
    uncertain = rasterize(uncertain_rings, shape) if uncertain_rings else np.zeros(shape, bool)
    return {"mask": mask, "uncertain": uncertain}
