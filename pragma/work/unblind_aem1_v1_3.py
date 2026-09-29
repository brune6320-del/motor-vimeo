"""Desciegue y análisis de la corrida A-E(−1) v1.3 `20260926T040705Z_bee282c1` (protocolo v2 rev. 1, paso 7).

    python3 work/unblind_aem1_v1_3.py --zip <ZIP> --mapping <sealed_mapping.json local>

Necesita la foto (núcleos oscuros del moño). Reproduce todo lo que se publica en
``auditoria/aem1v13_20260926T040705Z_bee282c1/``:

- el mapeo desciegado;
- la comparación de llaves;
- la adjudicación técnica;
- el análisis prerregistrado (código congelado);
- los descriptivos exploratorios, marcados como tales.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pragma_ae import aem1_v13 as v  # noqa: E402
from pragma_ae import aem1_v13_audit as audit  # noqa: E402
from pragma_ae.imageio import load_rgb, locate_image  # noqa: E402
from pragma_ae.masks import components, mask_iou  # noqa: E402

RUN = ROOT / "auditoria" / "aem1v13_20260926T040705Z_bee282c1"
PREREG = ROOT / "aem1" / "PRERREGISTRO_A-E-menos-1_v1_3.json"
BASE_REF = ROOT / "auditoria" / "aem1_20260925T062504Z_256dba9f" / "BASE_V2_REFERENCE.json"
MAPPING_SHA256 = "e1986a2b4ddad61eb0b171cf474797bfea045149ee027801b8ea65b80730c63f"
COMMITTED_CLAUDE_SHA256 = "8dde158be90e90b25167024d5ad94eb254bf06bf217a88fba3098841d0ed57bf"
PACKAGE_SHA256 = "a77a47b5c1e93bbc896dcd7b775afc22fef6ccc54ead8748b7e08c0f34a8051e"

# Regla de medición para other_person_excluded, fijada ANTES de calcular ninguna cifra:
# un píxel de máscara dentro de un núcleo de la persona posterior (≥ 10 px de la frontera
# ambigua) basta para FALSE. Núcleos: material oscuro (luma < 110 tras media 9×9) del moño y
# hombro/blusa floral, recortado para no tocar los mechones ambiguos.
BUN_CORE = (2610, 315, 2780, 415)          # ∩ material oscuro (la esquina superior izquierda es pared clara)
BUN_EXTENDED = (2590, 300, 2800, 425)      # ∩ material oscuro; solo informativo
SHOULDER_CORE = (2400, 840, 2520, 990)
O_POINTS = {"O1": (2460, 860), "O2": (2700, 380), "O3": (2735, 360), "O4": (2325, 965)}

ADJUDICATION_RATIONALE = {
    "C03.other_person_excluded": "medicion",
    "C05.other_person_excluded": "medicion_provisional",
    "C07.other_person_excluded": "medicion_provisional",
    "C05.target_hair_included": "regla_prerregistrada",
    "C15.target_dark_sleeves_included": "regla_prerregistrada",
}


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def measure_o(mask, dark) -> dict:
    def count(box, use_dark):
        x1, y1, x2, y2 = box
        sub = mask[y1:y2, x1:x2]
        if use_dark:
            sub = sub & dark[y1:y2, x1:x2]
        comps = [c["area"] for c in components(sub)] if sub.any() else []
        return {"px": int(sub.sum()), "islands": len(comps), "largest": max(comps) if comps else 0}
    # Corrección declarada tras medir: el borde inferior del núcleo hombro/blusa (y ≥ 980) toca el
    # hombro de la propia chica. Se reportan aparte las islas que NO tocan esa fila inferior.
    sx1, sy1, sx2, sy2 = SHOULDER_CORE
    sub = mask[sy1:sy2, sx1:sx2]
    separate = [c["area"] for c in components(sub) if c["bbox"][3] < sy2 - sy1] if sub.any() else []
    return {"bun_core": count(BUN_CORE, True), "shoulder_core": count(SHOULDER_CORE, False),
            "shoulder_core_separate_islands": {"px": int(sum(separate)), "islands": len(separate)},
            "bun_extended": count(BUN_EXTENDED, True),
            "o_coverage": {sid: round(v.patch_coverage(mask, xy), 4) for sid, xy in O_POINTS.items()}}


def islands_near_head(mask, box=(2200, 280, 2900, 1100), min_area=3) -> list:
    x1, y1, x2, y2 = box
    comps = sorted(components(mask[y1:y2, x1:x2]), key=lambda c: -c["area"])
    return [{"area_px": c["area"], "bbox": [c["bbox"][0] + x1, c["bbox"][1] + y1, c["bbox"][2] + x1, c["bbox"][3] + y1]}
            for c in comps[1:] if c["area"] >= min_area]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    args = parser.parse_args(argv)

    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    for path, digest in prereg["analysis_implementation_sha256"].items():
        if sha(ROOT / path) != digest:
            raise SystemExit(f"{path} cambió después del prerregistro: el análisis no sería el congelado")
    if sha(args.mapping) != MAPPING_SHA256:
        raise SystemExit("mapeo sellado distinto del registrado")
    first_path, second_path = RUN / "juicios_claude_crudos_v13.json", RUN / "segunda_llave_chatgpt_v13.json"
    if sha(first_path) != COMMITTED_CLAUDE_SHA256:
        raise SystemExit("los juicios de Claude no coinciden con el hash comprometido")
    first = json.loads(first_path.read_text(encoding="utf-8"))
    second = json.loads(second_path.read_text(encoding="utf-8"))
    if second["package_sha256"] != PACKAGE_SHA256:
        raise SystemExit("la segunda llave no juzgó el paquete registrado")
    mapping = json.loads(args.mapping.read_text(encoding="utf-8"))
    base_ref = json.loads(BASE_REF.read_text(encoding="utf-8"))
    cid = {label: row["candidate_id"] for label, row in mapping["mapping"].items()}

    # 1. Comparación celda a celda.
    cells, agree, disagreements = {}, {"criteria": 0, "aux": 0, "holes": 0}, []
    totals = {"criteria": 0, "aux": 0, "holes": 0}
    for label in sorted(first["candidates"]):
        a, b = first["candidates"][label], second["candidates"][label]
        row = {}
        for group in ("criteria", "aux"):
            for field, value in a[group].items():
                totals[group] += 1
                same = b[group][field] == value
                agree[group] += same
                row[field] = {"claude": value, "chatgpt": b[group][field], "agree": same}
                if not same:
                    disagreements.append({"label": label, "candidate_id": cid[label], "field": field,
                                          "claude": value, "chatgpt": b[group][field]})
        for number, value in a["holes"].items():
            totals["holes"] += 1
            agree["holes"] += b["holes"].get(number) == value
        cells[label] = row

    # 2. Adjudicación técnica: medición con la regla fijada antes de medir.
    photo = load_rgb(locate_image())
    dark = v.dark_map(v.gray_of(photo))
    blobs = audit._read(args.zip)
    blind_ids = list(cid.values())
    masks = audit.load_masks(blobs, blind_ids)
    measurements = {label: measure_o(masks[cid[label]], dark) for label in sorted(cid)}
    head_islands = {label: islands_near_head(masks[cid[label]]) for label in ("C03", "C05", "C07")}

    def o_value(label):
        m = measurements[label]
        raw = "FALSE" if (m["bun_core"]["px"] or m["shoulder_core"]["px"]) else "TRUE"
        corrected = "FALSE" if (m["bun_core"]["px"] or m["shoulder_core_separate_islands"]["px"]) else "TRUE"
        if raw != corrected:
            raise SystemExit(f"{label}: la corrección del núcleo cambiaría la adjudicación; revisar a mano")
        return corrected

    adjudications = {}
    for label in ("C03", "C05", "C07"):
        m = measurements[label]
        adjudications[(cid[label], "other_person_excluded")] = {
            "value": o_value(label), "kind": ADJUDICATION_RATIONALE[f"{label}.other_person_excluded"],
            "evidence": {"bun_core": m["bun_core"], "shoulder_core": m["shoulder_core"],
                         "bun_extended": m["bun_extended"], "o_coverage": m["o_coverage"],
                         "largest_islands_head_zone": head_islands[label][:6]}}
    for label, field in (("C05", "target_hair_included"), ("C15", "target_dark_sleeves_included")):
        adjudications[(cid[label], field)] = {
            "value": "NO_CONSENSO", "kind": "regla_prerregistrada",
            "evidence": "las auxiliares solo cuentan si son TRUE en ambas llaves (H-C1, H-G1, H-G4) y no deciden aceptación"}

    # 3. Análisis prerregistrado con el código congelado.
    analysis = audit.analyze(args.zip, prereg, base_ref, mapping, first, second, adjudications)

    # 4. Mejor intento (protocolo v2 §5.4): menos criterios no TRUE sumando llaves; desempates:
    #    más sentinelas KEEP cumplidos, orden de etiqueta.
    def non_true(label):
        return sum(analysis["reconciled"][key][cid[label]]["values"][c] != "TRUE"
                   for key in ("claude", "chatgpt") for c in audit.CRITERIA)
    ranking = sorted(cid, key=lambda lab: (non_true(lab), len(analysis["sentinels"][cid[lab]]["missed_keep"]), lab))
    best = ranking[0]

    # 5. Exploratorio (NO prerregistrado): estabilidad entre semillas por rama y área de agujeros D.
    x1, y1, x2, y2 = v.CONTACT_BOX
    chains = [f"{b}|{p}" for b in ("BASE", "+POS_HAIR", "+POS_SLEEVE", "+POS_HAIR+SLEEVE")
              for p in ("point+corrections", "box+corrections")]
    seed_masks = audit.load_masks(blobs, [f"{c}|s{k}" for c in chains for k in range(3)])
    seed_stability = {}
    for chain in chains:
        g = [seed_masks[f"{chain}|s{k}"] for k in range(3)]
        crops = [m[y1:y2, x1:x2] for m in g]
        pairs = [(0, 1), (0, 2), (1, 2)]
        seed_stability[chain] = {
            "iou_contact_s01_s02_s12": [round(mask_iou(crops[i], crops[j]), 3) if (crops[i].any() or crops[j].any()) else None
                                        for i, j in pairs],
            "iou_global_s01_s02_s12": [round(mask_iou(g[i], g[j]), 3) for i, j in pairs],
            "empty_in_contact": [k for k in range(3) if not crops[k].any()]}
    d_area = {label: sum(h["area_px"] for h in mapping["holes"][label]
                         if first["candidates"][label]["holes"].get(str(h["number"])) == "D"
                         and second["candidates"][label]["holes"].get(str(h["number"])) == "D")
              for label in sorted(cid)}

    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / "mapeo_desciegado.json").write_bytes(args.mapping.read_bytes())
    double_key = {
        "schema": "pragma.aem1v13_double_key", "schema_version": "0.1.0",
        "first_key": {"file": first_path.name, "sha256": sha(first_path), "committed_in": "abd3f32"},
        "second_key": {"file": second_path.name, "sha256": sha(second_path), "package_sha256_echoed": second["package_sha256"]},
        "blindness": "TEMPORAL_DOBLE: ChatGPT recibió solo el paquete y su LEEME; Claude comprometió sus juicios por hash antes",
        "agreement": {k: f"{agree[k]}/{totals[k]}" for k in agree},
        "agreement_all_cells": f"{agree['criteria'] + agree['aux']}/{totals['criteria'] + totals['aux']}",
        "cells": cells, "disagreements": disagreements,
        "technical_adjudication": {f"{k[0]}.{k[1]}": val for k, val in adjudications.items()},
        "o_rule": ("fijada antes de medir: FALSE si hay algún píxel de máscara en el núcleo oscuro del moño "
                   f"{BUN_CORE} o en el núcleo hombro/blusa {SHOULDER_CORE}; en otro caso TRUE"),
        "o_measurements_all": measurements,
        "core_geometry_note": ("corrección declarada tras medir: el borde inferior del núcleo hombro/blusa (y 980–990) toca el "
                               "hombro de la chica; los píxeles allí pertenecen a la componente principal de la chica "
                               "(verificado por conectividad hasta y = 1149) y no son inclusión posterior. Solo cuentan las islas "
                               "separadas (C04: 179 px; C06: 14 px). Ninguna adjudicación cambia: C03 es FALSE por su isla de "
                               "5 px dentro del núcleo del moño; C05 y C07 tienen 0 px en todos los núcleos."),
        "phone_hole_note": ("las dos llaves marcan L el agujero de la mano que cuelga; Claude lo describe como el teléfono "
                            "sostenido y ChatGPT como hueco entre mano y torso/overol: misma etiqueta, descripción distinta"),
        "verdict_relevance": "ninguna discrepancia cambia el veredicto: body_and_edges_complete es FALSE en las 18 en ambas llaves",
    }
    (RUN / "doble_llave_v13.json").write_text(json.dumps(double_key, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    public = {
        "schema": "pragma.aem1v13_analysis_public", "schema_version": "0.1.0",
        "prereg_content_sha256": prereg["content_sha256"],
        "analysis_code_frozen": prereg["analysis_implementation_sha256"],
        "case_status": analysis["case_status"], "passing": analysis["passing"],
        "best_attempt": {"label": best, "candidate_id": cid[best],
                         "ranking_top5": [{"label": lab, "candidate_id": cid[lab], "non_true_both_keys": non_true(lab),
                                           "keep_missed": analysis["sentinels"][cid[lab]]["missed_keep"]} for lab in ranking[:5]]},
        "base_reproduction": analysis["base_reproduction"],
        "hypotheses": analysis["hypotheses"],
        "reciprocal": analysis["reciprocal"],
        "perturbation": analysis["perturbation"],
        "ownership": analysis["ownership"], "leaks_bun": analysis["leaks_bun"], "interpretation": analysis["interpretation"],
        "consensus": analysis["consensus"], "sentinels": analysis["sentinels"],
        "sam2_rejectable": False, "project_status": analysis["project_status"],
        "exploratory_not_preregistered": {"seed_stability_per_chain": seed_stability, "d_hole_area_px_both_keys": d_area},
    }
    (RUN / "aem1v13_analisis.json").write_text(json.dumps(public, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("caso:", public["case_status"], "· mejor intento:", best, cid[best])
    print("acuerdo:", double_key["agreement"], "· hipótesis:", public["hypotheses"])
    print("recíproco:", public["reciprocal"]["stability"]["label"], "R_ref cubre moño:", public["reciprocal"]["covers_bun"])


if __name__ == "__main__":
    main()
