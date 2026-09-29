"""A-E(−1) v1.3: diseño cerrado y métricas prerregistradas (ChatGPT 002 · Claude 003).

Nada de este módulo ejecuta SAM 2. Define, antes de la corrida:

- las perturbaciones deterministas de punto (anillo L∞ de 15 px) y de caja (traslación,
  expansión y contracción por separado), con su regla de validez (``INVALID_PERTURBATION``);
- la regla reproducible que elige los prompts positivos nuevos dentro de una región segura;
- las etiquetas de estabilidad bajo perturbación y de propiedad frente al prompt recíproco.

Todas las etiquetas **informan y nunca deciden** la aceptación de una candidata: eso lo hacen los
cuatro criterios visuales del protocolo de auditoría ciega. Ninguna máscara compuesta
(p. ej. ``objetivo − posterior``) se evalúa ni se exporta en v1.3.
"""

from __future__ import annotations

import math

import numpy as np

from .masks import as_bool, mask_iou

# Caja de contacto del protocolo v1 §5 (semiabierta). Contiene toda la frontera chica↔persona
# posterior visible (moño, coronilla, hombro y blusa), así que la distancia a esta caja es una
# cota inferior de la distancia a esa frontera.
CONTACT_BOX = (2150, 250, 2900, 1300)

STEP = 15
# Axiales primero (obligatorias según ChatGPT 002), después diagonales: anillo L∞ de radio 15.
POINT_OFFSETS = ((STEP, 0), (-STEP, 0), (0, STEP), (0, -STEP),
                 (STEP, STEP), (STEP, -STEP), (-STEP, STEP), (-STEP, -STEP))
BOX_TRANSLATIONS = ((STEP, 0), (-STEP, 0), (0, -STEP), (0, STEP))

PATCH_RADIUS = 6                 # el mismo parche 13×13 de los sentinelas y del preflight
DARK_LUMA = 110                  # el mismo umbral "dark" de las regiones de auditoría
BLUR_RADIUS = 4                  # media en caja 9×9 para no confundir el grano de la foto con bordes
DARK_FRACTION_MIN = 0.98         # fracción mínima de material oscuro en el cuadrado seguro
SAFE_HALF_MIN = STEP + PATCH_RADIUS   # 21: el parche de cualquier perturbación queda dentro del cuadrado
SAFE_HALF_MAX = 150
CONTACT_MARGIN_MIN = 40          # L∞ desde CONTACT_BOX para los prompts nuevos de la chica
PERTURBED_CONTACT_MARGIN_MIN = CONTACT_MARGIN_MIN - STEP     # 25
HOLDOUT_DIST_MIN = 100           # euclídea, prompt nuevo ↔ cualquier holdout
PERTURBED_HOLDOUT_DIST_MIN = HOLDOUT_DIST_MIN - math.ceil(STEP * math.sqrt(2))   # 78
PROMPT_DIST_MIN = 100            # euclídea, prompt nuevo ↔ cualquier otro prompt
PERTURBED_DARK_FRACTION_MIN = 0.90

STABLE_IOU = 0.90
OWNERSHIP_DISJOINT_MAX = 0.02
OWNERSHIP_SHARED_MIN = 0.10
SENTINEL_KEEP_MIN = 0.80
SENTINEL_DROP_MAX = 0.20


# ─── geometría ────────────────────────────────────────────────────────────────────────────────

def box_margin(xy, box) -> int:
    """Distancia L∞ del píxel ``xy`` a la caja semiabierta; ≤ 0 si está dentro."""
    x, y = (int(round(float(v))) for v in xy)
    x1, y1, x2, y2 = box
    return max(x1 - x, x - (x2 - 1), y1 - y, y - (y2 - 1))


def distance(a, b) -> float:
    return math.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1]))


def point_perturbations(xy, offsets=POINT_OFFSETS):
    """Radio L∞ = 15 px. En euclídea, las axiales mueven 15 px y las diagonales 15·√2 ≈ 21,21 px (ChatGPT 003 b)."""
    x, y = (int(round(float(v))) for v in xy)
    return [{"id": f"d{dx:+d}{dy:+d}", "dx": dx, "dy": dy, "xy": [x + dx, y + dy],
             "linf_px": max(abs(dx), abs(dy)), "euclidean_px": round(math.hypot(dx, dy), 2)} for dx, dy in offsets]


