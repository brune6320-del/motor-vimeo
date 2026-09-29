"""Auditoría de una corrida A-E(−1) v1.3 según el protocolo v2 (rev. 1). Tres etapas separadas en el tiempo.

1. ``integrity``   (paso 2): bytes, hashes, prerregistro, plan de llamadas y congelado. **No devuelve
   ningún dato de resultado** (ni áreas, ni scores, ni sentinelas).
2. ``blind_package`` (paso 3): láminas ``C01``… con agujeros numerados, mapeo sellado en local y
   paquete para ChatGPT. Devuelve solo hashes y el número de láminas.
3. ``analyze``     (paso 7, después de archivar las dos llaves): sentinelas, agujeros, consenso y
   adjudicación, perturbación, recíproco, propiedad, reproducción de BASE e hipótesis.

Escrito y probado antes de la corrida (con un ZIP simulado); su SHA-256 queda en el prerregistro.
Todo lo que deriva de la foto se escribe en ``local/``.
"""

from __future__ import annotations

import hashlib
import io
import json
import secrets
import zipfile
from pathlib import Path

import numpy as np

from . import EXPECTED_IMAGE_SHA256
from . import aem1_v13 as v
from .masks import dilate_square, enclosed_holes

ZIP_PREFIX = "PRAGMA_AEM1v13_"
CONFIG = "aem1v13_config.json"
CALLS = "aem1v13_calls.json"
MANIFEST = "aem1v13_manifest.json"
REPORT = "aem1v13_report.json"
NPZ = "aem1v13_perturbaciones.npz"
PNG_BRANCHES = ("BASE", "+POS_HAIR", "+POS_SLEEVE", "+POS_HAIR+SLEEVE", "RECIPROCAL")
CRITERIA = ("correct_subject", "body_and_edges_complete", "other_person_excluded", "background_excluded")
AUX = ("target_hair_included", "target_dark_sleeves_included")
HOLE_MIN_PX = 1000
GPU_CHECKPOINT_MIN_BYTES = 800 * 2**20
OVERVIEW_BOX = (2000, 200, 3650, 2248)
REGIONS = [  # las mismas ventanas que la auditoría v1
    ("cabeza_y_pelo_recogido", (2450, 250, 3150, 900)),
    ("contacto_posterior", (2150, 650, 2700, 1300)),
    ("mano_levantada", (2850, 550, 3500, 1450)),
    ("mano_colgante", (2000, 1750, 2500, 2248)),
    ("costado_derecho", (3100, 850, 3550, 1650)),
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def packed_sha256(mask) -> str:
    """El mismo hash que v1.2 y la tabla de la corrida 1: np.packbits sin cabecera."""
    return sha(np.packbits(np.asarray(mask, bool)).tobytes())


def safe_name(candidate_id: str) -> str:
    return candidate_id.replace("|", "__")


def is_png_candidate(candidate_id: str) -> bool:
    return candidate_id.split("|", 1)[0] in PNG_BRANCHES


def candidates_of(plan) -> list:
    return [cid for call in plan for cid in call["candidates"]]


# ─── 1. integridad (sin resultados) ───────────────────────────────────────────────────────────

def _read(zip_path):
    with zipfile.ZipFile(zip_path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def load_masks(blobs: dict, candidate_ids) -> dict:
    from PIL import Image

    wanted = list(candidate_ids)
    out = {}
    npz = np.load(io.BytesIO(blobs[NPZ])) if any(not is_png_candidate(c) for c in wanted) else None
    for cid in wanted:
        if is_png_candidate(cid):
            with Image.open(io.BytesIO(blobs[f"masks/{safe_name(cid)}.png"])) as handle:
                out[cid] = np.asarray(handle.convert("L")) > 127
        else:
            shape = tuple(int(x) for x in npz["__shape__"])
            bits = np.unpackbits(npz[safe_name(cid)])[: shape[0] * shape[1]]
            out[cid] = bits.reshape(shape).astype(bool)
    return out


def integrity(zip_path, prereg: dict) -> dict:
    """Paso 2 del protocolo: ¿es este el ZIP del prerregistro, íntegro y producido en GPU real?"""
    zip_path = Path(zip_path)
    raw = zip_path.read_bytes()
    problems = []
    blobs = _read(zip_path)
    try:
        manifest = json.loads(blobs[MANIFEST])
        config = json.loads(blobs[CONFIG])
        calls = json.loads(blobs[CALLS])
    except KeyError as missing:
        return {"status": "INVALID_BUNDLE", "problems": [f"falta {missing}"], "zip_sha256": sha(raw)}
    listed = set(manifest["files"])
    present = set(blobs) - {MANIFEST}
    if listed != present:
        problems.append(f"manifiesto ≠ contenido: sobran {sorted(present - listed)}, faltan {sorted(listed - present)}")
    for name, meta in manifest["files"].items():
        if name in blobs and (len(blobs[name]) != meta["bytes"] or sha(blobs[name]) != meta["sha256"]):
            problems.append(f"bytes o SHA-256 distintos: {name}")
    if config.get("prereg_content_sha256") != prereg["content_sha256"] or config.get("prereg") != prereg:
        problems.append("el prerregistro embebido no es el versionado")
    plan = prereg["call_plan"]
    if [c["call_id"] for c in calls] != [c["call_id"] for c in plan]:
        problems.append("las llamadas ejecutadas no son las del plan prerregistrado")
    for executed, planned in zip(calls, plan):
        for field in ("points", "labels", "box", "mask_input_from", "multimask_output", "candidates"):
            if executed.get(field) != planned.get(field):
                problems.append(f"{planned['call_id']}: {field} distinto del plan")
    expected = candidates_of(plan)
    if sorted(manifest.get("masks", {})) != sorted(expected):
        problems.append("el manifiesto no lista exactamente las candidatas del plan")
    else:
        try:
            masks = load_masks(blobs, expected)
        except (KeyError, ValueError, OSError) as exc:
            problems.append(f"máscara ausente o ilegible: {exc}")
        else:
            bad = [cid for cid in expected if masks[cid].shape != (2248, 4000)
                   or packed_sha256(masks[cid]) != manifest["masks"][cid]]
            if bad:
                problems.append(f"máscaras con hash o forma distintos: {len(bad)}")
    env = config.get("environment", {})
    freeze = prereg["sam2_freeze"]
    if env.get("image_sha256") != EXPECTED_IMAGE_SHA256:
        problems.append("la foto no es la de aceptación")
    luma = config.get("luma_check", {})
    if not luma or luma.get("max_abs_deviation", 99) > 3.0:
        problems.append("la luma de los prompts no se comprobó o se desvía > 3,0")
    simulated = (env.get("torch") == "SIMULATED" or env.get("sam2_commit") == "SIMULATED"
                 or int(env.get("checkpoint_bytes", 0)) < GPU_CHECKPOINT_MIN_BYTES)
    if simulated:
        run_kind = "SIMULATED"
    elif env.get("device") != "cuda":
        run_kind = "REAL_CPU"
    else:
        run_kind = "REAL_GPU"
    if run_kind != "SIMULATED":
        if env.get("sam2_commit") != freeze["SAM2_GIT_COMMIT"]:
            problems.append("commit de SAM 2 distinto del congelado")
        if env.get("checkpoint_sha256") != freeze["CHECKPOINT_SHA256"] or env.get("checkpoint_bytes") != freeze["CHECKPOINT_BYTES"]:
            problems.append("checkpoint distinto del congelado")
    if problems:
        status = "INVALID_BUNDLE"
    elif run_kind == "SIMULATED":
        status = "SIMULATED_RUN_NOT_EVIDENCE"
    elif run_kind == "REAL_CPU":
        status = "REAL_CPU_NOT_COMPARABLE"
    else:
        status = "INTEGRITY_PASS"
    return {"status": status, "run_kind": run_kind, "problems": problems, "zip_sha256": sha(raw),
            "zip_bytes": len(raw), "run_id": config.get("run_id"), "prereg_content_sha256": config.get("prereg_content_sha256"),
            "environment": {k: env.get(k) for k in ("device", "device_name", "dtype", "torch", "python", "sam2_commit",
                                                    "checkpoint_sha256", "checkpoint_bytes", "image_sha256")},
            "calls": len(calls), "candidates": len(expected),
            "note": "sin datos de resultado: ni áreas, ni scores, ni sentinelas (protocolo v2 §2, paso 2)"}


# ─── 2. paquete ciego ─────────────────────────────────────────────────────────────────────────

def base_reproduction(masks: dict, base_reference: dict) -> dict:
    exact, differs = [], []
    for cid, ref in sorted(base_reference["candidates"].items()):
        (exact if packed_sha256(masks[cid]) == ref["packed_mask_sha256"] else differs).append(cid)
    return {"label": "BIT_EXACT" if not differs else "NOT_BIT_EXACT", "bit_exact": exact, "not_bit_exact": differs}


def blind_candidates(plan, reproduction) -> list:
    pos = [cid for cid in candidates_of(plan) if cid.split("|", 1)[0].startswith("+POS")]
    return pos + list(reproduction["not_bit_exact"])


def _shade(photo, mask, box, holes=()):
    from PIL import Image

    x1, y1, x2, y2 = box
    h, w = mask.shape
    ex1, ey1, ex2, ey2 = max(0, x1 - 1), max(0, y1 - 1), min(w, x2 + 1), min(h, y2 + 1)
    extended = mask[ey1:ey2, ex1:ex2]
    edge = (extended & dilate_square(~extended, 1))[y1 - ey1:y1 - ey1 + (y2 - y1), x1 - ex1:x1 - ex1 + (x2 - x1)]
    crop = photo[y1:y2, x1:x2].astype(np.float32)
    m = mask[y1:y2, x1:x2]
    view = np.where(m[..., None], crop, crop * 0.28)
    view[edge] = (255, 0, 255)
    for hole in holes:           # contorno cian de cada agujero numerado que cae en el recorte
        hx1, hy1, hx2, hy2 = hole["bbox"]
        if hx2 <= x1 or hx1 >= x2 or hy2 <= y1 or hy1 >= y2:
            continue
        inside = hole["mask"][y1:y2, x1:x2]
        ring = inside & dilate_square(~inside, 1)
        view[ring] = (0, 255, 255)
    return Image.fromarray(view.astype(np.uint8))


def _labels(mask) -> np.ndarray:
    """Imagen de etiquetas 4-conexas por corridas (sin SciPy); 0 = fondo."""
    m = np.asarray(mask, bool)
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
                    parent[b] = a
                scan += 1
            current.append((index, start, end))
        previous = current
    label = np.zeros((h, w), np.int32)
    roots = {}
    for y, start, end, index in runs:
        label[y, start:end] = roots.setdefault(find(index), len(roots) + 1)
    return label


def holes_with_masks(mask, min_area=HOLE_MIN_PX) -> list:
    """Agujeros cerrados ≥ ``min_area``, numerados de mayor a menor, con su máscara exacta."""
    complement = ~np.asarray(mask, bool)
    out = []
    for number, hole in enumerate(enclosed_holes(mask, min_area), 1):
        x1, y1, x2, y2 = hole["bbox"]
        label = _labels(complement[y1:y2, x1:x2])
        counts = np.bincount(label.ravel())
        # La componente del agujero ocupa toda su caja ajustada y tiene exactamente su área.
        matches = [k for k in range(1, len(counts)) if counts[k] == hole["area"]
                   and (label[0] == k).any() and (label[-1] == k).any() and (label[:, 0] == k).any() and (label[:, -1] == k).any()]
        region = np.zeros_like(complement)
        region[y1:y2, x1:x2] = label == matches[0]
        out.append({"number": number, "area": hole["area"], "bbox": hole["bbox"], "mask": region})
    return out


def blind_sheet(photo, mask, label, out_path):
    """Lámina v2: vista completa, cinco primeros planos 1:1 y un recorte ×2 por agujero ≥ 1000 px."""
    from PIL import Image, ImageDraw

    holes = holes_with_masks(mask)
    overview = _shade(photo, mask, OVERVIEW_BOX, holes)
    scale = 520 / overview.width
    overview = overview.resize((520, round(overview.height * scale)), Image.LANCZOS)
    draw_o = ImageDraw.Draw(overview)
    for hole in holes:
        x1, y1, x2, y2 = hole["bbox"]
        cx, cy = ((x1 + x2) / 2 - OVERVIEW_BOX[0]) * scale, ((y1 + y2) / 2 - OVERVIEW_BOX[1]) * scale
        draw_o.text((cx + 4, cy - 6), str(hole["number"]), fill=(0, 255, 255))
    tiles = [("vista_completa (reducida)", overview)] + [(name, _shade(photo, mask, box, holes)) for name, box in REGIONS]
    hole_tiles = []
    for hole in holes[:16]:
        x1, y1, x2, y2 = hole["bbox"]
        box = (max(0, x1 - 40), max(0, y1 - 40), min(mask.shape[1], x2 + 40), min(mask.shape[0], y2 + 40))
        tile = _shade(photo, mask, box, [hole])
        tile = tile.resize((tile.width * 2, tile.height * 2), Image.NEAREST)
        hole_tiles.append((f"agujero {hole['number']} · {hole['area']} px", tile))
    rows = [tiles[:3], tiles[3:]] + ([hole_tiles[i:i + 6] for i in range(0, len(hole_tiles), 6)] if hole_tiles else [])
    header, gap = 22, 8
    sizes = [(sum(t.width for _, t in row) + gap * (len(row) - 1), max(t.height for _, t in row) + header) for row in rows]
    listing = [f"#{h['number']}: {h['area']} px · caja {tuple(int(v) for v in h['bbox'])}" for h in holes]
    text_h = 18 * (len(listing) + 2)
    width = max(max(w for w, _ in sizes), 900)
    sheet = Image.new("RGB", (width, 40 + sum(h for _, h in sizes) + gap * len(rows) + text_h), (20, 20, 20))
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 12), f"CANDIDATA {label}  (ciega: sin rama, protocolo, semilla ni score)", fill=(255, 255, 0))
    y = 40
    for row, (_, row_h) in zip(rows, sizes):
        x = 0
        for name, tile in row:
            draw.text((x + 4, y + 4), name, fill=(230, 230, 230))
            sheet.paste(tile, (x, y + header))
            x += tile.width + gap
        y += row_h + gap
    draw.text((8, y + 4), f"Agujeros cerrados >= {HOLE_MIN_PX} px (contorno cian): {len(holes)}"
              + ("" if len(holes) <= 16 else " · solo los 16 mayores tienen recorte"), fill=(0, 255, 255))
    for i, line in enumerate(listing):
        draw.text((8, y + 22 + 18 * i), line, fill=(200, 255, 255))
    sheet.save(out_path)
    return [{"number": h["number"], "area_px": h["area"], "bbox": list(h["bbox"])} for h in holes]


