"""Diseño cerrado de A-E(−1) v1.4 → prerregistro determinista (sin SAM 2 y sin GPU).

Uso:
    python3 work/design_aem1_v1_4.py            # necesita la foto y el ZIP local de la corrida v1.3
    python3 work/design_aem1_v1_4.py --check    # recalcula y comprueba que el JSON versionado no cambió

Escribe:
- ``aem1/PRERREGISTRO_A-E-menos-1_v1_4.json`` (versionado: coordenadas, reglas, hashes y cifras);
- ``local/aem1_v1_4_diseno/`` (privado: lámina de diseño y hoja de contactos de H2 y sus perturbaciones).

Un solo cambio respecto de v1.3 (ChatGPT 005 §4): el positivo H2, añadido a la cadena ganadora
``+POS_HAIR+SLEEVE|box+corrections`` con sus tres semillas. H2 no se elige a mano: la región son los
píxeles que las dos llaves de v1.3 marcaron como agujero D en las **tres** semillas de referencia, y
dentro de ella se aplica la misma regla de cuadrado seguro que eligió H1 y S1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pragma_ae import EXPECTED_IMAGE_SHA256, EXPECTED_IMAGE_SIZE  # noqa: E402
from pragma_ae import aem1_v13 as v13  # noqa: E402
from pragma_ae import aem1_v13_audit as a13  # noqa: E402
from pragma_ae import aem1_v14 as w  # noqa: E402
from pragma_ae.imageio import load_rgb, locate_image  # noqa: E402
from pragma_ae.preflight import sentinel_contact_sheet  # noqa: E402

V13_PREREG = ROOT / "aem1" / "PRERREGISTRO_A-E-menos-1_v1_3.json"
V13_RUN = ROOT / "auditoria" / "aem1v13_20260926T040705Z_bee282c1"
V13_ZIP = ROOT / "local" / "runs" / "PRAGMA_AEM1v13_20260926T040705Z_bee282c1_PENDING_EXTERNAL_AUDIT.zip"
V13_ZIP_SHA256 = "6d795132cd8e609388cdb1b3671dee7e0d1c39067880cfb0ca6a1b1a6783ce14"
LETTER_005 = ROOT / "dialogo" / "005_chatgpt_a_claude.md"
PROTOCOL_V2 = ROOT / "auditoria" / "PROTOCOLO_AUDITORIA_AEM1_v2.md"
ANALYSIS_CODE = ["pragma_ae/aem1_v14.py", "pragma_ae/aem1_v14_audit.py",
                 "pragma_ae/aem1_v13.py", "pragma_ae/aem1_v13_audit.py", "pragma_ae/masks.py"]
OUT_JSON = ROOT / "aem1" / "PRERREGISTRO_A-E-menos-1_v1_4.json"
OUT_LOCAL = ROOT / "local" / "aem1_v1_4_diseno"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(payload: dict) -> str:
    body = {k: val for k, val in payload.items() if k != "content_sha256"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def reference_from_v13(dark):
    """Máscaras de referencia de v1.3, sus agujeros D de consenso y los juicios congelados por semilla."""
    if sha(V13_ZIP) != V13_ZIP_SHA256:
        raise SystemExit("el ZIP local de v1.3 no es el auditado")
    prereg13 = json.loads(V13_PREREG.read_text(encoding="utf-8"))
    mapping = json.loads((V13_RUN / "mapeo_desciegado.json").read_text(encoding="utf-8"))
    first = json.loads((V13_RUN / "juicios_claude_crudos_v13.json").read_text(encoding="utf-8"))
    second = json.loads((V13_RUN / "segunda_llave_chatgpt_v13.json").read_text(encoding="utf-8"))
    analysis = json.loads((V13_RUN / "aem1v13_analisis.json").read_text(encoding="utf-8"))
    closure = json.loads((V13_RUN / "cierre_chatgpt005.json").read_text(encoding="utf-8"))
    label_of = {row["candidate_id"]: label for label, row in mapping["mapping"].items()}
    blobs = a13._read(V13_ZIP)
    manifest = json.loads(blobs[a13.MANIFEST])
    ref_ids = w.seed_ids(w.REF_BRANCH)
    base_ids = [f"BASE|box|{k}" for k in w.SEEDS]
    masks = a13.load_masks(blobs, ref_ids)
    packed = {cid: manifest["masks"][cid] for cid in base_ids + ref_ids}
    for cid in ref_ids:
        if a13.packed_sha256(masks[cid]) != packed[cid]:
            raise SystemExit(f"{cid}: la máscara no coincide con el manifiesto de v1.3")
    defect, judgments, holes_by_seed = {}, {}, {}
    for k, cid in enumerate(ref_ids):
        label = label_of[cid]
        holes = a13.holes_with_masks(masks[cid])
        d_numbers = [str(h["number"]) for h in holes
                     if first["candidates"][label]["holes"].get(str(h["number"])) == "D"
                     and second["candidates"][label]["holes"].get(str(h["number"])) == "D"]
        defect[k] = [h["mask"] for h in holes if str(h["number"]) in d_numbers]
        holes_by_seed[k] = holes
        screen = a13.sentinel_screen(masks[cid], prereg13["base_config"])
        keys = {}
        for key, raw in (("claude", first), ("chatgpt", second)):
            judgment = raw["candidates"][label]
            values, _ = a13.reconcile(a13._flat(judgment), screen, judgment.get("holes", {}))
            keys[key] = {c: values[c] for c in a13.CRITERIA}
        consensus = analysis["consensus"][cid]
        judgments[f"s{k}"] = {
            "candidate_id": cid, "v1_3_label": label,
            **{c: consensus[c] for c in a13.CRITERIA},
            "d_holes": d_numbers,
            "holes": [{"number": h["number"], "area": h["area"], "bbox": list(h["bbox"]),
                       "consensus": "D" if str(h["number"]) in d_numbers else "L"} for h in holes],
            "o_core_px": w.measure_o(masks[cid], dark)["core_px"],
            "keys_v1_3": keys,
        }
    return prereg13, masks, packed, defect, judgments, holes_by_seed, closure


def build(image, gray, dark):
    prereg13, ref_masks, packed, defect, judgments, holes_by_seed, closure = reference_from_v13(dark)
    base_config = prereg13["base_config"]
    holdouts = {s["id"]: s["xy"] for g in base_config["holdouts"].values() for s in g}
    prompts = {s["id"]: s["xy"] for s in base_config["prompts"]}
    prompts.update({k: prereg13["new_prompts"][k]["xy"] for k in ("H1", "S1")})
    size = EXPECTED_IMAGE_SIZE

    region = w.common_defect_region(defect)
    chosen = w.select_point_in_region(dark, region, list(holdouts.values()), list(prompts.values()))
    if chosen is None:
        raise SystemExit("H2: ninguna posición de la región cumple las restricciones")
    xy = chosen["xy"]
    ys, xs = np.nonzero(region)
    near_h = min(holdouts, key=lambda k: v13.distance(xy, holdouts[k]))
    near_p = min(prompts, key=lambda k: v13.distance(xy, prompts[k]))
    targets = {}
    for k, cid in enumerate(w.seed_ids(w.REF_BRANCH)):
        t = w.hole_containing(ref_masks[cid], xy)
        u = w.hole_containing(ref_masks[cid], w.UPPER_PROBE)
        targets[f"s{k}"] = {"target_hole": {"number": t["number"], "area": t["area"], "bbox": list(t["bbox"])},
                            "upper_probe_hole": None if u is None else {"number": u["number"], "area": u["area"],
                                                                        "bbox": list(u["bbox"])}}
    h2 = {
        "xy": xy,
        "owner_expected": "chica",
        "material": "pelo oscuro visible entre la cara y el índice levantado (parte baja de la franja)",
        "region_rule": ("píxeles que las dos llaves de v1.3 marcaron como agujero D (consenso) en las TRES semillas de "
                        "referencia +POS_HAIR+SLEEVE|box+corrections"),
        "region": {"px": int(region.sum()), "bbox_xyxy": [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1],
                   "packed_sha256": a13.packed_sha256(region)},
        "selection_rule": ("pragma_ae.aem1_v14.select_point_in_region: rejilla par; mayor cuadrado seguro ≥ 98 % oscuro; "
                           "empates por fracción oscura, margen a la caja de contacto, menor y, menor x"),
        "safe_square_half_min_px": w.H2_SAFE_HALF_MIN,
        "safe_square_half_px": chosen["safe_half"],
        "safe_square_dark_fraction": chosen["safe_square_dark_fraction"],
        "why_smaller_than_H1_S1": ("la franja mide ~40 px de ancho: el mayor cuadrado seguro dentro de la región es de 31 px, "
                                   "por debajo del mínimo de 43 px de H1/S1. Consecuencia declarada: las perturbaciones que "
                                   "sacan el parche del pelo son INVALID_PERTURBATION y no se ejecutan"),
        "contact_box_margin_linf_px": chosen["contact_margin_linf"],
        "nearest_holdout": {"id": near_h, "distance_px": round(v13.distance(xy, holdouts[near_h]), 1)},
        "nearest_prompt": {"id": near_p, "distance_px": round(v13.distance(xy, prompts[near_p]), 1)},
        **v13.patch_stats(gray, xy),
        "image_sha256": EXPECTED_IMAGE_SHA256,
        "inside_target_hole_of_each_reference_seed": targets,
        "owner_verified_by": "auditor IA Claude en la lámina privada de diseño",
        "owner_second_key": "PENDIENTE (ChatGPT, en la lámina privada del paquete de la carta 006)",
    }
    perturbations = []
    for p in v13.point_perturbations(xy):
        ok, reasons = v13.validate_perturbed_point(p["xy"], size, list(holdouts.values()), dark=dark)
        perturbations.append({**p, "valid": ok, "reasons": reasons, **v13.patch_stats(gray, p["xy"])})
    n_valid = sum(r["valid"] for r in perturbations)

    new_prompts = {k: prereg13["new_prompts"][k] for k in ("H1", "S1")}
    new_prompts["H2"] = h2
    all_prompts = {**prompts, "H2": xy}
    call_plan = w.build_call_plan(all_prompts, base_config["BOX"], perturbations)
    counts = {"BASE|box": 3, "REF": 3, "H2": 3, "PERTURB_POINT": 3 * n_valid, "valid_point_perturbations": n_valid}
    counts["total_masks"] = sum(val for key, val in counts.items() if key != "valid_point_perturbations")
    if sum(len(c["candidates"]) for c in call_plan) != counts["total_masks"]:
        raise SystemExit("el plan de llamadas no produce el número de máscaras declarado")
    counts["calls"] = len(call_plan)
    for c in call_plan:
        if c["branch"] == w.REF_BRANCH:
            twin = next(p for p in prereg13["call_plan"] if p["call_id"] == c["call_id"])
            if any(c[f] != twin[f] for f in ("points", "labels", "box", "mask_input_from", "multimask_output", "candidates")):
                raise SystemExit(f"{c['call_id']}: la llamada de referencia no es idéntica a la de v1.3")

    payload = {
        "schema": "pragma.aem1_preregistration",
        "schema_version": "0.1.0",
        "experiment": "A-E(−1) v1.4 · caso chica · una sola intervención (H2)",
        "status": "PREREGISTERED",
        "frozen_on": "2026-09-26",
        "responds_to": ["dialogo/005_chatgpt_a_claude.md"],
        "go_to_preregistration": {
            "by": "ChatGPT", "letter": LETTER_005.relative_to(ROOT).as_posix(), "letter_sha256": sha(LETTER_005),
            "accepted": ["una sola intervención nueva", "cadena +POS_HAIR+SLEEVE · box+corrections", "tres semillas",
                         "referencia v1.3 obligatoriamente bit a bit", "H2 únicamente como positivo adicional",
                         "ningún otro cambio", "H-C3 congelada tal cual", "H-G5 añadida antes de los datos",
                         "PASS = contrato completo, no «H2 cerró el agujero»"],
            "cross_audit_before_run": "PENDIENTE: ChatGPT revisa este prerregistro antes de ejecutar (ChatGPT 005)",
        },
        "correction_of_letter_005": {
            "proposed": list(w.UPPER_PROBE),
            "problem": ("(2964, 672) está en la parte ALTA de la franja: agujero D solo en s0 y s2; C01 (s1) ya cubre esa "
                        "parte y su único agujero D es la parte BAJA (2984–3025 × 842–997). Con ese punto la hipótesis no "
                        "podía probarse en el mejor intento"),
            "fix": "H2 se elige dentro de los píxeles que son agujero D de consenso en las tres semillas (la parte baja)",
            "second_key_on_old_point": "ChatGPT 005 confirmó que el punto viejo es pelo de la chica; el nuevo requiere su llave",
            "upper_probe_role": "solo descriptivo: si la parte alta de s0 y s2 también se cierra",
        },
        "generated_by": "work/design_aem1_v1_4.py",
        "image": prereg13["image"],
        "sam2_freeze": {**prereg13["sam2_freeze"],
                        "reproducibility": "GPU NVIDIA L4, como la corrida 1 y v1.3 (la reproducción bit a bit se probó en L4)"},
        "base_config": base_config,
        "new_prompts": new_prompts,
        "safety_constants": prereg13["safety_constants"],
        "invalid_perturbation": prereg13["invalid_perturbation"],
        "reference": {
            "v1_3_run": "20260926T040705Z_bee282c1",
            "v1_3_zip_sha256": V13_ZIP_SHA256,
            "v1_3_prereg_content_sha256": prereg13["content_sha256"],
            "v1_3_closure": {"file": (V13_RUN / "cierre_chatgpt005.json").relative_to(ROOT).as_posix(),
                             "sha256": sha(V13_RUN / "cierre_chatgpt005.json"), "AEM1_v1_3": closure["AEM1_v1_3"]},
            "chain": f"{w.REF_BRANCH}|{w.PROTOCOL}",
            "v1_3_packed_mask_sha256": packed,
            "bit_exact_rule": ("BASE|box y las 3 semillas de referencia deben salir bit a bit iguales a v1.3. Si alguna no lo "
                               "es, la comparación de esa semilla usa la referencia de esta corrida y su consenso ciego"),
            "judgments": judgments,
        },
        "branches": {
            "BASE": {"purpose": "semillas: la misma llamada box (multimask) de v1.3", "protocols": {"box": "BOX, multimask, 3 salidas"}},
            w.REF_BRANCH: {"purpose": "referencia: la cadena ganadora de v1.3, idéntica llamada a llamada",
                           "points": ["P+1", "H1", "S1", "P-1", "P-2", "P-3"], "labels": [1, 1, 1, 0, 0, 0]},
            w.H2_BRANCH: {"purpose": "la intervención: H2 como cuarto positivo en la corrección; nada más cambia",
                          "points": ["P+1", "H1", "S1", "H2", "P-1", "P-2", "P-3"], "labels": [1, 1, 1, 1, 0, 0, 0]},
            "PERTURB_POINT": {"offsets_px": [list(o) for o in v13.POINT_OFFSETS], "linf_radius_px": v13.STEP,
                              "one_at_a_time": True,
                              "targets": {"H2": {"base": "H2", "base_xy": xy, "branch": w.H2_BRANCH,
                                                 "protocols": [w.PROTOCOL], "perturbations": perturbations,
                                                 "valid_count": n_valid,
                                                 "chain": "semillas de BASE sin cambios; solo H2 se perturba (H1 y S1 fijos)"}}},
        },
        "combination": "NINGUNA",
        "candidate_counts": counts,
        "call_plan": call_plan,
        "call_plan_semantics": prereg13["call_plan_semantics"],
        "analysis_implementation_sha256": {path: sha(ROOT / path) for path in ANALYSIS_CODE},
        "blind_audit": {
            "protocol": PROTOCOL_V2.relative_to(ROOT).as_posix(), "protocol_sha256": sha(PROTOCOL_V2),
            "candidates": "6 láminas N01–N06: las 3 semillas con H2 y las 3 de referencia, mezcladas al azar",
            "why_reference_is_included": ("señuelo y retest: la persona que juzga no sabe cuáles tienen H2, y se mide si cada "
                                          "llave repite su juicio de v1.3 sobre la misma máscara"),
            "reference_judgment_if_bit_exact": "la doble llave de v1.3 (congelada arriba); el retest solo describe",
            "not_blind_judged": ["BASE|box", "PERTURB_POINT"],
            "order": "el paquete va a ChatGPT antes que cualquier resultado; los juicios de Claude se comprometen por hash",
        },
        "adjudication_rules": {
            "other_person_excluded": ("discrepancia → medición prerregistrada: FALSE si hay píxeles de máscara en el núcleo "
                                      f"oscuro del moño {list(w.BUN_CORE)} o islas separadas en el núcleo hombro/blusa "
                                      f"{list(w.SHOULDER_CORE)}; si una llave cita material posterior fuera de los núcleos, "
                                      "con coordenadas, tercera revisión ciega (§5.2)"),
            "aux": "discrepancia → NO_CONSENSO (las auxiliares no deciden nada en v1.4)",
            "correct_subject, body_and_edges_complete, background_excluded": "protocolo v2 rev. 1 §5.2",
            "hole_D_L": "solo se adjudica si el agujero cuenta para H-G5 (agujero nuevo fuera de la región de H2); §5.2",
        },
        "metrics": {
            "target_hole": ("por semilla: el agujero cerrado ≥ 1000 px de la referencia que contiene H2; es evaluable si las "
                            "dos llaves lo marcaron D"),
            "closure": ("cerrado = quedan < 1000 px del agujero objetivo sin cubrir Y ningún agujero ≥ 1000 px de la "
                        "candidata lo toca (pragma_ae.aem1_v14.closure)"),
            "h2_region": "el agujero objetivo dilatado 15 px (L∞)",
            "new_d_hole": ("agujero ≥ 1000 px de la candidata, fuera de la región de H2, con ≥ 50 % de sus píxeles DENTRO "
                           "de la máscara de referencia (pérdida nueva, no material que ya faltaba) y D en las dos llaves"),
            "o_worse": ("referencia O TRUE y candidata O no TRUE; o, si la referencia ya era FALSE (s0: isla de 5 px en el "
                        "moño), más píxeles en los núcleos que la referencia"),
            "perturbation_stability": "pragma_ae.aem1_v13.perturbation_stability por semilla, más cierre bajo cada perturbación",
            "descriptive_only": ["cambio global (IoU global y fuera de la región, píxeles perdidos y ganados fuera)",
                                 "cierre de la parte alta de la franja en s0 y s2 (sonda (2964, 672))",
                                 "retest de cada llave sobre las máscaras de referencia"],
        },
        "hypotheses": [
            {"id": "H-C3", "by": "Claude (carta 005), congelada por ChatGPT 005", "function": "pragma_ae.aem1_v14.hypothesis_h_c3",
             "statement": "H2 cierra el agujero objetivo de la franja en ≥ 2 de 3 semillas sin empeorar O",
             "holds_if": "≥ 2 semillas evaluables con closure = cerrado y sin o_worse",
             "refuted_if": "aun contando como éxito las semillas no evaluables, no llegan a 2",
             "otherwise": "INDETERMINATE"},
            {"id": "H-G5", "by": "ChatGPT (carta 005)", "function": "pragma_ae.aem1_v14.hypothesis_h_g5",
             "statement": "H2 actúa como reparación local, no como resegmentación global",
             "holds_if": "≥ 2/3 semillas cerradas, ninguna con o_worse y ninguna con un agujero D nuevo fuera de la región de H2",
             "refuted_if": "≥ 2/3 semillas cerradas CON un agujero D nuevo, o ≥ 2/3 con o_worse",
             "otherwise": "INDETERMINATE",
             "role": "hipótesis causal y diagnóstica; NO es un quinto requisito de PASS"},
        ],
        "decision": {
            "acceptance": ("solo por el protocolo de auditoría v2 rev. 1 §5: los cuatro criterios TRUE en el consenso de las dos "
                           "llaves, más agujeros, sentinelas y adjudicación. Solo las candidatas con H2 pueden dar PASS. Cerrar "
                           "la franja no basta: si queda el mentón u otro D, es NO PASS (ChatGPT 005 §6)"),
            "case_labels": {"PASS_FULL_SUBJECT_UNDER_FIXED_AEM1_PROTOCOL": "alguna candidata con H2 pasa",
                            "INCONCLUSIVE_SELECTED_OUTPUT_FAILED": "ninguna pasa"},
            "stop_rule": ("A-E(−1) se cierra con v1.4 pase lo que pase: AEM1_CLOSED_DEMONSTRATED o AEM1_CLOSED_INCONCLUSIVE. "
                          "Otra iteración exige una decisión explícita de las dos IAs y de la persona usuaria (ChatGPT 005)"),
            "user_veto": True, "sam2_rejectable": False, "project_status": "INCONCLUSIVE_A_E0_REQUIRED", "phase_b": "BLOQUEADA",
            "scope_of_a_pass": "una foto, un caso, un protocolo fijo: no demuestra A-E1 ni generaliza",
        },
        "forbidden": [
            "cambiar H2, la caja, los umbrales o cualquier otro prompt después de ver datos de esta corrida",
            "elegir semilla, salida o candidata por score",
            "reparar máscaras (restas, uniones o rellenos): se juzga la salida de SAM 2 tal cual",
            "ejecutar un caso INVALID_PERTURBATION",
            "FastAPI, localhost, YOLO-seg o BiRefNet; tocar la extensión",
        ],
        "outputs": {
            "zip": "PRAGMA_AEM1v14_<run_id>_PENDING_EXTERNAL_AUDIT.zip",
            "contents": ["aem1v14_config.json (prerregistro embebido, entorno, compuertas y luma)",
                         "aem1v14_calls.json (las llamadas ejecutadas, en orden)", "aem1v14_manifest.json (bytes y SHA-256)",
                         "aem1v14_report.json", "masks/<candidata>.png para BASE, referencia y H2 (9)",
                         f"aem1v14_perturbaciones.npz ({3 * n_valid} máscaras en packbits)"],
            "not_shown_in_colab": "el cuaderno no muestra máscaras, áreas, scores ni sentinelas: solo progreso e integridad",
        },
    }
    payload["content_sha256"] = canonical_hash(payload)
    return payload, ref_masks, region, holes_by_seed


def _edge(mask):
    padded = np.pad(mask, 1)
    interior = padded[:-2, 1:-1] & padded[2:, 1:-1] & padded[1:-1, :-2] & padded[1:-1, 2:]
    return mask & ~interior


def design_sheets(image, payload, ref_masks, region):
    """Material privado para la segunda llave: H2, su cuadrado seguro, sus perturbaciones y los agujeros de referencia."""
    from PIL import Image, ImageDraw

    OUT_LOCAL.mkdir(parents=True, exist_ok=True)
    h2 = payload["new_prompts"]["H2"]
    tiles = [("H2", tuple(h2["xy"]), "prompt_positive", h2["material"])]
    for p in payload["branches"]["PERTURB_POINT"]["targets"]["H2"]["perturbations"]:
        tiles.append((f"H2{p['id']}", tuple(p["xy"]), "prompt_positive" if p["valid"] else "drop_background",
                      "perturbacion " + ("OK" if p["valid"] else "INVALIDA")))
    sentinel_contact_sheet(image, tiles, OUT_LOCAL / "hoja_contactos_H2_v1_4.png", columns=9)

    box = (2560, 520, 3200, 1100)
    x1, y1, x2, y2 = box
    panels = []
    raw_arr = np.ascontiguousarray(image[y1:y2, x1:x2]).copy()
    raw_arr[_edge(region[y1:y2, x1:x2])] = (255, 160, 0)
    raw = Image.fromarray(raw_arr)
    draw = ImageDraw.Draw(raw)
    x, y = h2["xy"]
    half = h2["safe_square_half_px"]
    draw.rectangle([x - half - x1, y - half - y1, x + half - x1, y + half - y1], outline=(0, 255, 0), width=2)
    for p in payload["branches"]["PERTURB_POINT"]["targets"]["H2"]["perturbations"]:
        px, py = p["xy"]
        draw.rectangle([px - x1 - 2, py - y1 - 2, px - x1 + 2, py - y1 + 2], outline=(0, 255, 0) if p["valid"] else (255, 0, 0))
    draw.ellipse([x - x1 - 7, y - y1 - 7, x - x1 + 7, y - y1 + 7], outline=(40, 90, 255), width=3)
    ux, uy = w.UPPER_PROBE
    draw.ellipse([ux - x1 - 7, uy - y1 - 7, ux - x1 + 7, uy - y1 + 7], outline=(255, 255, 255), width=2)
    draw.text((6, 6), "foto · región D común (naranja) · H2 (azul) · cuadrado seguro (verde) · punto viejo (blanco)", fill=(255, 255, 0))
    panels.append(raw)
    for k, cid in enumerate(w.seed_ids(w.REF_BRANCH)):
        m = ref_masks[cid]
        crop = image[y1:y2, x1:x2].astype(np.float32)
        view = np.where(m[y1:y2, x1:x2][..., None], crop, crop * 0.3)
        for hole in a13.holes_with_masks(m):
            view[_edge(hole["mask"][y1:y2, x1:x2])] = (0, 255, 255)
        tile = Image.fromarray(view.astype(np.uint8))
        d = ImageDraw.Draw(tile)
        d.ellipse([x - x1 - 7, y - y1 - 7, x - x1 + 7, y - y1 + 7], outline=(40, 90, 255), width=3)
        d.text((6, 6), f"referencia v1.3 s{k} · agujeros >= 1000 px en cian", fill=(255, 255, 0))
        panels.append(tile)
    sheet = Image.new("RGB", (sum(p.width for p in panels) + 8 * (len(panels) - 1), panels[0].height), (20, 20, 20))
    offset = 0
    for p in panels:
        sheet.paste(p, (offset, 0))
        offset += p.width + 8
    sheet.save(OUT_LOCAL / "lamina_diseno_v1_4.png")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--image", help="ruta explícita de la foto")
    parser.add_argument("--check", action="store_true", help="no escribe: compara con el JSON versionado")
    args = parser.parse_args(argv)
    image = load_rgb(locate_image(args.image))
    gray = v13.gray_of(image)
    dark = v13.dark_map(gray)
    payload, ref_masks, region, _ = build(image, gray, dark)
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        same = OUT_JSON.read_text(encoding="utf-8") == text
        print("prerregistro v1.4 reproducido byte a byte:", same)
        raise SystemExit(0 if same else 1)
    OUT_JSON.write_text(text, encoding="utf-8")
    design_sheets(image, payload, ref_masks, region)
    h2 = payload["new_prompts"]["H2"]
    print("H2", h2["xy"], "· cuadrado seguro", 2 * h2["safe_square_half_px"] + 1, "px · margen", h2["contact_box_margin_linf_px"],
          "· holdout más cercano", h2["nearest_holdout"], "· luma", h2["patch_luma_mean"])
    block = payload["branches"]["PERTURB_POINT"]["targets"]["H2"]
    print(f"perturbaciones de H2: {block['valid_count']}/8 válidas", [p["id"] for p in block["perturbations"] if not p["valid"]])
    print("objetivo por semilla:", {s: t["target_hole"] for s, t in h2["inside_target_hole_of_each_reference_seed"].items()})
    print("máscaras:", payload["candidate_counts"])
    print("content_sha256:", payload["content_sha256"])
    print("escrito:", OUT_JSON.relative_to(ROOT), "· lámina privada en", OUT_LOCAL.relative_to(ROOT))


if __name__ == "__main__":
    main()
