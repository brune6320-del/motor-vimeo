"""Comprobación geométrica entre dos llaves de máscara (A‑E0, DEC‑025, a partir de ChatGPT 008).

Reparto de trabajo:
- el código dice **que** dos máscaras difieren, **dónde** y **cuánto**;
- la revisión (IA o humana) adjudica **qué significa** cada diferencia.

La motivación es A‑E(−1) v1.4: las dos llaves visuales fallaron con una isla de 3–5 px (FP diminuto) y
con miles de píxeles ausentes abiertos al exterior (FN abierto), que un detector de agujeros cerrados
no ve.

Definiciones (A y B son las máscaras de las dos llaves, del mismo tamaño):
- ``A_ONLY = A & ~B``, ``B_ONLY = B & ~A``, ``XOR = A_ONLY | B_ONLY``, ``consenso = A & B``.
- **Tolerancia de frontera** ``t`` (px): un tramo de ``A_ONLY`` o ``B_ONLY`` en el que no cabe un
  cuadrado de ``(2t+1)²`` es desacuerdo de trazo, no semántico.
  - ``THICK``: componente 4‑conexa de la apertura morfológica ``open(lado, t)``.
  - ``ISLAND``: componente del lado sin nada de la apertura y **sin contacto** con el consenso
    (vecindad 8), de cualquier tamaño. Una isla de 3 px sobre otra persona no desaparece por fina.
  - ``thin``: el resto del XOR, que pasa automáticamente a ``uncertain``.
  - Cada píxel del XOR cae exactamente en uno de los tres grupos.
- **Qué exige adjudicación** (``requires_adjudication``): toda ``ISLAND``, sea del tamaño que sea, y
  todo ``THICK`` de ``area_px`` ≥ ``MIN_ADJUDICATE_PX``. Un ``THICK`` pegado más pequeño se lista
  igual, pero si nadie lo adjudica pasa a ``uncertain`` por la regla de la línea media.
- Campos de cada componente:
  - ``missing_from``: la llave que no incluye la región;
  - ``touches_image_border``: toca el marco de la foto;
  - ``touches_mask_exterior``: es vecina (8) del exterior común, la parte de ``~(A|B)`` conectada
    con el marco. La diferencia está en la silueta y no dentro del objeto;
  - ``open_or_enclosed``: ``ENCLOSED`` si en la llave que no la incluye la región cae dentro de un
    agujero cerrado (un detector de agujeros la vería), y ``OPEN`` si está conectada con su exterior
    (el caso N04, que ese detector no ve);
  - ``touches_consensus``: vecina (8) del consenso;
  - ``semantic_adjudication``: lo rellena la revisión y nunca el código.

Adjudicación: ``INCLUDE`` · ``EXCLUDE`` · ``UNCERTAIN_INCLUDE`` · ``UNCERTAIN_EXCLUDE``. Las dos últimas
van a ``uncertain_mask`` con un valor binario de mejor estimación, que es el que usa
``metric_all_pixels``.
"""

from __future__ import annotations

import numpy as np

from .masks import as_bool, dilate_square, mask_bbox, mask_iou

TOLERANCE_PX = 2
MIN_ADJUDICATE_PX = 100
ADJUDICATIONS = ("INCLUDE", "EXCLUDE", "UNCERTAIN_INCLUDE", "UNCERTAIN_EXCLUDE")


def labels(mask) -> np.ndarray:
    """Etiquetas 4‑conexas por corridas (sin SciPy); 0 = fuera. Numeradas por orden de aparición."""
    m = as_bool(mask)
    h, w = m.shape
    parent, runs, previous = [], [], []

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for y in range(h):
        row = np.concatenate(([False], m[y], [False]))
        change = np.flatnonzero(row[1:] != row[:-1])
        current, pointer = [], 0
        for start, end in zip(change[0::2].tolist(), change[1::2].tolist()):
            index = len(parent)
            parent.append(index)
            runs.append((y, start, end, index))
            while pointer < len(previous) and previous[pointer][2] <= start:
                pointer += 1
            scan = pointer
            while scan < len(previous) and previous[scan][1] < end:
                a, b = find(index), find(previous[scan][0])
                if a != b:
                    parent[max(a, b)] = min(a, b)
                scan += 1
            current.append((index, start, end))
        previous = current
    label = np.zeros((h, w), np.int32)
    roots = {}
    for y, start, end, index in runs:
        label[y, start:end] = roots.setdefault(find(index), len(roots) + 1)
    return label


def _border_labels(label) -> set:
    edge = np.concatenate((label[0], label[-1], label[:, 0], label[:, -1]))
    return set(np.unique(edge[edge > 0]).tolist())