LEEME_V2 = """# Paquete ciego · A‑E(−1) v1.3 · corrida {run_id}

Para: ChatGPT (segunda llave). De: Claude. **Privado:** son recortes de una foto de personas reales.

Protocolo: `auditoria/PROTOCOLO_AUDITORIA_AEM1_v2.md` (rev. 1), SHA‑256 `{protocol_sha256}`.
Mapeo sellado: SHA‑256 `{mapping_sha256}`. **Ninguna carta acompaña a este paquete** y no se ha
revelado ningún resultado. Hay {n} láminas, de `C01` a `C{n:02d}`.

Cómo leer cada lámina:

- arriba, la vista completa reducida y cinco primeros planos a resolución nativa;
- lo excluido está oscurecido y el borde de la máscara va en magenta;
- cada **agujero cerrado ≥ 1000 px** va contorneado en cian, numerado y con su recorte ×2.

Por cada etiqueta, responde:

1. `correct_subject`: TRUE si **más de la mitad del área** está sobre la chica del frente (cuerpo,
   pelo, ropa o accesorios). Una parte, por ejemplo solo una prenda o un botón, es TRUE.
2. `body_and_edges_complete`: cabeza y pelo visibles, cara, mano en V con dedos, ambos brazos o
   mangas, mano que cuelga y torso hasta el borde, sin faltantes de contorno ≥ ~1000 px. Clasifica
   **cada agujero numerado** como `D` (defecto: falta material de la chica) o `L` (legítimo: se ve
   fondo). Un solo `D` basta para FALSE.
3. `other_person_excluded`: nada del pelo recogido, pelo, blusa floral u hombro de la persona
   posterior, salvo un borde ambiguo de ≤ 5 px.
4. `background_excluded`: nada de pared, cuadros, mesa, vasitos o silla (salvo un borde de ≤ 5 px);
   sin islas ≥ 500 px.

Preguntas auxiliares (no deciden):

- `target_hair_included`: la mayor parte del pelo visible de la chica está dentro.
- `target_dark_sleeves_included`: la mayor parte de las dos mangas oscuras está dentro, sin
  perforaciones grandes.

Cada respuesta es TRUE, FALSE o UNSURE; UNSURE cuenta como FALSE. Toda respuesta que no sea TRUE
lleva nota con región y defecto.

**Devuelve:**

- el SHA‑256 de este ZIP;
- un JSON con la forma de `plantilla_juicios.json`, rellenado.

Después, y solo después, recibirás el desciegue.
"""


