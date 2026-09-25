"""Auditoría ciega de A-E(−1) según auditoria/PROTOCOLO_AUDITORIA_AEM1_v1.md.

    python3 work/blind_audit_aem1.py prepare <ZIP>     # láminas A–L + mapeo sellado (solo imprime su hash)
    python3 work/blind_audit_aem1.py unblind <ZIP> <juicios_crudos.json> <salida_dir_repo>

`prepare` no imprime nada que identifique protocolo, semilla o score. Las láminas y el mapeo
quedan en local/ (derivan de la foto); en el repositorio solo entran hashes, juicios y tablas.
"""

import hashlib
import io
import json
import secrets
import string
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pragma_ae.aem1_audit import CRITERIA, audit_zip, write_verdict  # noqa: E402
from pragma_ae.imageio import load_rgb, locate_image  # noqa: E402
from pragma_ae.masks import dilate_square  # noqa: E402

PROTOCOL = ROOT / "auditoria" / "PROTOCOLO_AUDITORIA_AEM1_v1.md"
PROTOCOL_SHA256 = "436937d45b86d8e236eb625274a29e42653285437af644f5d3845968c0240810"
CONTACT_BOX = (2150, 250, 2900, 1300)
REGIONS = [  # (nombre, caja) · mismas ventanas para todas las etiquetas
    ("cabeza_y_pelo_recogido", (2450, 250, 3150, 900)),
    ("contacto_posterior", (2150, 650, 2700, 1300)),
    ("mano_levantada", (2850, 550, 3500, 1450)),
    ("mano_colgante", (2000, 1750, 2500, 2248)),
    ("costado_derecho", (3100, 850, 3550, 1650)),
]
OVERVIEW_BOX = (2000, 200, 3650, 2248)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_dir(zip_path: Path) -> Path:
    return ROOT / "local" / "audit" / zip_path.stem


def masks_from_zip(zip_path, auto):
    with zipfile.ZipFile(zip_path) as archive:
        for row in auto["candidates"]:
            with Image.open(io.BytesIO(archive.read(row["alpha_file"]))) as handle:
                yield row, np.asarray(handle.convert("L")) > 0


def shade(photo, mask, box):
    """Recorte a 1:1: fuera de la máscara oscurecido; borde interior real en magenta (no el del recorte)."""
    x1, y1, x2, y2 = box
    h, w = mask.shape
    ex1, ey1, ex2, ey2 = max(0, x1 - 1), max(0, y1 - 1), min(w, x2 + 1), min(h, y2 + 1)
    extended = mask[ey1:ey2, ex1:ex2]
    edge = (extended & dilate_square(~extended, 1))[y1 - ey1:y1 - ey1 + (y2 - y1), x1 - ex1:x1 - ex1 + (x2 - x1)]
    crop = photo[y1:y2, x1:x2].astype(np.float32)
    m = mask[y1:y2, x1:x2]
    view = np.where(m[..., None], crop, crop * 0.28)
    view[edge] = (255, 0, 255)
    return Image.fromarray(view.astype(np.uint8))


def blind_sheet(photo, mask, label, out_path):
    overview = shade(photo, mask, OVERVIEW_BOX)
    overview = overview.resize((520, round(overview.height * 520 / overview.width)), Image.LANCZOS)
    tiles = {name: shade(photo, mask, box) for name, box in REGIONS}
    row1 = [("vista_completa (reducida)", overview), ("cabeza_y_pelo_recogido", tiles["cabeza_y_pelo_recogido"]),
            ("contacto_posterior", tiles["contacto_posterior"])]
    row2 = [("mano_levantada", tiles["mano_levantada"]), ("mano_colgante", tiles["mano_colgante"]),
            ("costado_derecho", tiles["costado_derecho"])]
    header, gap = 22, 8

    def row_size(row):
        return sum(t.width for _, t in row) + gap * (len(row) - 1), max(t.height for _, t in row) + header

    w = max(row_size(row1)[0], row_size(row2)[0])
    h = 40 + row_size(row1)[1] + gap + row_size(row2)[1]
    sheet = Image.new("RGB", (w, h), (20, 20, 20))
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 12), f"CANDIDATA {label}  (ciega: sin protocolo, semilla ni score)", fill=(255, 255, 0))
    y = 40
    for row in (row1, row2):
        x = 0
        for name, tile in row:
            draw.text((x + 4, y + 4), name, fill=(230, 230, 230))
            sheet.paste(tile, (x, y + header))
            x += tile.width + gap
        y += row_size(row)[1] + gap
    sheet.save(out_path)


