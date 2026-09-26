"""A-E(−1) v1.4: una sola intervención (el positivo H2) sobre la cadena ganadora de v1.3.

Nada de este módulo ejecuta SAM 2. Define, antes de la corrida:

- la región donde puede caer H2: los píxeles que son agujero ``D`` (por consenso de las dos llaves
  de v1.3) en las **tres** semillas de referencia ``+POS_HAIR+SLEEVE|box+corrections``;
- la regla reproducible que elige H2 dentro de esa región;
- el plan de llamadas (referencia bit a bit + H2 + perturbaciones de H2);
- las medidas prerregistradas: cierre del agujero objetivo, agujeros nuevos fuera de la región de
  H2, empeoramiento de O y las hipótesis H-C3 (Claude) y H-G5 (ChatGPT 005).

Todas las medidas **informan**; la aceptación sigue siendo la del protocolo de auditoría ciega v2
rev. 1 (cuatro criterios en las dos llaves, agujeros, sentinelas y adjudicación técnica).
"""

from __future__ import annotations

import numpy as np

from . import aem1_v13 as v13
from .aem1_v13_audit import holes_with_masks
from .masks import as_bool, components, dilate_square, mask_iou

REF_BRANCH = "+POS_HAIR+SLEEVE"
H2_BRANCH = "+POS_HAIR+SLEEVE+H2"
PROTOCOL = "box+corrections"
SEEDS = (0, 1, 2)
HOLE_MIN_PX = 1000
# El parche 13×13 de la compuerta de luma debe caber entero en material oscuro; el resto de
# restricciones (caja de contacto, holdouts, prompts) son las mismas de H1 y S1 en v1.3.
H2_SAFE_HALF_MIN = v13.PATCH_RADIUS + 1
H2_REGION_DILATION_PX = v13.STEP
# Un agujero de v1.4 es una pérdida nueva si al menos la mitad de sus píxeles estaban DENTRO de la
# máscara de referencia (si ya estaban fuera, es material que ya faltaba y ahora quedó encerrado).
NEW_HOLE_PRIOR_INSIDE_MIN = 0.5
# Regla de medición de O de la adjudicación v1.3 (dialogo/005; aceptada por ChatGPT 005),
# prerregistrada aquí con la corrección de islas separadas del núcleo hombro/blusa.
BUN_CORE = (2610, 315, 2780, 415)          # ∩ material oscuro
SHOULDER_CORE = (2400, 840, 2520, 990)     # solo islas que no tocan su fila inferior
# El punto propuesto en la carta 005 (parte alta de la franja). Solo descriptivo en v1.4.
UPPER_PROBE = (2964, 672)


def seed_ids(branch):
    return [f"{branch}|{PROTOCOL}|s{k}" for k in SEEDS]


# ─── región y regla de H2 ─────────────────────────────────────────────────────────────────────

def common_defect_region(defect_holes: dict) -> np.ndarray:
    """Píxeles que son agujero D de consenso en todas las semillas.

    ``defect_holes``: semilla → lista de máscaras de agujeros D de consenso (ambas llaves).
    """
    region = None
    for seed, masks in defect_holes.items():
        if not masks:
            raise ValueError(f"semilla {seed} sin agujeros D: no hay región común")
        union = np.logical_or.reduce([as_bool(m) for m in masks])
        region = union if region is None else region & union
    return region


def select_point_in_region(dark, region, holdouts, prompts, contact_box=v13.CONTACT_BOX,
                           min_half=H2_SAFE_HALF_MIN, grid=2):
    """Como ``aem1_v13.select_safe_point``, pero solo en píxeles de ``region`` (rejilla par absoluta).

    Se elige el mayor cuadrado seguro (≥ 98 % oscuro). Empates: mayor fracción oscura, mayor
    margen a la caja de contacto, menor y, menor x. Restricciones: margen L∞ ≥ 40, holdouts y
    prompts ≥ 100 px, semilado ≥ ``min_half``.
    """
    region = as_bool(region)
    ys, xs = np.nonzero(region)
    keep = (xs % grid == 0) & (ys % grid == 0)
    xs, ys = xs[keep], ys[keep]
    if xs.size == 0:
        return None
    table = v13.integral(dark)
    halves = v13.safe_half_map(table, xs, ys)
    fractions = np.round(v13.square_mean(table, xs, ys, halves), 6)
    best = None
    for x, y, half, fraction in zip(xs.tolist(), ys.tolist(), halves.tolist(), fractions.tolist()):
        if half < min_half:
            continue
        margin = v13.box_margin((x, y), contact_box)
        if margin < v13.CONTACT_MARGIN_MIN:
            continue
        if any(v13.distance((x, y), h) < v13.HOLDOUT_DIST_MIN for h in holdouts):
            continue
        if any(v13.distance((x, y), p) < v13.PROMPT_DIST_MIN for p in prompts):
            continue
        key = (-half, -fraction, -margin, y, x)
        if best is None or key < best[0]:
            best = (key, x, y, half, margin, fraction)
    if best is None:
        return None
    _, x, y, half, margin, fraction = best
    return {"xy": [x, y], "safe_half": half, "safe_square_dark_fraction": fraction, "contact_margin_linf": margin}


