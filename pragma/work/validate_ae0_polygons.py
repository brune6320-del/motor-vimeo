"""Valida un archivo de polígonos A‑E0 antes de entregarlo (formato en ``ae0/FORMATO_POLIGONOS_A-E0.md``).

    python3 work/validate_ae0_polygons.py <poligonos.json>

Comprueba:
- el esquema y el bloque ``key``;
- que estén **exactamente** las personas del inventario adjudicado;
- que cada anillo sea válido y la máscara no salga vacía;
- que todos los vértices crudos, de ``rings`` y de ``uncertain_rings``, sean finitos y estén dentro
  de la foto: ``0 <= x <= 4000`` y ``0 <= y <= 2248``. Sin esto, ``rasterize`` recortaría en silencio
  lo que sale de la imagen (ChatGPT 013);
- que ni la máscara ni la zona incierta se salgan de la caja adjudicada de la persona (margen de
  40 px). Una zona incierta enorme neutralizaría parte del benchmark, porque DEC‑025 la excluye de
  las métricas (ChatGPT 013).

No exige ``uncertain ⊆ mask``: una banda incierta legítima cruza la frontera. Tampoco pone un máximo
de área incierta: DEC‑025 ya obliga a reportar ``uncertain_area_px`` y ``uncertain_fraction``.

Imprime el SHA‑256 del archivo, que es el que se compromete, y el área de cada máscara.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pragma_ae import EXPECTED_IMAGE_SHA256, EXPECTED_IMAGE_SIZE  # noqa: E402
from pragma_ae.masks import mask_bbox  # noqa: E402
from pragma_ae.polygon import rasterize_person  # noqa: E402

INVENTORY = ROOT / "ae0/scene_inventory.json"
MARGIN = 40
SCHEMA = "pragma.ae0_polygons"


def vertex_errors(rings, label: str) -> list[str]:
    """Errores de los vértices crudos: finitos y dentro de ``[0, ancho] × [0, alto]``."""
    w, h = EXPECTED_IMAGE_SIZE
    errors = []
    for k, ring in enumerate(rings):
        try:
            pts = np.asarray(ring, dtype=np.float64)
        except (TypeError, ValueError):
            errors.append(f"{label}[{k}]: vértices no numéricos")
            continue
        if pts.ndim != 2 or pts.shape[1] != 2 or len(pts) < 3:
            errors.append(f"{label}[{k}]: cada anillo necesita al menos 3 vértices [x, y]")
            continue
        finite = np.isfinite(pts).all(axis=1)
        if not finite.all():
            errors.append(f"{label}[{k}]: {int((~finite).sum())} vértices no finitos")
        inside = (pts[:, 0] >= 0) & (pts[:, 0] <= w) & (pts[:, 1] >= 0) & (pts[:, 1] <= h)
        outside = finite & ~inside
        if outside.any():
            errors.append(f"{label}[{k}]: {int(outside.sum())} vértices fuera de la foto "
                          f"(0 ≤ x ≤ {w}, 0 ≤ y ≤ {h}), p. ej. {pts[outside][0].tolist()}")
    return errors


def outside_box(box, bbox) -> bool:
    x1, y1, x2, y2 = bbox
    return box[0] < x1 - MARGIN or box[1] < y1 - MARGIN or box[2] > x2 + MARGIN or box[3] > y2 + MARGIN


def check(path: Path, inventory_path: Path = INVENTORY) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    persons = {o["id"]: o for o in inventory["objects"] if o["concept_en"] == "person"}
    errors, stats = [], {}
    if data.get("schema") != SCHEMA:
        errors.append(f"schema debe ser {SCHEMA}")
    key = data.get("key") or {}
    for field in ("auditor", "blind_statement", "image_sha256", "derivation", "created"):
        if not key.get(field):
            errors.append(f"key.{field} falta")
    if key.get("image_sha256") and key["image_sha256"] != EXPECTED_IMAGE_SHA256:
        errors.append("key.image_sha256 no es la foto de PRAGMA")
    if key.get("derivation") and key["derivation"] != "AI_POLYGON_RASTER":
        errors.append("key.derivation debe ser AI_POLYGON_RASTER (NUMPY_MINIMAL)")
    given = data.get("persons") or {}
    if set(given) != set(persons):
        errors.append(f"personas {sorted(given)} ≠ inventario {sorted(persons)}")
    shape = (EXPECTED_IMAGE_SIZE[1], EXPECTED_IMAGE_SIZE[0])
    for oid, entry in given.items():
        bad = (vertex_errors(entry.get("rings") or [], "rings")
               + vertex_errors(entry.get("uncertain_rings") or [], "uncertain_rings"))
        if bad:
            errors.extend(f"{oid}: {e}" for e in bad)
            continue
        r = rasterize_person(entry, shape)
        area = int(r["mask"].sum())
        if not area:
            errors.append(f"{oid}: máscara vacía")
            continue
        box = mask_bbox(r["mask"])
        ubox = mask_bbox(r["uncertain"])
        if oid in persons:
            bbox = persons[oid]["bbox"]
            if outside_box(box, bbox):
                errors.append(f"{oid}: la máscara {list(box)} se sale de la caja adjudicada {bbox} (±{MARGIN} px)")
            if ubox is not None and outside_box(ubox, bbox):
                errors.append(f"{oid}: la zona incierta {list(ubox)} se sale de la caja adjudicada {bbox} (±{MARGIN} px)")
        stats[oid] = {"area_px": area, "bbox": list(box), "uncertain_px": int(r["uncertain"].sum()),
                      "uncertain_bbox": list(ubox) if ubox is not None else None,
                      "rings": len(entry.get("rings") or []), "vertices": sum(len(x) for x in entry.get("rings") or []),
                      "uncertain_rings": len(entry.get("uncertain_rings") or [])}
    return {"file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "persons": stats,
            "errors": errors, "valid": not errors}


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        raise SystemExit(__doc__)
    report = check(Path(args[0]))
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