def exterior(mask) -> np.ndarray:
    """Parte de ``~mask`` conectada (4) con el marco de la imagen."""
    label = labels(~as_bool(mask))
    border = _border_labels(label)
    return np.isin(label, list(border)) if border else np.zeros(label.shape, bool)


def erode_square(mask, radius: int) -> np.ndarray:
    """Erosión con cuadrado (2r+1)²; fuera de la imagen cuenta como vacío."""
    m = as_bool(mask)
    if radius <= 0:
        return m.copy()
    padded = np.ones((m.shape[0] + 2 * radius, m.shape[1] + 2 * radius), bool)
    padded[radius:-radius, radius:-radius] = ~m
    return ~dilate_square(padded, radius)[radius:-radius, radius:-radius]


def opening(mask, radius: int) -> np.ndarray:
    """Apertura con cuadrado (2r+1)²: lo que queda donde cabe el cuadrado entero."""
    return dilate_square(erode_square(mask, radius), radius) & as_bool(mask)


def _label_boxes(label) -> dict:
    """Caja semiabierta de cada etiqueta > 0."""
    ys, xs = np.nonzero(label)
    ids = label[ys, xs]
    n = int(label.max())
    x1 = np.full(n + 1, label.shape[1]); y1 = np.full(n + 1, label.shape[0])
    x2 = np.zeros(n + 1, int); y2 = np.zeros(n + 1, int)
    np.minimum.at(x1, ids, xs); np.minimum.at(y1, ids, ys)
    np.maximum.at(x2, ids, xs + 1); np.maximum.at(y2, ids, ys + 1)
    return {k: (int(x1[k]), int(y1[k]), int(x2[k]), int(y2[k])) for k in range(1, n + 1)}


def _grow(box, shape, pad=1):
    x1, y1, x2, y2 = box
    return (max(0, x1 - pad), max(0, y1 - pad), min(shape[1], x2 + pad), min(shape[0], y2 + pad))


def _record(cid, side, missing_from, kind, box, crop, region, ctx, min_adjudicate_px):
    """Campos de un componente; ``region`` es su máscara dentro de ``crop`` (caja +1 px)."""
    cx1, cy1, cx2, cy2 = crop
    x1, y1, x2, y2 = box
    h, w = ctx["shape"]
    near = dilate_square(region, 1)
    lacking = ctx["lacking"][missing_from][cy1:cy2, cx1:cx2][region]
    return {
        "id": cid,
        "side": side,
        "missing_from": missing_from,
        "kind": kind,
        "area_px": int(region.sum()),
        "bbox": [x1, y1, x2, y2],
        "touches_image_border": x1 == 0 or y1 == 0 or x2 == w or y2 == h,
        "touches_mask_exterior": bool((near & ctx["exterior"][cy1:cy2, cx1:cx2]).any()),
        "open_or_enclosed": "OPEN" if set(np.unique(lacking).tolist()) & ctx["lacking_border"][missing_from] else "ENCLOSED",
        "touches_consensus": bool((near & ctx["consensus"][cy1:cy2, cx1:cx2]).any()),
        "requires_adjudication": kind == "ISLAND" or int(region.sum()) >= min_adjudicate_px,
        "semantic_adjudication": None,
    }