# ─── medidas prerregistradas ──────────────────────────────────────────────────────────────────

def hole_containing(mask, xy, min_area=HOLE_MIN_PX):
    """El agujero cerrado ≥ ``min_area`` de ``mask`` que contiene el píxel ``xy``, con su número de lámina."""
    x, y = xy
    for hole in holes_with_masks(mask, min_area):
        if hole["mask"][y, x]:
            return hole
    return None


def h2_region(shape, target_mask, xy, radius=H2_REGION_DILATION_PX) -> np.ndarray:
    """Región de H2: el agujero objetivo dilatado 15 px; sin agujero objetivo, el cuadrado de 15 px alrededor de H2."""
    if target_mask is not None:
        return dilate_square(as_bool(target_mask), radius)
    out = np.zeros(shape, bool)
    x, y = xy
    out[max(0, y - radius):y + radius + 1, max(0, x - radius):x + radius + 1] = True
    return out


def closure(target_mask, mask, min_area=HOLE_MIN_PX) -> dict:
    """¿Se cerró el agujero objetivo? Cerrado = quedan < 1000 px sin cubrir y ningún agujero ≥ 1000 px lo toca.

    Lo segundo impide que un agujero grande que solo roza la región cuente como cerrado; lo
    primero impide que el faltante cuente como cerrado solo porque dejó de estar encerrado.
    """
    t = as_bool(target_mask)
    m = as_bool(mask)
    residual = int((t & ~m).sum())
    touching = [{"number": h["number"], "area": h["area"]} for h in holes_with_masks(m, min_area) if (h["mask"] & t).any()]
    return {"target_px": int(t.sum()), "residual_px": residual, "covered_fraction": round(1 - residual / max(int(t.sum()), 1), 4),
            "holes_touching_target": touching, "closed": residual < min_area and not touching}


def candidate_new_holes(mask, ref_mask, region, min_area=HOLE_MIN_PX) -> list:
    """Agujeros ≥ 1000 px de ``mask`` fuera de ``region`` que son pérdida nueva frente a ``ref_mask``.

    Devuelve sus números de lámina; que sean ``D`` lo deciden las dos llaves (consenso).
    """
    ref = as_bool(ref_mask)
    reg = as_bool(region)
    out = []
    for h in holes_with_masks(mask, min_area):
        if (h["mask"] & reg).any():
            continue
        inside_before = float((h["mask"] & ref).sum()) / h["area"]
        if inside_before >= NEW_HOLE_PRIOR_INSIDE_MIN:
            out.append({"number": h["number"], "area": h["area"], "bbox": list(h["bbox"]),
                        "fraction_inside_reference": round(inside_before, 4)})
    return out


def measure_o(mask, dark) -> dict:
    """Píxeles de máscara en los núcleos de la persona posterior (regla de medición de O)."""
    m = as_bool(mask)
    x1, y1, x2, y2 = BUN_CORE
    bun = m[y1:y2, x1:x2] & np.asarray(dark)[y1:y2, x1:x2]
    sx1, sy1, sx2, sy2 = SHOULDER_CORE
    sub = m[sy1:sy2, sx1:sx2]
    separate = [c["area"] for c in components(sub) if c["bbox"][3] < sy2 - sy1] if sub.any() else []
    core_px = int(bun.sum()) + int(sum(separate))
    return {"bun_core_px": int(bun.sum()), "shoulder_separate_px": int(sum(separate)), "core_px": core_px,
            "o_by_measurement": "FALSE" if core_px else "TRUE"}