def box_perturbations(box, image_size, step=STEP):
    """Tres familias separadas. Coordenadas de caja inclusivas: 0 ≤ x ≤ ancho−1, 0 ≤ y ≤ alto−1.

    - TRANSLATE: la caja entera se desplaza; si sale de la imagen es ``INVALID_PERTURBATION``
      (nunca se recorta, porque recortar mezclaría traslación y contracción).
    - EXPAND: cada lado sale ``step`` px; un lado que ya toca el borde de la imagen queda fijo, y se anota.
    - CONTRACT: cada lado entra ``step`` px.
    """
    width, height = image_size
    x1, y1, x2, y2 = (int(v) for v in box)
    limits = (0, 0, width - 1, height - 1)
    out = []
    for dx, dy in BOX_TRANSLATIONS:
        moved = [x1 + dx, y1 + dy, x2 + dx, y2 + dy]
        inside = moved[0] >= 0 and moved[1] >= 0 and moved[2] <= limits[2] and moved[3] <= limits[3]
        out.append({"id": f"T{dx:+d}{dy:+d}", "family": "TRANSLATE", "box": moved, "valid": inside,
                    "reason": None if inside else "INVALID_PERTURBATION: la caja trasladada sale de la imagen"})
    grown = [max(0, x1 - step), max(0, y1 - step), min(limits[2], x2 + step), min(limits[3], y2 + step)]
    fixed = [side for side, before, after, delta in (("x1", x1, grown[0], -step), ("y1", y1, grown[1], -step),
                                                     ("x2", x2, grown[2], step), ("y2", y2, grown[3], step))
             if after != before + delta]
    out.append({"id": "E15", "family": "EXPAND", "box": grown, "valid": True, "reason": None,
                "sides_fixed_at_image_border": fixed})
    shrunk = [x1 + step, y1 + step, x2 - step, y2 - step]
    ok = shrunk[0] < shrunk[2] and shrunk[1] < shrunk[3]
    out.append({"id": "C15", "family": "CONTRACT", "box": shrunk, "valid": ok,
                "reason": None if ok else "INVALID_PERTURBATION: la caja contraída queda vacía"})
    return out


# ─── fotometría ───────────────────────────────────────────────────────────────────────────────

def gray_of(rgb) -> np.ndarray:
    """Luma del preflight: media de los canales en coma flotante."""
    array = np.asarray(rgb)
    return array.astype(np.float32).mean(axis=2) if array.ndim == 3 else array.astype(np.float32)


def integral(values) -> np.ndarray:
    values = np.asarray(values, np.float64)
    out = np.zeros((values.shape[0] + 1, values.shape[1] + 1), np.float64)
    out[1:, 1:] = values.cumsum(axis=0).cumsum(axis=1)
    return out


def square_mean(table, x, y, half):
    """Media en el cuadrado (2·half+1)² centrado en (x, y); acepta arrays de centros; recorta al borde."""
    h, w = table.shape[0] - 1, table.shape[1] - 1
    x = np.asarray(x)
    y = np.asarray(y)
    x0, x1 = np.clip(x - half, 0, w), np.clip(x + half + 1, 0, w)
    y0, y1 = np.clip(y - half, 0, h), np.clip(y + half + 1, 0, h)
    total = table[y1, x1] - table[y0, x1] - table[y1, x0] + table[y0, x0]
    return total / np.maximum((x1 - x0) * (y1 - y0), 1)


def dark_map(gray, blur_radius=BLUR_RADIUS, threshold=DARK_LUMA) -> np.ndarray:
    """Material oscuro: media en caja (2r+1)² por debajo del umbral (bordes recortados)."""
    g = np.asarray(gray, np.float64)
    h, w = g.shape
    table = integral(g)
    y0 = np.clip(np.arange(h) - blur_radius, 0, h)
    y1 = np.clip(np.arange(h) + blur_radius + 1, 0, h)
    x0 = np.clip(np.arange(w) - blur_radius, 0, w)
    x1 = np.clip(np.arange(w) + blur_radius + 1, 0, w)
    total = table[y1][:, x1] - table[y0][:, x1] - table[y1][:, x0] + table[y0][:, x0]
    count = (y1 - y0)[:, None] * (x1 - x0)[None, :]
    return total / count < threshold