def compare_keys(a, b, tolerance_px: int = TOLERANCE_PX, min_adjudicate_px: int = MIN_ADJUDICATE_PX) -> dict:
    """Compara dos llaves y enumera cada diferencia que la revisión debe adjudicar.

    Devuelve ``{"summary", "components", "masks"}``. ``masks`` (no serializable) trae ``a_only``,
    ``b_only``, ``thin``, ``consensus`` y, por id, ``(recorte, máscara del recorte)`` de cada
    componente, para la lámina y para ``compose_reference``.
    """
    a, b = as_bool(a), as_bool(b)
    if a.shape != b.shape:
        raise ValueError(f"Las llaves tienen tamaños distintos: {a.shape} y {b.shape}")
    consensus = a & b
    lacking = {"A": labels(~a), "B": labels(~b)}
    ctx = {"shape": a.shape, "consensus": consensus, "exterior": exterior(a | b), "lacking": lacking,
           "lacking_border": {key: _border_labels(value) for key, value in lacking.items()}}
    near_consensus = dilate_square(consensus, 1)
    components, regions = [], {}
    thin = np.zeros(a.shape, bool)
    for side, missing_from, prefix, diff in (("A_ONLY", "B", "A", a & ~b), ("B_ONLY", "A", "B", b & ~a)):
        core_label = labels(opening(diff, tolerance_px))
        diff_label = labels(diff)
        found = [("THICK", core_label, k, box) for k, box in _label_boxes(core_label).items()]
        excluded = set(np.unique(diff_label[core_label > 0]).tolist())
        excluded |= set(np.unique(diff_label[near_consensus & diff]).tolist())
        found += [("ISLAND", diff_label, k, box) for k, box in _label_boxes(diff_label).items() if k not in excluded]
        cropped = []
        for kind, label, k, box in found:
            crop = _grow(box, a.shape)
            region = label[crop[1]:crop[3], crop[0]:crop[2]] == k
            cropped.append((int(region.sum()), box, kind, crop, region))
        cropped.sort(key=lambda item: (-item[0], item[1]))
        claimed = np.zeros(a.shape, bool)
        for number, (_, box, kind, crop, region) in enumerate(cropped, 1):
            cid = f"{prefix}{number}"
            components.append(_record(cid, side, missing_from, kind, box, crop, region, ctx, min_adjudicate_px))
            regions[cid] = (crop, region)
            claimed[crop[1]:crop[3], crop[0]:crop[2]] |= region
        thin |= diff & ~claimed
    a_only, b_only = a & ~b, b & ~a
    summary = {
        "shape": list(a.shape),
        "tolerance_px": int(tolerance_px),
        "min_adjudicate_px": int(min_adjudicate_px),
        "area_a": int(a.sum()),
        "area_b": int(b.sum()),
        "iou": round(mask_iou(a, b), 6),
        "consensus_px": int(consensus.sum()),
        "xor_px": int((a_only | b_only).sum()),
        "a_only_px": int(a_only.sum()),
        "b_only_px": int(b_only.sum()),
        "adjudicable_px": int(sum(c["area_px"] for c in components)),
        "thin_px": int(thin.sum()),
        "n_thick": sum(c["kind"] == "THICK" for c in components),
        "n_island": sum(c["kind"] == "ISLAND" for c in components),
        "n_open": sum(c["open_or_enclosed"] == "OPEN" for c in components),
        "n_requires_adjudication": sum(c["requires_adjudication"] for c in components),
        "auto_uncertain_px": int(sum(c["area_px"] for c in components if not c["requires_adjudication"])),
    }
    if summary["adjudicable_px"] + summary["thin_px"] != summary["xor_px"]:
        raise AssertionError("La partición del XOR no cuadra")
    return {"summary": summary, "components": components,
            "masks": {"a_only": a_only, "b_only": b_only, "thin": thin, "consensus": consensus,
                      "components": regions}}


def _paste(target, crop, region):
    x1, y1, x2, y2 = crop
    target[y1:y2, x1:x2] |= region


def compose_reference(diff: dict, adjudications: dict, tolerance_px: int | None = None) -> dict:
    """Referencia de tres estados a partir del consenso y de las adjudicaciones.

    - Consenso → primer plano. Fuera de A y de B → fondo.
    - Cada componente con ``requires_adjudication`` exige una adjudicación: sin eso no hay
      referencia (nada se decide en silencio).
    - ``thin`` y los ``THICK`` pequeños sin adjudicar → ``uncertain``. Su valor binario de mejor
      estimación es la línea media: un píxel es primer plano si está a ≤ t px (Chebyshev) del consenso.
    """
    t = diff["summary"]["tolerance_px"] if tolerance_px is None else tolerance_px
    masks = diff["masks"]
    missing = [c["id"] for c in diff["components"] if c["requires_adjudication"] and c["id"] not in adjudications]
    if missing:
        raise ValueError(f"Faltan adjudicaciones: {missing}")
    bad = {k: v for k, v in adjudications.items() if v not in ADJUDICATIONS}
    if bad:
        raise ValueError(f"Adjudicación no válida: {bad}")
    foreground = masks["consensus"].copy()
    uncertain = masks["thin"].copy()
    midline = dilate_square(masks["consensus"], t)
    foreground |= masks["thin"] & midline
    for c in diff["components"]:
        crop, region = masks["components"][c["id"]]
        if c["id"] not in adjudications:
            x1, y1, x2, y2 = crop
            _paste(uncertain, crop, region)
            _paste(foreground, crop, region & midline[y1:y2, x1:x2])
            continue
        verdict = adjudications[c["id"]]
        if verdict in ("INCLUDE", "UNCERTAIN_INCLUDE"):
            _paste(foreground, crop, region)
        if verdict.startswith("UNCERTAIN"):
            _paste(uncertain, crop, region)
    total = foreground.size
    return {"mask": foreground, "uncertain_mask": uncertain,
            "uncertain_area_px": int(uncertain.sum()),
            "uncertain_fraction": round(float(uncertain.sum()) / total, 8)}


