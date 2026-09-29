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
  igual, pero si nadie lo adjudica pasa a ``uncertain``.
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

Adjudicación: ``INCLUDE`` · ``EXCLUDE`` · ``UNCERTAIN_INCLUDE`` · ``UNCERTAIN_EXCLUDE``.

Tres estados (ChatGPT 009): ``foreground``, ``background`` y ``uncertain``. Dentro de ``uncertain``
no se inventa verdad:
- La máscara binaria se llama ``reference_estimate_mask``. Es un **estimador** con política declarada
  (``MIDLINE`` por defecto, ``INTERSECTION`` o ``UNION``), y lo que se mide contra ella se llama
  ``metric_all_pixels_estimate``.
- Toda métrica lleva sus **cotas exactas** sobre cualquier asignación de lo incierto:
  ``metric_all_pixels_min`` y ``metric_all_pixels_max``. Además se reportan
  ``metric_excluding_uncertain``, ``uncertain_area_px`` y ``uncertain_fraction``.

La omisión compartida (lo que las dos llaves dejan fuera igual) no aparece en el XOR. Para eso están
``contour_tiles``: teselas 1:1 sobre todo el contorno de la referencia compuesta, con las zonas de
desafío marcadas para la tercera revisión dirigida.
"""

from __future__ import annotations

import numpy as np

from .masks import as_bool, dilate_square, mask_bbox, mask_iou

TOLERANCE_PX = 2
MIN_ADJUDICATE_PX = 100
ADJUDICATIONS = ("INCLUDE", "EXCLUDE", "UNCERTAIN_INCLUDE", "UNCERTAIN_EXCLUDE")
ESTIMATE_POLICIES = ("MIDLINE", "INTERSECTION", "UNION")
MIDLINE_MAX_PX = 64
CONTOUR_TILE_PX = 512
CONTOUR_TILE_OVERLAP_PX = 64


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


def midline_estimate(consensus, background, targets, max_px: int = MIDLINE_MAX_PX) -> np.ndarray:
    """Línea media real entre las dos fronteras, evaluada solo en ``targets``.

    Un píxel objetivo es primer plano si está más cerca (Chebyshev) del consenso ``A & B`` que del
    fondo común ``~A & ~B``. Si está a la misma distancia de los dos, decide un tablero fijo
    (``(x + y)`` par → primer plano), que no favorece a ninguna llave ni sesga el área. Si no llega
    a ninguno de los dos en ``max_px`` px, queda como fondo.
    """
    t = as_bool(targets)
    out = np.zeros(t.shape, bool)
    box = mask_bbox(t)
    if box is None:
        return out
    h, w = t.shape
    x1, y1 = max(0, box[0] - max_px), max(0, box[1] - max_px)
    x2, y2 = min(w, box[2] + max_px), min(h, box[3] + max_px)
    pending = t[y1:y2, x1:x2].copy()
    fg = as_bool(consensus)[y1:y2, x1:x2]
    bg = as_bool(background)[y1:y2, x1:x2]
    even = (np.arange(y1, y2)[:, None] + np.arange(x1, x2)[None, :]) % 2 == 0
    result = np.zeros(pending.shape, bool)
    for _ in range(max_px):
        if not pending.any():
            break
        fg, bg = dilate_square(fg, 1), dilate_square(bg, 1)
        hit_fg, hit_bg = pending & fg, pending & bg
        result |= (hit_fg & ~hit_bg) | (hit_fg & hit_bg & even)
        pending &= ~(hit_fg | hit_bg)
    out[y1:y2, x1:x2] = result
    return out


def compose_reference(diff: dict, adjudications: dict, estimate_policy: str = "MIDLINE") -> dict:
    """Referencia de tres estados a partir del consenso y de las adjudicaciones.

    - Consenso → primer plano. Fuera de A y de B → fondo.
    - Cada componente con ``requires_adjudication`` exige una adjudicación: sin eso no hay
      referencia (nada se decide en silencio).
    - ``thin`` y los ``THICK`` pequeños sin adjudicar → ``uncertain``. Su valor en
      ``reference_estimate_mask`` sale de ``estimate_policy``, que queda registrada:
      - ``MIDLINE``: ``midline_estimate``;
      - ``INTERSECTION``: fondo;
      - ``UNION``: primer plano.
    - ``UNCERTAIN_INCLUDE`` y ``UNCERTAIN_EXCLUDE`` → ``uncertain``, con el valor que dio la
      adjudicación.
    """
    if estimate_policy not in ESTIMATE_POLICIES:
        raise ValueError(f"Política de estimación no válida: {estimate_policy}")
    masks = diff["masks"]
    missing = [c["id"] for c in diff["components"] if c["requires_adjudication"] and c["id"] not in adjudications]
    if missing:
        raise ValueError(f"Faltan adjudicaciones: {missing}")
    bad = {k: v for k, v in adjudications.items() if v not in ADJUDICATIONS}
    if bad:
        raise ValueError(f"Adjudicación no válida: {bad}")
    estimate = masks["consensus"].copy()
    uncertain = np.zeros(estimate.shape, bool)
    auto = masks["thin"].copy()
    for c in diff["components"]:
        crop, region = masks["components"][c["id"]]
        verdict = adjudications.get(c["id"])
        if verdict is None:
            _paste(auto, crop, region)
            continue
        if verdict in ("INCLUDE", "UNCERTAIN_INCLUDE"):
            _paste(estimate, crop, region)
        if verdict.startswith("UNCERTAIN"):
            _paste(uncertain, crop, region)
    uncertain |= auto
    if estimate_policy == "UNION":
        estimate |= auto
    elif estimate_policy == "MIDLINE":
        background = ~(masks["consensus"] | masks["a_only"] | masks["b_only"])
        estimate |= midline_estimate(masks["consensus"], background, auto)
    return {"reference_estimate_mask": estimate, "uncertain_mask": uncertain,
            "estimate_policy": estimate_policy,
            "certain_foreground_px": int((estimate & ~uncertain).sum()),
            "uncertain_area_px": int(uncertain.sum()),
            "uncertain_fraction": round(float(uncertain.sum()) / uncertain.size, 8)}


def iou_with_uncertainty(pred, estimate, uncertain) -> dict:
    """IoU contra una referencia de tres estados, con sus cotas exactas (ChatGPT 009).

    Con P = predicción, F = primer plano cierto (``estimate & ~uncertain``) y U = incierto:
    - máximo (U a favor de P): ``(|P∩F| + |P∩U|) / |P∪F|``;
    - mínimo (U en contra de P): ``|P∩F| / (|P∪F| + |U∖P|)``.
    Unión vacía → 0, como ``mask_iou``.
    """
    p, e, u = as_bool(pred), as_bool(estimate), as_bool(uncertain)
    f = e & ~u
    pf, pu = int((p & f).sum()), int((p & u).sum())
    p_or_f, u_out = int((p | f).sum()), int((u & ~p).sum())
    return {
        "metric_all_pixels_estimate": round(mask_iou(p, e), 6),
        "metric_all_pixels_min": round(pf / (p_or_f + u_out), 6) if p_or_f + u_out else 0.0,
        "metric_all_pixels_max": round((pf + pu) / p_or_f, 6) if p_or_f else 0.0,
        "metric_excluding_uncertain": round(mask_iou(p & ~u, e & ~u), 6),
        "uncertain_area_px": int(u.sum()),
        "uncertain_fraction": round(float(u.sum()) / u.size, 8),
    }


def _inner_contour(mask) -> np.ndarray:
    """Píxeles de la máscara con algún vecino (8) fuera de ella dentro de la foto; el marco no cuenta."""
    m = as_bool(mask)
    padded = np.ones((m.shape[0] + 2, m.shape[1] + 2), bool)
    padded[1:-1, 1:-1] = m
    return m & dilate_square(~padded, 1)[1:-1, 1:-1]


def _overlap(a, b) -> bool:
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def contour_tiles(reference, uncertain=None, zones=None, size: int = CONTOUR_TILE_PX,
                  overlap: int = CONTOUR_TILE_OVERLAP_PX) -> list:
    """Teselas 1:1 que cubren todo el contorno de la referencia compuesta (omisión compartida).

    ``zones`` = {nombre: [cajas]} de alto riesgo (pelo, contacto, manos, objetos sostenidos). Una
    tesela es de desafío si toca ``uncertain`` o alguna zona; solo esas van a la tercera revisión
    dirigida, que no sabe qué decidió cada llave.
    """
    edge = _inner_contour(reference)
    h, w = edge.shape
    unc = as_bool(uncertain) if uncertain is not None else None
    step = max(1, size - overlap)
    tiles = []
    for y in range(0, max(1, h - overlap), step):
        for x in range(0, max(1, w - overlap), step):
            box = (x, y, min(w, x + size), min(h, y + size))
            n = int(edge[box[1]:box[3], box[0]:box[2]].sum())
            if not n:
                continue
            u = int(unc[box[1]:box[3], box[0]:box[2]].sum()) if unc is not None else 0
            hit = sorted(name for name, boxes in (zones or {}).items() if any(_overlap(box, z) for z in boxes))
            tiles.append({"id": f"T{len(tiles) + 1:03d}", "box": list(box), "contour_px": n,
                          "uncertain_px": u, "zones": hit, "challenge": bool(u or hit)})
    return tiles


def tile_pair(photo, reference, box):
    """Tesela 1:1: original sin nada al lado del contorno de la referencia (sin decir de qué llave)."""
    from PIL import Image

    rgb = np.asarray(photo)[..., :3]
    x1, y1, x2, y2 = box
    base = rgb[y1:y2, x1:x2]
    overlay = base.astype(np.float32) * 0.6
    m = as_bool(reference)[y1:y2, x1:x2]
    overlay[m] = base[m]
    overlay[dilate_square(_inner_contour(m), 1)] = (255, 220, 0)
    pair = Image.new("RGB", (2 * (x2 - x1) + 8, y2 - y1), (24, 24, 24))
    pair.paste(Image.fromarray(base.astype(np.uint8)), (0, 0))
    pair.paste(Image.fromarray(overlay.clip(0, 255).astype(np.uint8)), (x2 - x1 + 8, 0))
    return pair


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
        label = f"{c['id']} {c['kind']} {c['area_px']} px {c['open_or_enclosed']}"
        kinds = (("original", " · original"), ("xor", "")) if c["requires_adjudication"] else (("xor", ""),)
        for kind, suffix in kinds:
            tile = render(kind, crop)
            factor = max(1, min(8, 240 // max(tile.width, tile.height, 1)))
            tile = tile.resize((tile.width * factor, tile.height * factor), Image.NEAREST)
            if tile.width > 480 or tile.height > 480:
                tile.thumbnail((480, 480), Image.LANCZOS)
            zooms.append((label + suffix, tile))
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