def patch_stats(gray, xy, radius=PATCH_RADIUS) -> dict:
    x, y = (int(round(float(v))) for v in xy)
    patch = np.asarray(gray)[max(0, y - radius):y + radius + 1, max(0, x - radius):x + radius + 1]
    return {"patch_luma_mean": round(float(patch.mean()), 1), "patch_luma_std": round(float(patch.std()), 1)}


def safe_half_map(dark_table, xs, ys, min_fraction=DARK_FRACTION_MIN, max_half=SAFE_HALF_MAX) -> np.ndarray:
    """Mayor semilado s tal que todos los cuadrados de semilado 1…s tienen ≥ min_fraction de oscuro."""
    alive = np.ones(np.broadcast(xs, ys).shape, bool)
    best = np.zeros(alive.shape, np.int32)
    for half in range(1, max_half + 1):
        alive &= square_mean(dark_table, xs, ys, half) >= min_fraction
        if not alive.any():
            break
        best[alive] = half
    return best


def select_safe_point(dark, window, holdouts, prompts, contact_box=CONTACT_BOX, grid=2):
    """Regla reproducible para un prompt nuevo en material oscuro dentro de ``window`` (semiabierta).

    Candidatos: rejilla de ``grid`` px. Restricciones: margen L∞ a ``contact_box`` ≥ 40,
    distancia a todo holdout y a todo prompt ≥ 100, cuadrado seguro ≥ 21. Se elige el mayor
    cuadrado seguro. Empates, por orden: mayor fracción oscura en ese cuadrado (el más centrado,
    porque la tolerancia del 2 % crea mesetas), mayor margen a la caja de contacto, menor y, menor x.
    """
    x1, y1, x2, y2 = window
    ys, xs = np.mgrid[y1:y2:grid, x1:x2:grid]
    table = integral(dark)
    halves = safe_half_map(table, xs, ys)
    fractions = square_mean(table, xs, ys, halves)
    best = None
    for x, y, half, fraction in zip(xs.ravel().tolist(), ys.ravel().tolist(), halves.ravel().tolist(),
                                    np.round(fractions, 6).ravel().tolist()):
        if half < SAFE_HALF_MIN:
            continue
        margin = box_margin((x, y), contact_box)
        if margin < CONTACT_MARGIN_MIN:
            continue
        if any(distance((x, y), h) < HOLDOUT_DIST_MIN for h in holdouts):
            continue
        if any(distance((x, y), p) < PROMPT_DIST_MIN for p in prompts):
            continue
        key = (-half, -fraction, -margin, y, x)
        if best is None or key < best[0]:
            best = (key, x, y, half, margin)
    if best is None:
        return None
    _, x, y, half, margin = best
    return {"xy": [x, y], "safe_half": half, "contact_margin_linf": margin}


def validate_perturbed_point(xy, image_size, holdouts, contact_box=CONTACT_BOX, dark=None,
                             owner_contact_margin_min=PERTURBED_CONTACT_MARGIN_MIN):
    """Validez de un punto perturbado. Devuelve ``(válido, motivos)``; los motivos son ``INVALID_PERTURBATION``.

    ``dark`` solo se pasa cuando el prompt base es de material oscuro (pelo, manga): entonces el
    parche perturbado debe seguir siendo oscuro. Sin ``dark`` (p. ej. P+1 sobre el overol) se exigen
    solo la imagen, la caja de contacto y los holdouts; el propietario lo confirma el auditor.
    """
    width, height = image_size
    x, y = xy
    reasons = []
    if not (0 <= x < width and 0 <= y < height):
        reasons.append("fuera de la imagen")
    else:
        if box_margin(xy, contact_box) < owner_contact_margin_min:
            reasons.append(f"a menos de {owner_contact_margin_min} px (L∞) de la caja de contacto")
        near = [round(distance(xy, h), 1) for h in holdouts if distance(xy, h) < PERTURBED_HOLDOUT_DIST_MIN]
        if near:
            reasons.append(f"a menos de {PERTURBED_HOLDOUT_DIST_MIN} px de un holdout ({min(near)} px)")
        if dark is not None:
            patch = np.asarray(dark)[max(0, y - PATCH_RADIUS):y + PATCH_RADIUS + 1,
                                     max(0, x - PATCH_RADIUS):x + PATCH_RADIUS + 1]
            fraction = float(patch.mean())
            if fraction < PERTURBED_DARK_FRACTION_MIN:
                reasons.append(f"el parche deja el material oscuro ({fraction:.2f} < {PERTURBED_DARK_FRACTION_MIN})")
    return (not reasons), [f"INVALID_PERTURBATION: {r}" for r in reasons]