def masked_iou(pred, ref, uncertain=None) -> dict:
    """IoU contra la referencia en todos los píxeles y, si hay zona incierta, también sin ella."""
    pred, ref = as_bool(pred), as_bool(ref)
    out = {"metric_all_pixels": round(mask_iou(pred, ref), 6)}
    if uncertain is not None:
        keep = ~as_bool(uncertain)
        out["metric_excluding_uncertain"] = round(mask_iou(pred & keep, ref & keep), 6)
        out["uncertain_area_px"] = int((~keep).sum())
        out["uncertain_fraction"] = round(float((~keep).sum()) / keep.size, 8)
    return out


def public_report(diff: dict) -> dict:
    """Parte serializable (sin máscaras): cifras, cajas y banderas."""
    return {"summary": diff["summary"], "components": diff["components"]}


def diff_sheet(photo, a, b, diff: dict, out_path, box=None, max_width=1500, zoom_limit=12):
    """Lámina de adjudicación: original · contorno A · contorno B · XOR direccional, más un zoom por
    componente. A_ONLY en magenta, B_ONLY en cian, ``thin`` en gris.
    """
    from PIL import Image, ImageDraw

    rgb = np.asarray(photo)[..., :3]
    a, b = as_bool(a), as_bool(b)
    h, w = a.shape
    if box is None:
        x1, y1, x2, y2 = mask_bbox(a | b) or (0, 0, w, h)
        box = (max(0, x1 - 60), max(0, y1 - 60), min(w, x2 + 60), min(h, y2 + 60))

    def outline(mask):
        return mask & ~erode_square(mask, 1)

    def render(kind, crop):
        x1, y1, x2, y2 = crop
        base = rgb[y1:y2, x1:x2].astype(np.float32)
        if kind == "original":
            return Image.fromarray(base.astype(np.uint8))
        out = base * 0.45
        if kind in ("A", "B"):
            m = (a if kind == "A" else b)[y1:y2, x1:x2]
            out[m] = base[m]
            out[dilate_square(outline(m), 1)] = (255, 0, 255) if kind == "A" else (0, 255, 255)
        else:
            masks = diff["masks"]
            out[masks["a_only"][y1:y2, x1:x2]] = (255, 0, 255)
            out[masks["b_only"][y1:y2, x1:x2]] = (0, 255, 255)
            out[masks["thin"][y1:y2, x1:x2]] = (150, 150, 150)
        return Image.fromarray(out.clip(0, 255).astype(np.uint8))

    panels = [(name, render(kind, box)) for name, kind in
              (("original", "original"), ("contorno A", "A"), ("contorno B", "B"), ("A_ONLY · B_ONLY · thin", "xor"))]
    scale = min(1.0, max_width / (2 * panels[0][1].width))
    panels = [(n, p.resize((max(1, round(p.width * scale)), max(1, round(p.height * scale))), Image.LANCZOS))
              for n, p in panels]
    draw = ImageDraw.Draw(panels[3][1])
    for c in diff["components"]:
        cx = ((c["bbox"][0] + c["bbox"][2]) / 2 - box[0]) * scale
        cy = ((c["bbox"][1] + c["bbox"][3]) / 2 - box[1]) * scale
        draw.text((cx + 4, cy - 6), c["id"], fill=(255, 255, 0))
    zooms = []
    for c in diff["components"][:zoom_limit]:
        x1, y1, x2, y2 = c["bbox"]
        pad = max(24, (x2 - x1 + y2 - y1) // 4)
        crop = (max(0, x1 - pad), max(0, y1 - pad), min(w, x2 + pad), min(h, y2 + pad))
        tile = render("xor", crop)
        factor = max(1, min(8, 240 // max(tile.width, tile.height, 1)))
        tile = tile.resize((tile.width * factor, tile.height * factor), Image.NEAREST)
        if tile.width > 480 or tile.height > 480:
            tile.thumbnail((480, 480), Image.LANCZOS)
        label = f"{c['id']} {c['kind']} {c['area_px']} px {c['open_or_enclosed']}"
        zooms.append((label, tile))
    rows = [panels[:2], panels[2:]] + [zooms[i:i + 4] for i in range(0, len(zooms), 4)]
    header, gap = 22, 8
    sizes = [(sum(t.width for _, t in row) + gap * (len(row) - 1), max(t.height for _, t in row) + header)
             for row in rows]
    sheet = Image.new("RGB", (max(s[0] for s in sizes), sum(s[1] for s in sizes) + gap * len(rows)), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    y = 0
    for row, (_, height) in zip(rows, sizes):
        x = 0
        for name, tile in row:
            draw.text((x + 2, y + 4), name, fill=(235, 235, 235))
            sheet.paste(tile, (x, y + header))
            x += tile.width + gap
        y += height + gap
    sheet.save(out_path, quality=90)
    return out_path
