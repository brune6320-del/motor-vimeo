"""Auditoría IA del ZIP de A-E(−1) (DEC-018-P): lo que antes se pedía fiscalizar a la persona.

Dos etapas, deliberadamente separadas:

1. ``audit_zip``: automática y reproducible. Verifica integridad (manifiesto, bytes, SHA-256,
   digest de configuración, invariantes del informe), detecta corridas SIMULADAS o no GPU,
   recalcula los sentinelas de cada candidata con la foto, mide geometría (componentes, agujeros)
   e indicadores de fuga por regiones conocidas, y genera primeros planos a resolución completa.
   No elige ninguna candidata.
2. ``write_verdict``: el veredicto del auditor tras mirar TODAS las candidatas. Registra quién
   audita, qué candidata elige y por qué, los cuatro criterios visuales y un token que liga el
   veredicto a los bytes exactos de la máscara y a la evidencia.

Todo lo que deriva de la foto se escribe en ``local/`` (no versionado).
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from . import EXPECTED_IMAGE_SHA256, EXPECTED_IMAGE_SIZE
from .masks import dilate_square, mask_bbox

GPU_CHECKPOINT_MIN_BYTES = 800 * 2**20
CRITERIA = ("correct_subject", "body_and_edges_complete", "other_person_excluded", "background_excluded")

# Regiones de apoyo derivadas del preflight y del borrador A-E0 (ae0_002, ae0_003, ae0_048, ae0_049).
# Son APROXIMADAS: sirven para ordenar la inspección y detectar fugas groseras, nunca como GT.
REGIONS = {
    # (caja XYXY semiabierta, criterio de píxel, qué se espera de la máscara de la chica)
    "pelo_recogido_posterior": ((2636, 310, 2790, 430), "dark", "fuera"),
    "hombro_floral_posterior": ((2240, 740, 2560, 1010), "any", "fuera"),
    "pared_sobre_la_cabeza": ((2800, 280, 3300, 420), "any", "fuera"),
    "mesa_izquierda_de_la_chica": ((1500, 1500, 2080, 1850), "any", "fuera"),
    "cara_de_la_chica": ((2720, 600, 2990, 900), "any", "dentro"),
    "mano_en_V": ((2950, 640, 3350, 1300), "bright", "dentro"),
    "mano_que_cuelga": ((2150, 1880, 2330, 2100), "bright", "dentro"),
}
CLOSEUPS = {
    "cabeza_y_pelo_recogido": (2450, 250, 3150, 900),
    "contacto_posterior": (2150, 650, 2700, 1300),
    "mano_levantada": (2850, 550, 3500, 1450),
    "mano_colgante": (2000, 1750, 2500, 2248),
    "costado_derecho": (3100, 850, 3550, 1650),
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def packed_mask_sha256(mask) -> str:
    """Mismo hash que el cuaderno usa para ligar la selección (np.packbits sin cabecera)."""
    return _sha(np.packbits(np.asarray(mask, bool)).tobytes())


def run_components(mask):
    """Componentes 4-conexas por corridas (rápido sin SciPy). Devuelve [(área, toca_borde)]."""
    m = np.asarray(mask, bool)
    h, w = m.shape
    parent, area, border = [], [], []

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    previous = []   # [(índice, inicio, fin)] de la fila anterior, ordenadas por inicio
    for y in range(h):
        row = np.concatenate(([False], m[y], [False]))
        change = np.flatnonzero(row[1:] != row[:-1])
        current = []
        pointer = 0
        for start, end in zip(change[0::2].tolist(), change[1::2].tolist()):
            index = len(parent)
            parent.append(index)
            area.append(end - start)
            border.append(y == 0 or y == h - 1 or start == 0 or end == w)
            # Dos punteros: las corridas de ambas filas están ordenadas, así cada fila es O(r1 + r2).
            while pointer < len(previous) and previous[pointer][2] <= start:
                pointer += 1
            scan = pointer
            while scan < len(previous) and previous[scan][1] < end:
                a, b = find(index), find(previous[scan][0])
                if a != b:
                    parent[b] = a
                    area[a] += area[b]
                    border[a] = border[a] or border[b]
                scan += 1
            current.append((index, start, end))
        previous = current
    roots = {find(i) for i in range(len(parent))}
    return sorted(((area[r], border[r]) for r in roots), reverse=True)


def _pixel_selector(gray, box, kind):
    x1, y1, x2, y2 = box
    patch = gray[y1:y2, x1:x2]
    if kind == "dark":
        return patch < 110
    if kind == "bright":
        return patch > 225
    return np.ones_like(patch, bool)


def _region_coverage(mask, gray, box, kind):
    x1, y1, x2, y2 = box
    select = _pixel_selector(gray, box, kind)
    covered = np.asarray(mask[y1:y2, x1:x2], bool) & select
    total = int(select.sum())
    return round(float(covered.sum()) / total, 4) if total else None


def _patch_coverage(mask, xy, radius):
    x, y = (int(round(float(v))) for v in xy)
    h, w = mask.shape
    patch = mask[max(0, y - radius):min(h, y + radius + 1), max(0, x - radius):min(w, x + radius + 1)]
    return float(np.asarray(patch, np.float32).mean())


def _load_alpha(data: bytes):
    from PIL import Image

    with Image.open(io.BytesIO(data)) as handle:
        array = np.asarray(handle.convert("L"))
    return array


def _render_closeups(photo, mask, title, out_path):
    """Por región: foto con lo excluido oscurecido y el borde de la máscara en magenta, a 1:1."""
    from PIL import Image, ImageDraw

    tiles = []
    for name, (x1, y1, x2, y2) in CLOSEUPS.items():
        crop = photo[y1:y2, x1:x2].astype(np.float32)
        m = np.asarray(mask[y1:y2, x1:x2], bool)
        edge = m & dilate_square(~m, 1)   # borde interior: píxel dentro con algún vecino fuera
        view = np.where(m[..., None], crop, crop * 0.30)
        view[edge] = (255, 0, 255)
        tile = Image.fromarray(view.astype(np.uint8))
        canvas = Image.new("RGB", (tile.width, tile.height + 24), (0, 0, 0))
        canvas.paste(tile, (0, 24))
        ImageDraw.Draw(canvas).text((6, 5), f"{name} ({x1},{y1})-({x2},{y2})", fill=(255, 255, 255))
        tiles.append(canvas)
    width = sum(t.width for t in tiles) + 8 * (len(tiles) - 1)
    height = max(t.height for t in tiles) + 30
    sheet = Image.new("RGB", (width, height), (25, 25, 25))
    ImageDraw.Draw(sheet).text((6, 6), title, fill=(255, 255, 0))
    x = 0
    for tile in tiles:
        sheet.paste(tile, (x, 30))
        x += tile.width + 8
    sheet.save(out_path)
    return out_path


def _render_overview(photo, candidates, out_path, box=(2000, 200, 3650, 2248), thumb_width=330):
    from PIL import Image, ImageDraw

    x1, y1, x2, y2 = box
    tiles = []
    for key, mask in candidates:
        crop = photo[y1:y2, x1:x2].astype(np.float32)
        m = np.asarray(mask[y1:y2, x1:x2], bool)
        view = np.where(m[..., None], crop, crop * 0.25).astype(np.uint8)
        tile = Image.fromarray(view)
        tile = tile.resize((thumb_width, round(tile.height * thumb_width / tile.width)), Image.LANCZOS)
        canvas = Image.new("RGB", (tile.width, tile.height + 22), (0, 0, 0))
        canvas.paste(tile, (0, 22))
        ImageDraw.Draw(canvas).text((4, 4), key, fill=(255, 255, 0))
        tiles.append(canvas)
    columns = 6
    rows = (len(tiles) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * (thumb_width + 6), rows * (tiles[0].height + 6)), (25, 25, 25))
    for index, tile in enumerate(tiles):
        sheet.paste(tile, ((index % columns) * (thumb_width + 6), (index // columns) * (tiles[0].height + 6)))
    sheet.save(out_path)
    return out_path


def audit_zip(zip_path, photo=None, out_dir=None) -> dict:
    """Auditoría automática. ``photo``: array RGB de la foto (si falta, se omiten píxeles y vistas)."""
    zip_path = Path(zip_path)
    out_dir = Path(out_dir) if out_dir else None
    problems, notes = [], []
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        blobs = {name: archive.read(name) for name in names}
    manifest = json.loads(blobs["aem1_manifest.json"])
    listed = {e["name"]: e for e in manifest["entries"]}
    if names != set(listed) | {"aem1_manifest.json"}:
        problems.append(f"el ZIP y el manifiesto no listan los mismos archivos: {sorted(names ^ (set(listed) | {'aem1_manifest.json'}))}")
    for name, entry in listed.items():
        blob = blobs.get(name)
        if blob is None:
            continue
        if len(blob) != entry["bytes"] or _sha(blob) != entry["sha256"]:
            problems.append(f"{name}: bytes o SHA-256 no coinciden con el manifiesto")
    report = json.loads(blobs["aem1_report.json"])
    config_file = json.loads(blobs["aem1_config.json"])
    config, digest = config_file["config"], config_file["config_digest"]
    recomputed = _sha(json.dumps(config, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    if recomputed != digest:
        problems.append("config_digest no corresponde a la configuración")
    if report.get("configuration") != config:
        problems.append("la configuración del informe difiere de aem1_config.json")
    for key, expected in (("phase_b_blocked", True), ("sam2_rejectable", False),
                          ("project_status", "INCONCLUSIVE_A_E0_REQUIRED")):
        if report.get(key) != expected:
            problems.append(f"invariante roto: {key}={report.get(key)!r}")
    environment = report.get("environment", {})
    if environment.get("image_sha256") != EXPECTED_IMAGE_SHA256:
        problems.append("la corrida no usó la foto de aceptación")

    simulated = environment.get("sam2_commit") == "SIMULATED" or environment.get("checkpoint_bytes", 0) < GPU_CHECKPOINT_MIN_BYTES
    if simulated:
        run_kind = "SIMULATED"
        notes.append("Corrida simulada (arnés): sirve para probar el flujo, NUNCA como evidencia de SAM 2.")
    elif environment.get("device") != "cuda":
        run_kind = "REAL_CPU"
        notes.append("SAM 2 real en CPU: la calidad vale; los tiempos no son comparables con GPU.")
    else:
        run_kind = "REAL_GPU"

    specs = {
        group: [(s["sentinel_id"], tuple(s["xy"])) for s in config[group]]
        for group in ("holdout_keep_subject", "holdout_drop_other_person", "holdout_drop_background")
    }
    radius = int(config["patch_radius"])
    keep_min, drop_max = float(config["keep_min_coverage"]), float(config["drop_max_coverage"])
    gray = photo.astype(np.float32).mean(axis=2) if photo is not None else None

    candidates, masks_for_overview = [], []
    for key, proposal in report["proposals"].items():
        if proposal["config_digest"] != digest:
            problems.append(f"{key}: la propuesta pertenece a otra configuración")
        for index, alpha_name in enumerate(proposal["alpha_files"]):
            if alpha_name not in blobs:
                problems.append(f"{key}: falta {alpha_name}")
                continue
            alpha = _load_alpha(blobs[alpha_name])
            if (alpha.shape[1], alpha.shape[0]) != EXPECTED_IMAGE_SIZE or not set(np.unique(alpha).tolist()) <= {0, 255}:
                problems.append(f"{alpha_name}: tamaño o valores no válidos")
                continue
            mask = alpha > 0
            coverage = {
                "keep": {sid: _patch_coverage(mask, xy, radius) for sid, xy in specs["holdout_keep_subject"]},
                "other_person": {sid: _patch_coverage(mask, xy, radius) for sid, xy in specs["holdout_drop_other_person"]},
                "background": {sid: _patch_coverage(mask, xy, radius) for sid, xy in specs["holdout_drop_background"]},
            }
            recorded = proposal["candidate_metrics"][index]["coverage"]
            same = all(abs(coverage[a][sid] - recorded[b][sid]) < 1e-9
                       for a, b in (("keep", "keep_subject"), ("other_person", "drop_other_person"),
                                    ("background", "drop_background")) for sid in coverage[a])
            if not same:
                problems.append(f"{key}#{index}: los sentinelas recalculados no coinciden con el informe")
            components = run_components(mask)
            holes = [a for a, touches in run_components(~mask) if not touches]
            row = {
                "key": key, "protocol": proposal["protocol"], "candidate_index": index,
                "seed_candidate_index": proposal.get("seed_candidate_index"),
                "alpha_file": alpha_name, "packed_mask_sha256": packed_mask_sha256(mask),
                "predicted_iou": proposal["candidate_scores"][index],
                "area_fraction": round(float(mask.mean()), 5), "bbox": mask_bbox(mask),
                "components": len(components),
                "largest_component_share": round(components[0][0] / max(1, int(mask.sum())), 4) if components else 0.0,
                "holes": len(holes), "holes_area_px": int(sum(holes)),
                "sentinels": {
                    "missed_keep": [s for s, v in coverage["keep"].items() if v < keep_min],
                    "leaked_other_person": [s for s, v in coverage["other_person"].items() if v > drop_max],
                    "leaked_background": [s for s, v in coverage["background"].items() if v > drop_max],
                },
                "sentinels_match_report": same,
            }
            row["sentinel_screen_pass"] = not any(row["sentinels"].values())
            if gray is not None:
                row["regions"] = {name: {"coverage": _region_coverage(mask, gray, box, kind), "expected": expected}
                                  for name, (box, kind, expected) in REGIONS.items()}
            candidates.append(row)
            masks_for_overview.append((f"{key}#{index}", mask))

    evidence = {}
    if out_dir is not None and photo is not None and candidates:
        out_dir.mkdir(parents=True, exist_ok=True)
        overview = _render_overview(photo, masks_for_overview, out_dir / "00_todas_las_candidatas.png")
        evidence[overview.name] = _sha(overview.read_bytes())
        for row, (label, mask) in zip(candidates, masks_for_overview):
            safe = label.replace("+", "_").replace(":", "_").replace("#", "_c")
            path = _render_closeups(photo, mask, f"{label} · sentinelas {'OK' if row['sentinel_screen_pass'] else 'REVISAR'}",
                                    out_dir / f"primeros_planos_{safe}.png")
            row["closeups_file"] = path.name
            evidence[path.name] = _sha(path.read_bytes())

    result = {
        "schema": "pragma.aem1_audit_auto", "schema_version": "0.1.0",
        "audited_at_utc": datetime.now(timezone.utc).isoformat(),
        "zip": zip_path.name, "zip_sha256": _sha(zip_path.read_bytes()), "zip_bytes": zip_path.stat().st_size,
        "run_id": report.get("run_id"), "run_kind": run_kind, "case_status_in_zip": report.get("case_status"),
        "config_digest": digest, "config_revision": config.get("config_revision"),
        "environment": {k: environment.get(k) for k in ("device", "device_name", "dtype", "sam2_commit",
                                                         "checkpoint_bytes", "checkpoint_sha256", "torch", "python")},
        "timings_s": report.get("timings_s"), "model": report.get("model"),
        "integrity": {"pass": not problems, "problems": problems},
        "candidates": candidates,
        "inspection_order": [f"{c['key']}#{c['candidate_index']}" for c in sorted(
            candidates, key=lambda c: (not c["sentinel_screen_pass"], c["components"], -c["area_fraction"]))],
        "inspection_order_note": "Orden para mirar, no selección: el auditor revisa TODAS y elige por contenido (DEC-005).",
        "evidence_files": evidence,
        "notes": notes,
    }
    if out_dir is not None:
        (out_dir / "aem1_audit_auto.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def write_verdict(auto: dict, selected: str, criteria: dict, notes: str, auditor: str, reasoning: list,
                  out_path=None, cross_audit=None) -> dict:
    """Veredicto del auditor. ``selected`` = "clave#índice" de una candidata de ``auto``."""
    by_label = {f"{c['key']}#{c['candidate_index']}": c for c in auto["candidates"]}
    if selected not in by_label:
        raise ValueError(f"{selected!r} no es una candidata auditada")
    if set(criteria) != set(CRITERIA) or not all(isinstance(v, bool) for v in criteria.values()):
        raise ValueError(f"criterios requeridos: {CRITERIA}")
    if not auditor.strip():
        raise ValueError("el auditor debe identificarse")
    if not all(criteria.values()) and not notes.strip():
        raise ValueError("si algún criterio es falso, las notas son obligatorias")
    chosen = by_label[selected]
    if not auto["integrity"]["pass"]:
        status = "INVALID_BUNDLE"
    elif auto["run_kind"] == "SIMULATED":
        status = "SIMULATED_RUN_NOT_EVIDENCE"
    elif chosen["sentinel_screen_pass"] and all(criteria.values()):
        status = "SEPARATION_DEMONSTRATED_UNDER_FIXED_AEM1_PROTOCOL"
    else:
        status = "INCONCLUSIVE_SELECTED_OUTPUT_FAILED"
    body = {
        "schema": "pragma.aem1_audit_verdict", "schema_version": "0.1.0",
        "zip_sha256": auto["zip_sha256"], "run_id": auto["run_id"], "run_kind": auto["run_kind"],
        "config_digest": auto["config_digest"], "selected": selected,
        "packed_mask_sha256": chosen["packed_mask_sha256"], "criteria": criteria, "notes": notes.strip(),
        "reasoning": reasoning, "auditor": auditor.strip(), "candidates_reviewed": sorted(by_label),
        "evidence_files": auto["evidence_files"], "case_status": status,
        "project_status": "INCONCLUSIVE_A_E0_REQUIRED", "phase_b_blocked": True, "sam2_rejectable": False,
        "cross_audit": cross_audit or {"by": "ChatGPT", "status": "PENDIENTE"},
        "user_veto": "la persona usuaria puede vetar este veredicto en cualquier momento",
    }
    body["inspection_token"] = _sha(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    body["decided_at_utc"] = datetime.now(timezone.utc).isoformat()
    if out_path is not None:
        Path(out_path).write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return body