# ─── métricas prerregistradas (solo informan) ─────────────────────────────────────────────────

def _crop(mask, box):
    x1, y1, x2, y2 = box
    return as_bool(mask)[y1:y2, x1:x2]


def patch_coverage(mask, xy, radius=PATCH_RADIUS) -> float:
    x, y = (int(round(float(v))) for v in xy)
    m = as_bool(mask)
    patch = m[max(0, y - radius):y + radius + 1, max(0, x - radius):x + radius + 1]
    return float(patch.mean())


def leaked(mask, points, drop_max=SENTINEL_DROP_MAX) -> list:
    """IDs de los sentinelas DROP cuyo parche cubre la máscara por encima de ``drop_max``."""
    return [sid for sid, xy in points if patch_coverage(mask, xy) > drop_max]


def ownership(target, reciprocal, box=CONTACT_BOX) -> dict:
    """¿Reclaman la chica (T) y la persona posterior (R) los mismos píxeles de la zona crítica?

    Nunca se usa para reparar T (nada de ``T − R``): solo mide.
    """
    t = _crop(target, box)
    r = _crop(reciprocal, box)
    t_px, r_px = int(t.sum()), int(r.sum())
    shared = int(np.logical_and(t, r).sum())
    if t_px == 0 or r_px == 0:
        return {"label": "NOT_EVALUABLE", "target_px": t_px, "reciprocal_px": r_px, "shared_px": shared,
                "shared_over_min": None, "shared_over_target": None, "shared_over_reciprocal": None}
    ratio = shared / min(t_px, r_px)
    if ratio <= OWNERSHIP_DISJOINT_MAX:
        label = "DISJOINT"
    elif ratio >= OWNERSHIP_SHARED_MIN:
        label = "SHARED"
    else:
        label = "MARGINAL"
    # Las dos razones direccionales evitan sobreinterpretar min(): una máscara pequeña casi
    # contenida en una enorme da una razón alta sin que la grande «reclame» la zona (ChatGPT 003 d).
    return {"label": label, "target_px": t_px, "reciprocal_px": r_px, "shared_px": shared,
            "shared_over_min": round(ratio, 4), "shared_over_target": round(shared / t_px, 4),
            "shared_over_reciprocal": round(shared / r_px, 4)}


def perturbation_stability(base, perturbed: list, drop_points=(), box=CONTACT_BOX) -> dict:
    """Estabilidad de una candidata (protocolo, índice) frente a sus perturbaciones válidas.

    - ``NOT_EVALUABLE``: no hay perturbaciones válidas;
    - ``CONFLICT``: el cribado de la otra persona (algún sentinela O* filtrado o ninguno) cambia
      entre la base y alguna perturbación: quién entra depende de 15 px;
    - ``UNSTABLE``: IoU global mínimo < 0,90;
    - ``STABLE``: en otro caso.
    """
    if not perturbed:
        return {"label": "NOT_EVALUABLE", "n": 0, "min_iou": None, "min_iou_contact": None, "o_flip": [],
                "o_coverage": {}, "o_flip_detail": []}
    def coverages(mask):
        return {sid: round(patch_coverage(mask, xy), 4) for sid, xy in drop_points}

    base_cov = coverages(base)
    base_leak = any(v > SENTINEL_DROP_MAX for v in base_cov.values())
    ious, ious_box, flips, detail = [], [], [], []
    per_perturbation = {}
    for pid, mask in perturbed:
        ious.append(mask_iou(base, mask) if (as_bool(base).any() or as_bool(mask).any()) else 1.0)
        b, m = _crop(base, box), _crop(mask, box)
        ious_box.append(mask_iou(b, m) if (b.any() or m.any()) else None)
        cov = coverages(mask)
        per_perturbation[pid] = cov
        if any(v > SENTINEL_DROP_MAX for v in cov.values()) != base_leak:
            flips.append(pid)
            # Valor continuo y distancia al umbral: distingue un cruce 0,199→0,201 de un cambio masivo.
            for sid in cov:
                if (cov[sid] > SENTINEL_DROP_MAX) != (base_cov[sid] > SENTINEL_DROP_MAX):
                    detail.append({"perturbation": pid, "sentinel": sid, "base": base_cov[sid], "perturbed": cov[sid],
                                   "distance_to_threshold": round(min(abs(base_cov[sid] - SENTINEL_DROP_MAX),
                                                                      abs(cov[sid] - SENTINEL_DROP_MAX)), 4)})
    min_iou = min(ious)
    boxed = [v for v in ious_box if v is not None]
    label = "CONFLICT" if flips else ("UNSTABLE" if min_iou < STABLE_IOU else "STABLE")
    return {"label": label, "n": len(perturbed), "min_iou": round(min_iou, 4),
            "min_iou_contact": round(min(boxed), 4) if boxed else None, "o_flip": flips,
            "o_threshold": SENTINEL_DROP_MAX, "o_coverage": {"base": base_cov, "perturbed": per_perturbation},
            "o_flip_detail": detail}


