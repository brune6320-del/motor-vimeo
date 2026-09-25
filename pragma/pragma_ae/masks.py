"""Primitivas de máscara sin dependencias pesadas.

Convenciones:
- máscara: array 2D booleano (alto, ancho);
- caja: XYXY en píxeles enteros, semiabierta: x1 <= x < x2, y1 <= y < y2;
- RLE: sin comprimir, orden por columnas y empezando por ceros, el mismo esquema
  que usa el formato ``uncompressed_rle`` de la familia SAM. Antes de consumir
  salidas reales de SAM 2 AMG, confirmar el formato contra el commit instalado.
"""

from __future__ import annotations

import hashlib

import numpy as np


def as_bool(mask) -> np.ndarray:
    array = np.asarray(mask)
    if array.ndim != 2:
        raise ValueError(f"La máscara debe ser 2D; forma recibida {array.shape}")
    return array.astype(bool, copy=False)


def area(mask) -> int:
    return int(as_bool(mask).sum())


def mask_bbox(mask):
    """Caja semiabierta que envuelve la máscara, o None si está vacía."""
    m = as_bool(mask)
    rows = np.flatnonzero(m.any(axis=1))
    cols = np.flatnonzero(m.any(axis=0))
    if rows.size == 0:
        return None
    return (int(cols[0]), int(rows[0]), int(cols[-1]) + 1, int(rows[-1]) + 1)


def box_area(box) -> int:
    x1, y1, x2, y2 = box
    return max(0, x2 - x1) * max(0, y2 - y1)


def box_iou(a, b) -> float:
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = box_area(a) + box_area(b) - inter
    return inter / union if union else 0.0


def box_union(a, b):
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def intersection_area(a, b, box_a=None, box_b=None) -> int:
    """|a ∩ b| calculado solo dentro de la intersección de sus cajas."""
    a = as_bool(a)
    b = as_bool(b)
    box_a = box_a if box_a is not None else mask_bbox(a)
    box_b = box_b if box_b is not None else mask_bbox(b)
    if box_a is None or box_b is None:
        return 0
    x1, y1 = max(box_a[0], box_b[0]), max(box_a[1], box_b[1])
    x2, y2 = min(box_a[2], box_b[2]), min(box_a[3], box_b[3])
    if x1 >= x2 or y1 >= y2:
        return 0
    return int(np.logical_and(a[y1:y2, x1:x2], b[y1:y2, x1:x2]).sum())


def mask_iou(a, b) -> float:
    inter = intersection_area(a, b)
    union = area(a) + area(b) - inter
    return inter / union if union else 0.0


def dilate_square(mask, radius: int) -> np.ndarray:
    """Dilatación exacta con elemento cuadrado (2r+1)², vía imagen integral: O(alto·ancho)."""
    m = as_bool(mask)
    if radius <= 0:
        return m.copy()
    h, w = m.shape
    integral = np.zeros((h + 1, w + 1), dtype=np.int64)
    integral[1:, 1:] = m.cumsum(axis=0, dtype=np.int64).cumsum(axis=1)
    y0 = np.clip(np.arange(h) - radius, 0, h)
    y1 = np.clip(np.arange(h) + radius + 1, 0, h)
    x0 = np.clip(np.arange(w) - radius, 0, w)
    x1 = np.clip(np.arange(w) + radius + 1, 0, w)
    total = (integral[y1][:, x1] - integral[y0][:, x1]
             - integral[y1][:, x0] + integral[y0][:, x0])
    return total > 0


def rle_encode(mask) -> dict:
    m = as_bool(mask)
    h, w = m.shape
    flat = m.T.reshape(-1)
    if flat.size == 0:
        return {"size": [h, w], "counts": []}
    change = np.flatnonzero(flat[1:] != flat[:-1]) + 1
    bounds = np.concatenate(([0], change, [flat.size]))
    counts = np.diff(bounds).astype(int).tolist()
    if flat[0]:
        counts = [0] + counts
    return {"size": [int(h), int(w)], "counts": counts}


def rle_decode(rle: dict) -> np.ndarray:
    h, w = (int(v) for v in rle["size"])
    counts = np.asarray(rle["counts"], dtype=np.int64)
    values = np.zeros(counts.size, dtype=bool)
    values[1::2] = True
    flat = np.repeat(values, counts)
    if flat.size != h * w:
        raise ValueError(f"RLE incoherente: {flat.size} píxeles para {h}×{w}")
    return flat.reshape(w, h).T


def packed_sha256(mask) -> str:
    """Hash de contenido de la máscara, independiente del formato de archivo."""
    m = as_bool(mask)
    header = f"{m.shape[0]}x{m.shape[1]}:".encode()
    return hashlib.sha256(header + np.packbits(m).tobytes()).hexdigest()