def blind_package(zip_path, photo, out_dir, prereg, base_reference, protocol_path, rng=None) -> dict:
    """Paso 3. Escribe en ``out_dir`` (local): láminas, mapeo sellado, plantilla y el ZIP del paquete."""
    rng = rng or secrets.SystemRandom()
    out_dir = Path(out_dir)
    sheets_dir = out_dir / "laminas"
    sheets_dir.mkdir(parents=True, exist_ok=True)
    blobs = _read(zip_path)
    plan = prereg["call_plan"]
    base_ids = sorted(base_reference["candidates"])
    reproduction = base_reproduction(load_masks(blobs, base_ids), base_reference)
    chosen = blind_candidates(plan, reproduction)
    order = list(chosen)
    rng.shuffle(order)
    labels = [f"C{i:02d}" for i in range(1, len(order) + 1)]
    masks = load_masks(blobs, order)
    mapping, holes = {}, {}
    for label, cid in zip(labels, order):
        holes[label] = blind_sheet(photo, masks[cid], label, sheets_dir / f"candidata_{label}.png")
        mapping[label] = {"candidate_id": cid, "packed_mask_sha256": packed_sha256(masks[cid])}
    mapping_bytes = json.dumps({"mapping": mapping, "holes": holes}, indent=2, sort_keys=True).encode()
    (out_dir / "sealed_mapping.json").write_bytes(mapping_bytes)
    template = {"schema": "pragma.aem1v13_blind_judgments", "schema_version": "0.1.0",
                "package_sha256": "<SHA-256 del ZIP que juzgaste>", "auditor": "<quién>",
                "candidates": {label: {"criteria": {c: "TRUE|FALSE|UNSURE" for c in CRITERIA},
                                       "aux": {a: "TRUE|FALSE|UNSURE" for a in AUX},
                                       "holes": {str(h["number"]): "D|L" for h in holes[label]},
                                       "notes": ""} for label in labels}}
    template_bytes = (json.dumps(template, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    protocol_sha = sha(Path(protocol_path).read_bytes())
    leeme = LEEME_V2.format(run_id=json.loads(blobs[CONFIG])["run_id"], protocol_sha256=protocol_sha,
                            mapping_sha256=sha(mapping_bytes), n=len(labels)).encode("utf-8")
    package = out_dir / f"PRAGMA_AEM1v13_paquete_ciego_{json.loads(blobs[CONFIG])['run_id']}.zip"
    sheet_hashes = {}
    with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in (("LEEME.md", leeme), ("plantilla_juicios.json", template_bytes)):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            archive.writestr(info, data)
        for label in labels:
            from PIL import Image

            buffer = io.BytesIO()
            Image.open(sheets_dir / f"candidata_{label}.png").convert("RGB").save(buffer, "JPEG", quality=92)
            data = buffer.getvalue()
            sheet_hashes[f"candidata_{label}.jpg"] = sha(data)
            archive.writestr(zipfile.ZipInfo(f"candidata_{label}.jpg", date_time=(2026, 1, 1, 0, 0, 0)), data)
    summary = {"package": package.name, "package_sha256": sha(package.read_bytes()),
               "sealed_mapping_sha256": sha(mapping_bytes), "protocol_sha256": protocol_sha,
               "sheets_sha256": sheet_hashes, "labels": labels, "n": len(labels),
               "base_reproduction_label": reproduction["label"], "base_not_bit_exact": len(reproduction["not_bit_exact"])}
    (out_dir / "blind_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


# ─── 3. análisis (después de las dos llaves) ──────────────────────────────────────────────────

def _flat(judgment: dict) -> dict:
    out = dict(judgment["criteria"])
    out.update(judgment.get("aux", {}))
    return out


def reconcile(values: dict, screen: dict, holes_verdict: dict) -> tuple:
    """Protocolo v2 §4: sentinelas y agujeros D fuerzan FALSE; nunca suben un criterio a TRUE."""
    values, notes = dict(values), []
    rules = (("body_and_edges_complete", screen["missed_keep"]), ("other_person_excluded", screen["leaked_other_person"]),
             ("background_excluded", screen["leaked_background"]))
    for field, ids in rules:
        if ids and values.get(field) == "TRUE":
            values[field] = "FALSE"
            notes.append(f"{field}: TRUE→FALSE por sentinelas {ids}")
    if any(v == "D" for v in holes_verdict.values()) and values.get("body_and_edges_complete") == "TRUE":
        values["body_and_edges_complete"] = "FALSE"
        notes.append("body_and_edges_complete: TRUE→FALSE por agujero clasificado D")
    return values, notes


def sentinel_screen(mask, base_config) -> dict:
    h = base_config["holdouts"]
    cov = lambda group: {s["id"]: round(v.patch_coverage(mask, s["xy"]), 4) for s in h[group]}  # noqa: E731
    keep, other, background = cov("keep_subject"), cov("drop_other_person"), cov("drop_background")
    return {"coverage": {**keep, **other, **background},
            "missed_keep": [k for k, c in keep.items() if c < v.SENTINEL_KEEP_MIN],
            "leaked_other_person": [k for k, c in other.items() if c > v.SENTINEL_DROP_MAX],
            "leaked_background": [k for k, c in background.items() if c > v.SENTINEL_DROP_MAX]}


def consensus(first: dict, second: dict, adjudications: dict) -> tuple:
    """Valor de consenso por celda: igual en ambas llaves, o el de la adjudicación técnica (v2 §5.2)."""
    values, pending = {}, []
    for cid in first:
        row = {}
        for field in CRITERIA + AUX:
            a, b = first[cid].get(field), second[cid].get(field)
            if a == b:
                row[field] = a
            elif (cid, field) in adjudications:
                row[field] = adjudications[(cid, field)]["value"]
            else:
                row[field] = "PENDING_ADJUDICATION"
                pending.append((cid, field))
        values[cid] = row
    return values, pending


def analyze(zip_path, prereg, base_reference, mapping, first_raw, second_raw, adjudications=None) -> dict:
    """Paso 7. ``first_raw``/``second_raw``: juicios ciegos por etiqueta (C01…) de cada llave."""
    adjudications = adjudications or {}
    blobs = _read(zip_path)
    plan = prereg["call_plan"]
    base_config = prereg["base_config"]
    all_ids = candidates_of(plan)
    masks = load_masks(blobs, all_ids)
    o_points = [(s["id"], s["xy"]) for s in base_config["holdouts"]["drop_other_person"]]
    k_points = [(s["id"], s["xy"]) for s in base_config["holdouts"]["keep_subject"]]
    screens = {cid: sentinel_screen(masks[cid], base_config) for cid in all_ids}
    girl_ids = [cid for cid in all_ids if cid.split("|", 1)[0] in ("BASE", "+POS_HAIR", "+POS_SLEEVE", "+POS_HAIR+SLEEVE")]

    # Juicios por candidata (las etiquetas se traducen con el mapeo sellado).
    label_to_cid = {label: row["candidate_id"] for label, row in mapping["mapping"].items()}
    keys = {"claude": {label_to_cid[k]: val for k, val in first_raw["candidates"].items()},
            "chatgpt": {label_to_cid[k]: val for k, val in second_raw["candidates"].items()}}
    reconciled = {}
    for key, rows in keys.items():
        reconciled[key] = {}
        for cid, judgment in rows.items():
            values, notes = reconcile(_flat(judgment), screens[cid], judgment.get("holes", {}))
            reconciled[key][cid] = {"values": values, "reconciliation": notes}
    flat = {key: {cid: row["values"] for cid, row in rows.items()} for key, rows in reconciled.items()}
    agreed, pending = consensus(flat["claude"], flat["chatgpt"], adjudications)
    reproduction = base_reproduction({cid: masks[cid] for cid in base_reference["candidates"]}, base_reference)
    for cid in reproduction["bit_exact"]:
        agreed[cid] = {**base_reference["candidates"][cid]["criteria"],
                       "target_hair_included": "NO_JUZGADO_V1", "target_dark_sleeves_included": "NO_JUZGADO_V1"}
    passing = sorted(cid for cid, row in agreed.items() if all(row[c] == "TRUE" for c in CRITERIA))

    # Perturbación (solo informa).
    def base_of(call, cid):
        suffix = cid.rsplit("|", 2)[-2:]
        if call["branch"] == "PERTURB_POINT" and call["target"] == "P+1":
            return f"BASE|{suffix[0]}|{suffix[1]}"
        if call["branch"] == "PERTURB_POINT":
            return f"+POS_HAIR+SLEEVE|{suffix[0]}|{suffix[1]}"
        return f"BASE|{suffix[0]}|{suffix[1]}"

    groups = {}
    for call in plan:
        if call["branch"] not in ("PERTURB_POINT", "PERTURB_BOX"):
            continue
        family = call.get("target") or call.get("family")
        for cid in call["candidates"]:
            base_cid = base_of(call, cid)
            groups.setdefault((call["branch"], family, base_cid), []).append((call["perturbation"], masks[cid]))
    stability = {}
    for (branch, family, base_cid), rows in sorted(groups.items()):
        stability[f"{branch}|{family}|{base_cid}"] = v.perturbation_stability(masks[base_cid], rows, o_points)
    summaries = {}
    for name, result in stability.items():
        branch, family, base_cid = name.split("|", 2)
        protocol = base_cid.split("|")[1]
        summaries.setdefault(f"{branch}|{family}|{protocol}", []).append(result["label"])
    family_summary = {k: {"labels": labels_, "summary": v.worst(labels_)} for k, labels_ in sorted(summaries.items())}

    # Recíproco y propiedad (solo informa).
    r_seeds = [(f"RECIPROCAL|R-corrections|s{k}", masks[f"RECIPROCAL|R-corrections|s{k}"]) for k in range(3)]
    r_stability = v.reciprocal_stability(r_seeds, k_points)
    r_ref = v.reference_mask(r_seeds, o_points)
    r_mask = masks[r_ref]
    bun = [(sid, xy) for sid, xy in o_points if sid in ("O2", "O3")]
    r_covers_bun = all(v.patch_coverage(r_mask, xy) >= v.SENTINEL_KEEP_MIN for _, xy in bun)
    leaks_bun = {cid: bool(v.leaked(masks[cid], bun)) for cid in girl_ids}
    owner = {cid: v.ownership(masks[cid], r_mask) for cid in girl_ids}
    interpretation = {cid: v.interpret_reciprocal(leaks_bun[cid], r_stability["label"], owner[cid]["label"], r_covers_bun)
                      for cid in girl_ids}

    # Hipótesis prerregistradas.
    both = {key: {cid: row for cid, row in flat[key].items()} for key in flat}
    hypotheses = {}
    pos_ids = [cid for cid in all_ids if cid.split("|", 1)[0].startswith("+POS")]
    if all(cid in both["claude"] and cid in both["chatgpt"] for cid in pos_ids) and not pending:
        hypotheses["H-C1"] = v.hypothesis_h_c1(both, leaks_bun)
        # BASE emparejada: la referencia si se reprodujo bit a bit; si no, su consenso ciego de esta corrida.
        hypotheses["H-G1"] = v.hypothesis_h_g1(both, agreed, {cid: agreed[cid] for cid in base_reference["candidates"]})
        hypotheses["H-G4"] = v.hypothesis_h_g4(both)
    else:
        hypotheses.update({h: "PENDING_ADJUDICATION" for h in ("H-C1", "H-G1", "H-G4")})
    hypotheses["H-C2"] = v.hypothesis_h_c2(
        [stability[f"PERTURB_POINT|P+1|BASE|point|{k}"]["label"] for k in range(3)])
    hypotheses["H-G2"] = v.hypothesis_h_g2(r_stability["label"])
    hypotheses["H-G3"] = v.hypothesis_h_g3(r_stability["label"], r_covers_bun, leaks_bun,
                                           {cid: owner[cid]["label"] for cid in girl_ids})

    if pending:
        case = "PENDING_TECHNICAL_ADJUDICATION"
    elif passing:
        case = "SEPARATION_DEMONSTRATED_UNDER_FIXED_AEM1_PROTOCOL"
    else:
        case = "INCONCLUSIVE_SELECTED_OUTPUT_FAILED"
    return {
        "schema": "pragma.aem1v13_analysis", "schema_version": "0.1.0",
        "case_status": case, "passing": passing, "pending_adjudication": [f"{c}.{f}" for c, f in pending],
        "base_reproduction": reproduction, "consensus": agreed, "reconciled": reconciled,
        "sentinels": screens, "perturbation": {"per_candidate": stability, "per_family": family_summary},
        "reciprocal": {"stability": r_stability, "reference": r_ref, "covers_bun": r_covers_bun},
        "ownership": owner, "leaks_bun": leaks_bun, "interpretation": interpretation,
        "hypotheses": hypotheses, "sam2_rejectable": False, "project_status": "INCONCLUSIVE_A_E0_REQUIRED",
    }