PRIORITY = ("CONFLICT", "UNSTABLE", "STABLE", "NOT_EVALUABLE")


def worst(labels) -> str:
    """Resumen de una familia: la peor etiqueta evaluable; NOT_EVALUABLE solo si todas lo son."""
    labels = list(labels)
    for label in PRIORITY:
        if label in labels:
            return label
    return "NOT_EVALUABLE"


def interpret_reciprocal(target_leaks_bun: bool, reciprocal_stability: str, ownership_label: str,
                         reciprocal_covers_bun: bool) -> str:
    """Tabla de interpretación prerregistrada (diagnóstico; nunca rechaza SAM 2)."""
    if reciprocal_stability != "STABLE" or ownership_label == "NOT_EVALUABLE":
        return "NO_INFERENCE"
    if target_leaks_bun:
        if ownership_label == "SHARED":
            return "OWNERSHIP_AMBIGUOUS"             # las dos consultas reclaman los mismos píxeles
        if ownership_label == "DISJOINT" and not reciprocal_covers_bun:
            return "BUN_ATTRIBUTED_TO_TARGET_BY_BOTH"  # ni pidiendo a la posterior se lleva su moño
        return "MIXED"
    if ownership_label == "DISJOINT":
        return "SEPARATION_CONSISTENT_BOTH_WAYS"
    return "MIXED"


def reciprocal_stability(seed_masks: list, girl_points=(), box=CONTACT_BOX) -> dict:
    """Las 3 semillas R-corrections: IoU por pares dentro de la caja de contacto.

    Orden de etiquetas: ``NOT_EVALUABLE`` (alguna vacía en la caja) > ``CONFLICT`` (el cribado K*,
    la chica dentro de R, cambia entre semillas) > ``UNSTABLE`` (IoU mínimo < 0,90) > ``STABLE``.
    """
    crops = [_crop(m, box) for _, m in seed_masks]
    if any(not c.any() for c in crops):
        return {"label": "NOT_EVALUABLE", "pairs": {}, "min_iou": None, "k_leak": {}}
    pairs = {}
    for i in range(len(seed_masks)):
        for j in range(i + 1, len(seed_masks)):
            pairs[f"{seed_masks[i][0]} ↔ {seed_masks[j][0]}"] = round(mask_iou(crops[i], crops[j]), 4)
    k_leak = {sid: bool(leaked(m, girl_points)) for sid, m in seed_masks}
    min_iou = min(pairs.values()) if pairs else 1.0
    if len(set(k_leak.values())) > 1:
        label = "CONFLICT"
    elif min_iou < STABLE_IOU:
        label = "UNSTABLE"
    else:
        label = "STABLE"
    return {"label": label, "pairs": pairs, "min_iou": min_iou, "k_leak": k_leak}


def reference_mask(seed_masks: list, posterior_points=()) -> str:
    """R_ref: la semilla con más sentinelas O* cubiertos (≥ 0,80); empate → la primera en orden."""
    def covered(mask):
        return sum(patch_coverage(mask, xy) >= SENTINEL_KEEP_MIN for _, xy in posterior_points)
    best = max(range(len(seed_masks)), key=lambda i: (covered(seed_masks[i][1]), -i))
    return seed_masks[best][0]


# ─── plan de llamadas (contrato ejecutable del prerregistro) ──────────────────────────────────