def prepare(zip_path):
    zip_path = Path(zip_path)
    if sha(PROTOCOL.read_bytes()) != PROTOCOL_SHA256:
        raise SystemExit("El protocolo congelado cambió: no se prepara la auditoría")
    photo = load_rgb(locate_image())
    auto = audit_zip(zip_path, photo=photo, out_dir=None)   # sin láminas con nombres
    if not auto["integrity"]["pass"] or auto["run_kind"] != "REAL_GPU":
        raise SystemExit(f"No auditable: integridad={auto['integrity']} run_kind={auto['run_kind']}")
    out = run_dir(zip_path) / "blind"
    out.mkdir(parents=True, exist_ok=True)
    labels = list(string.ascii_uppercase[:len(auto["candidates"])])
    order = list(range(len(auto["candidates"])))
    secrets.SystemRandom().shuffle(order)
    mapping, blind_metrics, rows = {}, {}, list(auto["candidates"])
    masks = {id(row): mask for row, mask in masks_from_zip(zip_path, auto)}
    for label, index in zip(labels, order):
        row = rows[index]
        mapping[label] = {"key": row["key"], "candidate_index": row["candidate_index"], "alpha_file": row["alpha_file"],
                          "packed_mask_sha256": row["packed_mask_sha256"]}
        blind_metrics[label] = {k: row[k] for k in ("sentinels", "sentinel_screen_pass", "components",
                                                    "largest_component_share", "holes", "holes_area_px", "regions")}
        blind_sheet(photo, masks[id(row)], label, out / f"candidata_{label}.png")
    mapping_bytes = json.dumps(mapping, indent=2, sort_keys=True).encode()
    (run_dir(zip_path) / "sealed_mapping.json").write_bytes(mapping_bytes)
    (run_dir(zip_path) / "blind_metrics.json").write_text(json.dumps(blind_metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    (run_dir(zip_path) / "auto.json").write_text(json.dumps(auto, indent=2, ensure_ascii=False), encoding="utf-8")
    sheets = {p.name: sha(p.read_bytes()) for p in sorted(out.glob("candidata_*.png"))}
    print(json.dumps({"sealed_mapping_sha256": sha(mapping_bytes), "labels": labels, "blind_sheets": len(sheets),
                      "protocol_sha256": PROTOCOL_SHA256, "zip_sha256": auto["zip_sha256"]}, indent=2))


def pairwise_contact_iou(masks):
    x1, y1, x2, y2 = CONTACT_BOX
    crops = {k: m[y1:y2, x1:x2] for k, m in masks.items()}
    result = {}
    keys = sorted(crops)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            inter = np.logical_and(crops[a], crops[b]).sum()
            union = np.logical_or(crops[a], crops[b]).sum()
            result[(a, b)] = float(inter / union) if union else None
    return result, {k: int(c.sum()) for k, c in crops.items()}


def unblind(zip_path, judgments_path, repo_out):
    zip_path, judgments_path, repo_out = Path(zip_path), Path(judgments_path), Path(repo_out)
    judgments = json.loads(judgments_path.read_text(encoding="utf-8"))
    base = run_dir(zip_path)
    mapping_bytes = (base / "sealed_mapping.json").read_bytes()
    if sha(mapping_bytes) != judgments["sealed_mapping_sha256"]:
        raise SystemExit("El mapeo sellado no coincide con el registrado en los juicios")
    mapping = json.loads(mapping_bytes)
    blind_metrics = json.loads((base / "blind_metrics.json").read_text(encoding="utf-8"))
    auto = json.loads((base / "auto.json").read_text(encoding="utf-8"))

    table = []
    for label in sorted(mapping):
        raw = judgments["candidates"][label]
        final = {c: raw["criteria"][c] == "TRUE" for c in CRITERIA}
        reconciled = []
        s = blind_metrics[label]["sentinels"]
        for field, ids in (("body_and_edges_complete", s["missed_keep"]),
                           ("other_person_excluded", s["leaked_other_person"]),
                           ("background_excluded", s["leaked_background"])):
            if ids and final[field]:
                final[field] = False
                reconciled.append(f"{field}: TRUE→FALSE por sentinelas {ids}")
        table.append({"label": label, **mapping[label], "raw": raw["criteria"], "final": final,
                      "passes": all(final.values()), "defects": raw.get("defects", []), "notes": raw.get("notes", ""),
                      "reconciliation": reconciled, "sentinels": s})

    # Sonda de riesgo de contacto (solo reporte).
    masks = {}
    with zipfile.ZipFile(zip_path) as archive:
        for row in table:
            with Image.open(io.BytesIO(archive.read(row["alpha_file"]))) as handle:
                masks[f"{row['key']}#{row['candidate_index']}"] = np.asarray(handle.convert("L")) > 0
    ious, pixels = pairwise_contact_iou(masks)
    other_ok = {f"{r['key']}#{r['candidate_index']}" for r in table if r["final"]["other_person_excluded"]}

    def group(filter_pair):
        pairs = {f"{a} ↔ {b}": v for (a, b), v in ious.items() if filter_pair(a, b)}
        if any(v is None for v in pairs.values()) or not pairs:
            return {"label": "NOT_EVALUABLE", "pairs": pairs}
        conflict = any(v < 0.75 and a in other_ok and b in other_ok
                       for (a, b), v in ious.items() if filter_pair(a, b))
        worst = min(pairs.values())
        label = "CONFLICT" if conflict else ("STABLE" if worst >= 0.90 else "UNSTABLE")
        return {"label": label, "min_iou": round(worst, 4), "pairs": {k: round(v, 4) for k, v in pairs.items()}}

    seed = lambda base_: (lambda a, b: a.startswith(base_ + "+corrections") and b.startswith(base_ + "+corrections"))
    cross = lambda a, b: ("point+corrections" in a and "box+corrections" in b) or ("box+corrections" in a and "point+corrections" in b)
    contact = {"box": CONTACT_BOX, "pixels_in_box": pixels,
               "point_seeds": group(seed("point")), "box_seeds": group(seed("box")), "point_vs_box": group(cross),
               "note": "CONTACT_RISK_PROBE: estabilidad, no exactitud. Nunca decide aceptación (protocolo §5)."}

    passing = [r for r in table if r["passes"]]
    pool = passing or table
    chosen = sorted(pool, key=lambda r: (sum(not v for v in r["final"].values()), len(r["defects"]), r["label"]))[0]
    selected = f"{chosen['key']}#{chosen['candidate_index']}"
    verdict = write_verdict(
        auto, selected, chosen["final"],
        notes="; ".join(chosen["defects"]) or chosen["notes"],
        auditor="Claude Code · auditoría ciega según auditoria/PROTOCOLO_AUDITORIA_AEM1_v1.md",
        reasoning=[f"Etiqueta ciega {chosen['label']}", f"{len(passing)} de {len(table)} candidatas pasan los cuatro criterios",
                   "selección por reglas del protocolo §6 (defectos y etiqueta), nunca por score"],
        cross_audit={"by": "ChatGPT", "status": "PENDIENTE", "material": "láminas ciegas A–L sin mapeo"},
    )
    verdict["protocol_sha256"] = PROTOCOL_SHA256
    verdict["raw_judgments_sha256"] = sha(judgments_path.read_bytes())
    verdict["sealed_mapping_sha256"] = judgments["sealed_mapping_sha256"]
    verdict["passing_candidates"] = [f"{r['key']}#{r['candidate_index']}" for r in passing]
    verdict["contact_risk_probe"] = contact
    repo_out.mkdir(parents=True, exist_ok=True)
    (repo_out / "aem1_audit_verdict.json").write_text(json.dumps(verdict, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    public_table = [{k: r[k] for k in ("label", "key", "candidate_index", "packed_mask_sha256", "raw", "final", "passes",
                                        "defects", "reconciliation", "sentinels")} for r in table]
    (repo_out / "aem1_tabla_desciegada.json").write_text(json.dumps({"mapping_sha256": judgments["sealed_mapping_sha256"],
                                                                      "candidates": public_table}, indent=2, ensure_ascii=False) + "\n",
                                                         encoding="utf-8")
    print(json.dumps({"case_status": verdict["case_status"], "selected": selected, "selected_label": chosen["label"],
                      "passing": verdict["passing_candidates"], "contact": {k: contact[k]["label"] for k in
                                                                            ("point_seeds", "box_seeds", "point_vs_box")}},
                     indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if sys.argv[1] == "prepare":
        prepare(sys.argv[2])
    elif sys.argv[1] == "unblind":
        unblind(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        raise SystemExit(__doc__)