def o_worse(o_ref: str, o_new: str, core_ref: int, core_new: int) -> bool:
    """Empeora O: pasa de TRUE a FALSE, o, si ya era FALSE, crecen los píxeles en los núcleos."""
    if o_ref == "TRUE":
        return o_new != "TRUE"
    return core_new > core_ref


def global_change(ref_mask, mask, region) -> dict:
    """Descriptivo: ¿reparación local o resegmentación global?"""
    ref, m, reg = as_bool(ref_mask), as_bool(mask), as_bool(region)
    out = ~reg
    return {"iou_global": round(mask_iou(ref, m), 4),
            "iou_outside_region": round(mask_iou(ref & out, m & out), 4) if (ref & out).any() or (m & out).any() else None,
            "lost_px_outside_region": int((ref & ~m & out).sum()), "gained_px_outside_region": int((m & ~ref & out).sum()),
            "gained_px_inside_region": int((m & ~ref & reg).sum())}


# ─── hipótesis prerregistradas ────────────────────────────────────────────────────────────────

def hypothesis_h_c3(per_seed: dict) -> str:
    """H-C3 (Claude, carta 005): H2 cierra el agujero objetivo en ≥ 2 de 3 semillas sin empeorar O."""
    ok = sum(1 for s in per_seed.values() if s["evaluable"] and s["closed"] and not s["o_worse"])
    unknown = sum(1 for s in per_seed.values() if not s["evaluable"])
    if ok >= 2:
        return "HOLDS"
    if ok + unknown <= 1:
        return "REFUTED"
    return "INDETERMINATE"


def hypothesis_h_g5(per_seed: dict) -> str:
    """H-G5 (ChatGPT 005): H2 es una reparación local, no una resegmentación global."""
    rows = list(per_seed.values())
    closed = sum(1 for s in rows if s["evaluable"] and s["closed"])
    if sum(1 for s in rows if s["evaluable"] and s["closed"] and s["new_d"]) >= 2 or sum(1 for s in rows if s["o_worse"]) >= 2:
        return "REFUTED"
    if closed >= 2 and not any(s["o_worse"] for s in rows) and not any(s["new_d"] for s in rows):
        return "HOLDS"
    return "INDETERMINATE"


# ─── plan de llamadas ─────────────────────────────────────────────────────────────────────────

def build_call_plan(prompts: dict, box, h2_perturbations: list) -> list:
    """Todas las llamadas de v1.4, en orden. ``prompts``: P+1, H1, S1, H2, P-1, P-2, P-3 → xy."""
    negatives = ["P-1", "P-2", "P-3"]
    calls = []

    def add(call_id, branch, point_ids, labels, seed=None, multimask=False, use_box=True, xy=None, **extra):
        points = [list((xy or {}).get(pid, prompts[pid])) for pid in point_ids]
        candidates = [f"{call_id}|{k}" for k in range(3)] if multimask else [call_id]
        calls.append({"call_id": call_id, "branch": branch, "protocol": "box" if multimask else PROTOCOL, **extra,
                      "point_ids": list(point_ids), "points": points, "labels": list(labels),
                      "box": list(box) if use_box else None, "mask_input_from": seed,
                      "multimask_output": multimask, "candidates": candidates})

    def chain(prefix, branch, positives, xy=None, **extra):
        ids = ["P+1"] + positives + negatives
        labels = [1] * (1 + len(positives)) + [0] * len(negatives)
        for k in SEEDS:
            add(f"{prefix}|{PROTOCOL}|s{k}", branch, ids, labels, seed={"call_id": "BASE|box", "index": k}, xy=xy, **extra)

    add("BASE|box", "BASE", [], [], multimask=True)
    chain(REF_BRANCH, REF_BRANCH, ["H1", "S1"])
    chain(H2_BRANCH, H2_BRANCH, ["H1", "S1", "H2"])
    for row in h2_perturbations:
        if row["valid"]:
            chain(f"PERTURB_POINT|H2|{row['id']}", "PERTURB_POINT", ["H1", "S1", "H2"], xy={"H2": row["xy"]},
                  target="H2", perturbation=row["id"])
    ids = [c["call_id"] for c in calls]
    assert len(ids) == len(set(ids)), "call_id repetido"
    return calls