def build_call_plan(base_prompts: dict, new_prompts: dict, box, perturb_point: dict, perturb_box: list) -> list:
    """Todas las llamadas a ``SAM2ImagePredictor.predict`` de v1.3, en orden de ejecución.

    ``mask_input_from`` apunta a una llamada anterior: se usa ``low_res_logits[index][None]`` de esa
    llamada, con ``multimask_output=False``, exactamente como v1.2.
    """
    P = dict(base_prompts)
    P.update(new_prompts)
    negatives = ["P-1", "P-2", "P-3"]
    calls = []

    def add(call_id, branch, protocol, point_ids, labels, use_box=None, seed=None, multimask=False, xy=None, **extra):
        points = [list(xy.get(pid, P.get(pid))) if xy else list(P[pid]) for pid in point_ids]
        n = 3 if multimask else 1
        suffix = [str(i) for i in range(n)] if multimask else [call_id.rsplit("|", 1)[1]]
        base_id = call_id if multimask else call_id.rsplit("|", 1)[0]
        calls.append({"call_id": call_id, "branch": branch, "protocol": protocol, **extra,
                      "point_ids": list(point_ids), "points": points, "labels": list(labels),
                      "box": list(use_box) if use_box is not None else None,
                      "mask_input_from": seed, "multimask_output": multimask,
                      "candidates": [f"{base_id}|{k}" for k in suffix]})

    def corrections(prefix, branch, extra_pos, seed_prefix, use_box=None, xy=None, **extra):
        protocol = "box+corrections" if use_box is not None else "point+corrections"
        ids = ["P+1"] + list(extra_pos) + negatives
        labels = [1] * (1 + len(extra_pos)) + [0] * len(negatives)
        for k in range(3):
            add(f"{prefix}|{protocol}|s{k}", branch, protocol, ids, labels, use_box=use_box,
                seed={"call_id": seed_prefix, "index": k}, xy=xy, **extra)

    # BASE: réplica exacta de v1.2
    add("BASE|point", "BASE", "point", ["P+1"], [1], multimask=True)
    add("BASE|box", "BASE", "box", [], [], use_box=box, multimask=True)
    corrections("BASE", "BASE", [], "BASE|point")
    corrections("BASE", "BASE", [], "BASE|box", use_box=box)
    # +POS: solo cambia la llamada de corrección; semillas de BASE
    for branch, extra_pos in (("+POS_HAIR", ["H1"]), ("+POS_SLEEVE", ["S1"]), ("+POS_HAIR+SLEEVE", ["H1", "S1"])):
        corrections(branch, branch, extra_pos, "BASE|point")
        corrections(branch, branch, extra_pos, "BASE|box", use_box=box)
    # RECIPROCAL_POSTERIOR
    add("RECIPROCAL|R-point", "RECIPROCAL_POSTERIOR", "R-point", ["P-1"], [1], multimask=True)
    for k in range(3):
        add(f"RECIPROCAL|R-corrections|s{k}", "RECIPROCAL_POSTERIOR", "R-corrections",
            ["P-1", "P-2", "P-3", "P+1", "H1", "S1"], [1, 1, 1, 0, 0, 0],
            seed={"call_id": "RECIPROCAL|R-point", "index": k})
    # PERTURB_POINT: P+1 en toda la cadena point; H1 o S1 en +POS_HAIR+SLEEVE (uno cada vez)
    for row in perturb_point["P+1"]:
        if not row["valid"]:
            continue
        prefix = f"PERTURB_POINT|P+1|{row['id']}"
        xy = {"P+1": row["xy"]}
        add(f"{prefix}|point", "PERTURB_POINT", "point", ["P+1"], [1], multimask=True, xy=xy,
            target="P+1", perturbation=row["id"])
        corrections(prefix, "PERTURB_POINT", [], f"{prefix}|point", xy=xy, target="P+1", perturbation=row["id"])
    for target in ("H1", "S1"):
        for row in perturb_point[target]:
            if not row["valid"]:
                continue
            prefix = f"PERTURB_POINT|{target}|{row['id']}"
            xy = {target: row["xy"]}
            corrections(prefix, "PERTURB_POINT", ["H1", "S1"], "BASE|point", xy=xy, target=target, perturbation=row["id"])
            corrections(prefix, "PERTURB_POINT", ["H1", "S1"], "BASE|box", use_box=box, xy=xy,
                        target=target, perturbation=row["id"])
    # PERTURB_BOX: la caja perturbada en toda la cadena box
    for row in perturb_box:
        if not row["valid"]:
            continue
        prefix = f"PERTURB_BOX|{row['id']}"
        add(f"{prefix}|box", "PERTURB_BOX", "box", [], [], use_box=row["box"], multimask=True,
            family=row["family"], perturbation=row["id"])
        corrections(prefix, "PERTURB_BOX", [], f"{prefix}|box", use_box=row["box"],
                    family=row["family"], perturbation=row["id"])
    ids = [c["call_id"] for c in calls]
    assert len(ids) == len(set(ids)), "call_id repetido"
    seen = set()
    for c in calls:
        if c["mask_input_from"] is not None:
            assert c["mask_input_from"]["call_id"] in seen, f"semilla posterior a su uso: {c['call_id']}"
        seen.add(c["call_id"])
    return calls


# ─── hipótesis prerregistradas (se evalúan después del desciegue) ─────────────────────────────

def _both(judgments, cid, field):
    return all(judgments[key][cid].get(field) == "TRUE" for key in judgments)


def _both_false(judgments, cid, field):
    return all(judgments[key][cid].get(field) == "FALSE" for key in judgments)


def _pos(branch):
    return [f"{branch}|{p}|s{k}" for p in ("point+corrections", "box+corrections") for k in range(3)]


def hypothesis_h_c1(judgments, leaks_bun) -> str:
    """H-C1 (Claude): +POS_HAIR recupera el pelo pero arrastra el moño."""
    cands = _pos("+POS_HAIR")
    hair = [c for c in cands if _both(judgments, c, "target_hair_included")]
    drags = [c for c in hair if _both_false(judgments, c, "other_person_excluded") or leaks_bun[c]]
    clean = [c for c in hair if _both(judgments, c, "other_person_excluded") and not leaks_bun[c]]
    if len(drags) >= 4:
        return "HOLDS"
    if len(clean) >= 4:
        return "REFUTED"
    return "INDETERMINATE"


def hypothesis_h_c2(stability_labels: list) -> str:
    """H-C2 (Claude): P+1 perturbado no es STABLE en point (3 salidas)."""
    if any(label in ("UNSTABLE", "CONFLICT") for label in stability_labels):
        return "HOLDS"
    if stability_labels and all(label == "STABLE" for label in stability_labels):
        return "REFUTED"
    return "INDETERMINATE"


def hypothesis_h_g1(judgments, consensus, base_reference) -> str:
    """H-G1 (ChatGPT): S1 recupera mangas sin empeorar la exclusión de la persona posterior."""
    cands = _pos("+POS_SLEEVE")
    sleeves = sum(_both(judgments, c, "target_dark_sleeves_included") for c in cands)
    worse = sum(base_reference[c.replace("+POS_SLEEVE", "BASE", 1)]["other_person_excluded"] == "TRUE"
                and consensus[c]["other_person_excluded"] == "FALSE" for c in cands)
    if sleeves >= 4 and worse <= 2:
        return "HOLDS"
    if len(cands) - sleeves >= 4 or worse >= 4:
        return "REFUTED"
    return "INDETERMINATE"


def hypothesis_h_g2(reciprocal_label: str) -> str:
    """H-G2 (ChatGPT): el recíproco no cambia de propietario grueso entre semillas."""
    return {"STABLE": "HOLDS", "UNSTABLE": "HOLDS", "CONFLICT": "REFUTED"}.get(reciprocal_label, "INDETERMINATE")


def hypothesis_h_g3(reciprocal_label: str, reciprocal_covers_bun: bool, leaks_bun: dict, ownership_labels: dict) -> str:
    """H-G3 (ChatGPT): la región del moño se reclama desde las dos consultas."""
    if reciprocal_label == "NOT_EVALUABLE":
        return "INDETERMINATE"
    leaking = [c for c, v in leaks_bun.items() if v]
    if reciprocal_covers_bun and any(ownership_labels[c] == "SHARED" for c in leaking):
        return "HOLDS"
    if reciprocal_covers_bun and leaking and all(ownership_labels[c] == "DISJOINT" for c in leaking):
        return "REFUTED"
    return "INDETERMINATE"


def hypothesis_h_g4(judgments) -> str:
    """H-G4 (ChatGPT): +POS_HAIR+SLEEVE recupera a la vez pelo y mangas en al menos una candidata."""
    hits = sum(_both(judgments, c, "target_hair_included") and _both(judgments, c, "target_dark_sleeves_included")
               for c in _pos("+POS_HAIR+SLEEVE"))
    return "HOLDS" if hits >= 1 else "REFUTED"
