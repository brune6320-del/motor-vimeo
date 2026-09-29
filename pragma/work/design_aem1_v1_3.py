"""Diseño cerrado de A-E(−1) v1.3 → prerregistro determinista (sin SAM 2 y sin GPU).

Uso:
    python3 work/design_aem1_v1_3.py            # necesita la foto (se localiza por SHA-256)
    python3 work/design_aem1_v1_3.py --check    # recalcula y comprueba que el JSON versionado no cambió

Escribe:
- ``aem1/PRERREGISTRO_A-E-menos-1_v1_3.json`` (versionado: solo coordenadas, reglas y cifras);
- ``local/aem1_v1_3_diseno/`` (privado: lámina de diseño y hoja de contactos de todos los prompts).

Los prompts nuevos no se eligen a mano. La regla es reproducible: el centro del mayor cuadrado de
material oscuro, dentro de una ventana declarada, que cumpla todas las distancias de seguridad. Ver
``pragma_ae.aem1_v13.select_safe_point``. La ventana es la afirmación del auditor sobre el
propietario y la segunda llave la verifica en la lámina privada.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pragma_ae import EXPECTED_IMAGE_SHA256, EXPECTED_IMAGE_SIZE  # noqa: E402
from pragma_ae import aem1_v13 as v  # noqa: E402
from pragma_ae.imageio import load_rgb, locate_image  # noqa: E402
from pragma_ae.preflight import sentinel_contact_sheet, specs_from_notebook  # noqa: E402

NOTEBOOK_V12 = ROOT / "outputs" / "PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_2.ipynb"
NOTEBOOK_V12_SHA256 = "06315e0fe15b84b446570903d7a6c5c219df5ea2ecf4577429cf107cdcdef0da"
RUN1_CONFIG_DIGEST = "fd29b18bbe50cf8236f41057567265e6083d13465511e4882cd8e533af58aa71"
PROTOCOL_V2 = ROOT / "auditoria" / "PROTOCOLO_AUDITORIA_AEM1_v2.md"
BASE_REFERENCE = ROOT / "auditoria" / "aem1_20260925T062504Z_256dba9f" / "BASE_V2_REFERENCE.json"
CROSS_AUDIT = ROOT / "dialogo" / "003_chatgpt_a_claude.md"
ANALYSIS_CODE = ["pragma_ae/aem1_v13.py", "pragma_ae/aem1_v13_audit.py", "pragma_ae/masks.py"]
# Corrección documental de ChatGPT 003: P+1 está materialmente sobre el botón/overol (coordenadas sin cambio).
DESCRIPTION_CORRECTIONS = {"P+1": "botón/overol en el torso de la chica"}
OUT_JSON = ROOT / "aem1" / "PRERREGISTRO_A-E-menos-1_v1_3.json"
OUT_LOCAL = ROOT / "local" / "aem1_v1_3_diseno"

# Afirmación del auditor (Claude), verificable en la lámina privada: dentro de cada ventana, todo
# material oscuro con cuadrado seguro ≥ 21 px pertenece a la chica.
WINDOWS = {
    "H1": {"window": (2940, 400, 3200, 900), "owner": "chica", "material": "pelo oscuro",
           "why": "pelo de la chica a la derecha de su cabeza (lado opuesto al moño), fuera de la caja de contacto"},
    "S1": {"window": (2120, 1350, 2340, 1850), "owner": "chica", "material": "manga oscura",
           "why": "manga oscura del brazo que cuelga, por debajo de la caja de contacto"},
}

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(payload: dict) -> str:
    body = {k: val for k, val in payload.items() if k != "content_sha256"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def run1_packed_hashes() -> dict:
    table = json.loads((ROOT / "auditoria" / "aem1_20260925T062504Z_256dba9f" / "aem1_tabla_desciegada.json").read_text())
    out = {}
    for row in table["candidates"]:
        key = row["key"]
        name = f"{key}#{row['candidate_index']}" if ":" not in key else f"{key}#0"
        out[name] = row["packed_mask_sha256"]
    return dict(sorted(out.items()))


def build(image, gray, dark):
    if sha(NOTEBOOK_V12) != NOTEBOOK_V12_SHA256:
        raise SystemExit("El cuaderno v1.2 no es el esperado")
    specs, box = specs_from_notebook(json.loads(NOTEBOOK_V12.read_text(encoding="utf-8")))
    by_group = {}
    for sid, xy, group, desc in specs:
        entry = {"id": sid, "xy": list(xy), "description": DESCRIPTION_CORRECTIONS.get(sid, desc), **v.patch_stats(gray, xy)}
        if sid in DESCRIPTION_CORRECTIONS:
            entry["description_v1_2"] = desc
        by_group.setdefault(group, []).append(entry)
    holdouts = {s["id"]: s["xy"] for g in ("keep_subject", "drop_other_person", "drop_background") for s in by_group[g]}
    prompts = {s["id"]: s["xy"] for g in ("prompt_positive", "prompt_negative_other_person") for s in by_group[g]}
    size = EXPECTED_IMAGE_SIZE

    new = {}
    for pid, decl in WINDOWS.items():
        others = list(prompts.values()) + [n["xy"] for n in new.values()]
        chosen = v.select_safe_point(dark, decl["window"], list(holdouts.values()), others)
        if chosen is None:
            raise SystemExit(f"{pid}: ninguna posición cumple las restricciones")
        xy = chosen["xy"]
        near_h = min(holdouts, key=lambda k: v.distance(xy, holdouts[k]))
        all_prompts = {**prompts, **{k: n["xy"] for k, n in new.items()}}
        near_p = min(all_prompts, key=lambda k: v.distance(xy, all_prompts[k]))
        half = chosen["safe_half"]
        x, y = xy
        new[pid] = {
            "xy": xy,
            "owner_expected": decl["owner"],
            "material": decl["material"],
            "declared_window_xyxy": list(decl["window"]),
            "window_rationale": decl["why"],
            "selection_rule": "pragma_ae.aem1_v13.select_safe_point (rejilla de 2 px)",
            "safe_square_half_px": half,
            "safe_square_dark_fraction": round(float(dark[y - half:y + half + 1, x - half:x + half + 1].mean()), 4),
            "contact_box_margin_linf_px": chosen["contact_margin_linf"],
            "frontier_distance_lower_bound_px": chosen["contact_margin_linf"],
            "nearest_holdout": {"id": near_h, "distance_px": round(v.distance(xy, holdouts[near_h]), 1)},
            "nearest_prompt": {"id": near_p, "distance_px": round(v.distance(xy, all_prompts[near_p]), 1)},
            **v.patch_stats(gray, xy),
            "image_sha256": EXPECTED_IMAGE_SHA256,
            "owner_verified_by": "auditor IA Claude en la lámina privada de diseño",
            "owner_second_key": "PASS (ChatGPT 003: el punto y sus 8 perturbaciones sobre la chica)",
        }

    def point_block(base_id, base_xy, use_dark):
        rows = []
        for p in v.point_perturbations(base_xy):
            ok, reasons = v.validate_perturbed_point(p["xy"], size, list(holdouts.values()),
                                                     dark=dark if use_dark else None)
            rows.append({**p, "valid": ok, "reasons": reasons, **v.patch_stats(gray, p["xy"])})
        return {"base": base_id, "base_xy": list(base_xy), "perturbations": rows,
                "valid_count": sum(r["valid"] for r in rows)}

    p_plus = prompts["P+1"]
    perturb_point = {
        "P+1": {**point_block("P+1", p_plus, use_dark=False), "branch": "BASE",
                "protocols": ["point", "point+corrections"],
                "chain": "el punto perturbado sustituye a P+1 en la semilla (point, multimask) y en la corrección"},
        "H1": {**point_block("H1", new["H1"]["xy"], use_dark=True), "branch": "+POS_HAIR+SLEEVE",
               "protocols": ["point+corrections", "box+corrections"],
               "chain": "semillas de BASE sin cambios; solo H1 se perturba (S1 fijo)"},
        "S1": {**point_block("S1", new["S1"]["xy"], use_dark=True), "branch": "+POS_HAIR+SLEEVE",
               "protocols": ["point+corrections", "box+corrections"],
               "chain": "semillas de BASE sin cambios; solo S1 se perturba (H1 fijo)"},
    }
    box_rows = v.box_perturbations(box, size)
    perturb_box = {"base_box_xyxy": list(box), "protocols": ["box", "box+corrections"],
                   "chain": "la caja perturbada sustituye a la base en la semilla (box, multimask) y en la corrección",
                   "coordinates": "inclusivas: 0 ≤ x ≤ 3999, 0 ≤ y ≤ 2247 (y2 = 2247 es la última fila)",
                   "perturbations": box_rows, "valid_count": sum(r["valid"] for r in box_rows)}

    positives = ["P+1"]
    negatives = [s["id"] for s in by_group["prompt_negative_other_person"]]
    corrections = lambda extra: {"points": positives + extra + negatives,  # noqa: E731
                                 "labels": [1] * (1 + len(extra)) + [0] * len(negatives)}
    seed_note = "mask_input = low_res_logits[s] de la semilla BASE del mismo tipo; multimask_output=False"
    branches = {
        "BASE": {
            "purpose": "replicar la corrida 1 (los mismos prompts, la misma caja y el mismo congelado)",
            "protocols": {
                "point": {"points": ["P+1"], "labels": [1], "box": None, "multimask_output": True, "outputs": 3},
                "box": {"points": [], "labels": [], "box": "BOX", "multimask_output": True, "outputs": 3},
                "point+corrections:s{0,1,2}": {**corrections([]), "box": None, "seed": "point", "note": seed_note},
                "box+corrections:s{0,1,2}": {**corrections([]), "box": "BOX", "seed": "box", "note": seed_note},
            },
            "reproduction_check": {
                "rule": "packed_mask_sha256 de cada candidata BASE frente a la corrida 1",
                "labels": {"BIT_EXACT": ("máscara idéntica: su referencia es BASE_V2_REFERENCE (adjudicación de la corrida 1 "
                                         "normalizada a las definiciones v2), NO una doble llave v2 heredada; no vuelve al paquete ciego"),
                           "NOT_BIT_EXACT": "las que difieran entran al paquete ciego con etiquetas nuevas"},
                "reference": {"file": BASE_REFERENCE.relative_to(ROOT).as_posix(), "sha256": sha(BASE_REFERENCE),
                              "kind": "REFERENCIA_NORMALIZADA_ADJUDICADA",
                              "why": "ChatGPT 003 (e): BIT_EXACT_MASK ≠ BIT_EXACT_JUDGMENT_UNDER_NEW_PROTOCOL"},
                "run1_packed_mask_sha256": run1_packed_hashes(),
            },
        },
    }
    for name, extra in (("+POS_HAIR", ["H1"]), ("+POS_SLEEVE", ["S1"]), ("+POS_HAIR+SLEEVE", ["H1", "S1"])):
        branches[name] = {
            "purpose": f"efecto causal de añadir {' y '.join(extra)} como positivo(s) a las correcciones",
            "only_change_vs_BASE": f"{' y '.join(extra)} con etiqueta 1 en la llamada de corrección; semillas idénticas a BASE",
            "protocols": {
                "point+corrections:s{0,1,2}": {**corrections(extra), "box": None, "seed": "point (BASE)", "note": seed_note},
                "box+corrections:s{0,1,2}": {**corrections(extra), "box": "BOX", "seed": "box (BASE)", "note": seed_note},
            },
            "why_not_point_or_box_alone": ("los positivos nuevos contrarrestan a los negativos; sin negativos, "
                                           "box ya incluye todo lo oscuro (corrida 1) y point no lleva negativos"),
        }
    branches["RECIPROCAL_POSTERIOR"] = {
        "purpose": "¿puede SAM 2 segmentar de forma estable a la persona posterior cuando se le pide directamente?",
        "mirror_of": "point y point+corrections, con los papeles invertidos",
        "protocols": {
            "R-point": {"points": ["P-1"], "labels": [1], "box": None, "multimask_output": True, "outputs": 3},
            "R-corrections:s{0,1,2}": {"points": ["P-1", "P-2", "P-3", "P+1", "H1", "S1"], "labels": [1, 1, 1, 0, 0, 0],
                                       "box": None, "seed": "R-point",
                                       "note": "mask_input = low_res_logits[s] de R-point; multimask_output=False"},
        },
        "sentinels_swapped": {"keep": "O1–O4", "drop_other_person": "K1–K7", "drop_background": "B1–B3"},
        "reference_mask": "R_ref = la semilla R-corrections con más sentinelas O cubiertos (≥ 0,80); empate → menor índice",
        "never": "no se usa para reparar la máscara de la chica (nada de objetivo − posterior)",
    }
    branches["PERTURB_POINT"] = {"offsets_px": [list(o) for o in v.POINT_OFFSETS],
                                 "neighbourhood": ("anillo L∞ de radio 15 px, determinista: 4 axiales (euclídea 15 px) y "
                                                   "4 diagonales (euclídea 15·√2 ≈ 21,21 px); no son desplazamientos equivalentes"),
                                 "linf_radius_px": v.STEP, "euclidean_px": {"axial": float(v.STEP), "diagonal": round(v.STEP * 2 ** 0.5, 2)},
                                 "one_at_a_time": True, "targets": perturb_point}
    branches["PERTURB_BOX"] = perturb_box

    n_valid_p = sum(t["valid_count"] for t in perturb_point.values())
    counts = {
        "BASE": 12, "+POS": 18, "RECIPROCAL": 6,
        "PERTURB_POINT": perturb_point["P+1"]["valid_count"] * 6 + (perturb_point["H1"]["valid_count"]
                                                                  + perturb_point["S1"]["valid_count"]) * 6,
        "PERTURB_BOX": perturb_box["valid_count"] * 6,
        "valid_point_perturbations": n_valid_p,
    }
    counts["total_masks"] = sum(val for k, val in counts.items() if k not in ("valid_point_perturbations", "calls"))
    base_xy = {q["id"]: q["xy"] for q in by_group["prompt_positive"] + by_group["prompt_negative_other_person"]}
    call_plan = v.build_call_plan(base_xy, {k: n["xy"] for k, n in new.items()}, list(box),
                                  {k: t["perturbations"] for k, t in perturb_point.items()}, box_rows)
    if sum(len(c["candidates"]) for c in call_plan) != counts["total_masks"]:
        raise SystemExit("el plan de llamadas no produce el número de máscaras declarado")
    counts["calls"] = len(call_plan)

    payload = {
        "schema": "pragma.aem1_preregistration",
        "schema_version": "0.1.0",
        "experiment": "A-E(−1) v1.3 · caso chica",
        "status": "PREREGISTERED",
        "frozen_on": "2026-09-25",
        "responds_to": ["dialogo/002_chatgpt_a_claude.md", "dialogo/003_chatgpt_a_claude.md"],
        "cross_audit": {
            "by": "ChatGPT", "letter": CROSS_AUDIT.relative_to(ROOT).as_posix(), "letter_sha256": sha(CROSS_AUDIT),
            "inspected_package_sha256": "0453d7d271f260e5db4faef7b9a769dfd63386d6afdabca45d290aeb0737e8ff",
            "inspected_prereg_content_sha256": "20d1f9f534ab941e0a278d6c218149c910c4abedfedb0fe25e17d3ba02c2bf1d",
            "verdicts": {"ZIP_INTEGRITY": "PASS", "DESIGN_PROMPTS_SECOND_KEY": "PASS", "H1/S1/P+1_PERTURBATIONS": "PASS",
                         "DECISION_A": "ACCEPT", "DECISION_B": "ACCEPT_WITH_NAMING_CLARIFICATION",
                         "DECISION_C": "ACCEPT_WITH_CONTINUOUS_DIAGNOSTICS", "DECISION_D": "ACCEPT_AS_DIAGNOSTIC",
                         "DECISION_E": "CHANGE_REQUIRED", "BLIND_PROTOCOL_V2": "ACCEPT_AFTER_TECHNICAL_ADJUDICATION_CHANGE"},
            "changes_applied_before_any_run": [
                "(e) BASE bit a bit → BASE_V2_REFERENCE (referencia normalizada y adjudicada), no doble llave heredada",
                "protocolo v2 rev. 1 §5.2: discrepancia → adjudicación técnica; la persona usuaria conserva el veto",
                "(b) perturbaciones con radio L∞ y distancia euclídea explícitos",
                "(c) cobertura continua de O* y distancia al umbral en cada CONFLICT",
                "(d) razones de propiedad |T∩R|/|T| y |T∩R|/|R| además de la de min()",
                "descripción de P+1: botón/overol en el torso de la chica (sin cambiar coordenadas)",
                "hipótesis H-G1…H-G4 de ChatGPT registradas",
            ],
            "result": "AEM1_v1.3 = GO_TO_BUILD tras aplicar los cambios (ChatGPT 003)",
        },
        "generated_by": "work/design_aem1_v1_3.py",
        "image": {"sha256": EXPECTED_IMAGE_SHA256, "size": list(size), "orientation": "EXIF aplicado; sin redimensionar"},
        "sam2_freeze": {
            "SAM2_GIT_COMMIT": "2b90b9f5ceec907a1c18123530e92e794ad901a4",
            "MODEL_CONFIG": "configs/sam2.1/sam2.1_hiera_l.yaml",
            "CHECKPOINT": "sam2.1_hiera_large.pt",
            "CHECKPOINT_SHA256": "2647878d5dfa5098f2f8649825738a9345572bae2d4350a2468587ece47dd318",
            "CHECKPOINT_BYTES": 898083611,
            "dtype": "bfloat16 (autocast CUDA), como la corrida 1",
            "gate": "el cuaderno bloquea antes de generar si el commit, el checkpoint o la foto difieren",
        },
        "base_config": {
            "source_notebook": NOTEBOOK_V12.relative_to(ROOT).as_posix(),
            "source_notebook_sha256": NOTEBOOK_V12_SHA256,
            "run1_config_digest": RUN1_CONFIG_DIGEST,
            "BOX": list(box),
            "prompts": by_group["prompt_positive"] + by_group["prompt_negative_other_person"],
            "holdouts": {"keep_subject": by_group["keep_subject"], "drop_other_person": by_group["drop_other_person"],
                         "drop_background": by_group["drop_background"]},
            "patch_radius": v.PATCH_RADIUS, "keep_min_coverage": v.SENTINEL_KEEP_MIN, "drop_max_coverage": v.SENTINEL_DROP_MAX,
        },
        "new_prompts": new,
        "safety_constants": {
            "contact_box_xyxy": list(v.CONTACT_BOX),
            "contact_box_claim": "toda la frontera visible chica↔persona posterior está dentro de esta caja; su margen es cota inferior de la distancia a la frontera",
            "contact_margin_min_linf_px": v.CONTACT_MARGIN_MIN,
            "perturbed_contact_margin_min_linf_px": v.PERTURBED_CONTACT_MARGIN_MIN,
            "holdout_distance_min_px": v.HOLDOUT_DIST_MIN,
            "perturbed_holdout_distance_min_px": v.PERTURBED_HOLDOUT_DIST_MIN,
            "prompt_distance_min_px": v.PROMPT_DIST_MIN,
            "dark_luma_threshold": v.DARK_LUMA, "dark_blur_radius": v.BLUR_RADIUS,
            "safe_square_dark_fraction_min": v.DARK_FRACTION_MIN, "safe_square_half_min_px": v.SAFE_HALF_MIN,
            "perturbed_patch_dark_fraction_min": v.PERTURBED_DARK_FRACTION_MIN,
            "luma": "media de los canales RGB en el parche 13×13, como el preflight v1.2",
            "runtime_binding": "el cuaderno recalcula la luma de TODO prompt (base y perturbado) y bloquea si difiere > 3,0 del valor registrado aquí",
        },
        "invalid_perturbation": "un caso INVALID_PERTURBATION no se ejecuta y nunca cuenta como evidencia contra SAM 2",
        "branches": branches,
        "combination": "NINGUNA en v1.3 (ChatGPT 002: solo si se prerregistra; no se prerregistra)",
        "candidate_counts": counts,
        "call_plan": call_plan,
        "call_plan_semantics": ("cada llamada es SAM2ImagePredictor.predict(point_coords=points o None, point_labels=labels o None, "
                                "box=box o None, mask_input=low_res_logits[index][None] de mask_input_from o None, "
                                "multimask_output, return_logits=True); máscara = logits > 0; mismas conversiones que v1.2 "
                                "(float32 para puntos y caja, int32 para etiquetas)"),
        "analysis_implementation_sha256": {path: sha(ROOT / path) for path in ANALYSIS_CODE},
        "consensus": ("valor de consenso de una celda = el de las dos llaves si coinciden; si no, el de la adjudicación técnica "
                      "(protocolo v2 rev. 1 §5.2); mientras falte, la candidata no pasa"),
        "blind_audit": {
            "protocol": PROTOCOL_V2.relative_to(ROOT).as_posix(),
            "protocol_sha256": sha(PROTOCOL_V2),
            "candidates": "las 18 de +POS_HAIR, +POS_SLEEVE y +POS_HAIR+SLEEVE, más las de BASE que no se reproduzcan bit a bit",
            "not_blind_judged": ["RECIPROCAL_POSTERIOR", "PERTURB_POINT", "PERTURB_BOX"],
            "order": "el paquete va a ChatGPT antes que cualquier resultado; los juicios de Claude se comprometen por hash",
        },
        "metrics": {
            "perturbation_stability": {
                "function": "pragma_ae.aem1_v13.perturbation_stability",
                "unit": "cada candidata (protocolo, índice) frente a la misma candidata con cada perturbación válida",
                "labels": {
                    "NOT_EVALUABLE": "ninguna perturbación válida",
                    "CONFLICT": "el cribado O* (algún sentinela de la persona posterior filtrado o ninguno) cambia entre base y alguna perturbación",
                    "UNSTABLE": "IoU global mínimo < 0,90",
                    "STABLE": "en otro caso",
                },
                "family_summary": "la peor etiqueta evaluable (CONFLICT > UNSTABLE > STABLE)",
                "secondary": "IoU mínimo dentro de CONTACT_BOX (None si las dos están vacías en la caja)",
                "continuous": "cobertura de cada O* (base y cada perturbación) y, en cada cruce, su distancia al umbral 0,20 (ChatGPT 003 c)",
                "base_of_each_family": {"P+1": "BASE (point y point+corrections)", "H1 y S1": "+POS_HAIR+SLEEVE",
                                        "caja": "BASE (box y box+corrections)"},
            },
            "reciprocal_stability": {
                "function": "pragma_ae.aem1_v13.reciprocal_stability",
                "unit": "las 3 semillas R-corrections, IoU por pares dentro de CONTACT_BOX",
                "labels": {"NOT_EVALUABLE": "alguna vacía en la caja",
                           "CONFLICT": "el cribado K* (la chica filtrada dentro de R) cambia entre semillas",
                           "UNSTABLE": "IoU mínimo < 0,90", "STABLE": "en otro caso"},
            },
            "ownership": {
                "function": "pragma_ae.aem1_v13.ownership",
                "unit": "cada candidata de la chica (BASE y +POS) frente a R_ref, dentro de CONTACT_BOX",
                "ratio": "|T∩R| / min(|T|, |R|) en la caja; se reportan siempre también |T∩R|/|T| y |T∩R|/|R|",
                "role": "diagnóstico, nunca criterio de aceptación (ChatGPT 003 d)",
                "labels": {"NOT_EVALUABLE": "T o R vacía en la caja", "DISJOINT": "≤ 0,02",
                           "MARGINAL": "entre 0,02 y 0,10", "SHARED": "≥ 0,10"},
                "also_reported": ["T filtra O2 u O3 (> 0,20)", "R_ref cubre O2 y O3 (≥ 0,80)"],
            },
            "interpretation": {
                "function": "pragma_ae.aem1_v13.interpret_reciprocal",
                "table": {
                    "NO_INFERENCE": "R no es STABLE o la propiedad no es evaluable",
                    "OWNERSHIP_AMBIGUOUS": "T arrastra el moño y T, R lo reclaman a la vez (SHARED)",
                    "BUN_ATTRIBUTED_TO_TARGET_BY_BOTH": "T arrastra el moño, T y R son DISJOINT y R no cubre el moño",
                    "SEPARATION_CONSISTENT_BOTH_WAYS": "T no arrastra el moño y T, R son DISJOINT",
                    "MIXED": "cualquier otro caso",
                },
                "scope": "diagnóstico del prompting; nunca rechaza SAM 2",
            },
        },
        "hypotheses": [
            {"id": "H-C1", "by": "Claude (carta 002)", "function": "pragma_ae.aem1_v13.hypothesis_h_c1",
             "statement": "+POS_HAIR recupera el pelo de la chica pero vuelve a arrastrar el moño",
             "unit": "las 6 candidatas de +POS_HAIR",
             "holds_if": "≥ 4 con target_hair_included TRUE en ambas llaves y (other_person_excluded FALSE en ambas llaves u O2/O3 filtrado)",
             "refuted_if": "≥ 4 con target_hair_included TRUE en ambas llaves, other_person_excluded TRUE en ambas y sin O2/O3 filtrado",
             "otherwise": "INDETERMINATE",
             "inference_limit": "aunque se cumpla, solo muestra que esta familia de prompts no resuelve la ambigüedad (ChatGPT 002)"},
            {"id": "H-C2", "by": "Claude (carta 003)", "function": "pragma_ae.aem1_v13.hypothesis_h_c2",
             "statement": "PERTURB_POINT sobre P+1 no es STABLE en el protocolo point",
             "reason": "P+1 (2588, 1785) está en la fila superior de la caja del botón que devolvió point#0 en la corrida 1 (2555–2604 × 1785–1824)",
             "holds_if": "alguna de las 3 salidas de point es UNSTABLE o CONFLICT",
             "refuted_if": "las 3 salidas de point son STABLE"},
            {"id": "H-G1", "by": "ChatGPT (carta 003)", "function": "pragma_ae.aem1_v13.hypothesis_h_g1",
             "statement": "S1 tendrá un efecto predominantemente local sobre la recuperación de mangas y no sobre la propiedad del moño",
             "unit": "las 6 candidatas de +POS_SLEEVE, cada una frente a su BASE emparejada (mismo protocolo y semilla)",
             "holds_if": "≥ 4/6 con target_dark_sleeves_included TRUE en ambas llaves y ≤ 2/6 empeoran other_person_excluded frente a su BASE",
             "refuted_if": "≥ 4 no recuperan mangas (no TRUE en ambas llaves) o ≥ 4 introducen una fuga nueva de la persona posterior",
             "otherwise": "INDETERMINATE",
             "operationalization_by_claude": ("«empeora» = BASE emparejada con other_person_excluded TRUE (referencia si es bit a bit; "
                                              "si no, su consenso ciego) y +POS_SLEEVE con consenso FALSE")},
            {"id": "H-G2", "by": "ChatGPT (carta 003)", "function": "pragma_ae.aem1_v13.hypothesis_h_g2",
             "statement": "las correcciones recíprocas no cambiarán de propietario grueso entre semillas",
             "holds_if": "reciprocal_stability ∈ {STABLE, UNSTABLE}", "refuted_if": "reciprocal_stability = CONFLICT",
             "otherwise": "NOT_EVALUABLE no confirma ni refuta (INDETERMINATE)",
             "reason": "tres anclas positivas sobre la posterior y negativos explícitos sobre la chica deberían estabilizar qué persona se elige antes que su frontera"},
            {"id": "H-G3", "by": "ChatGPT (carta 003)", "function": "pragma_ae.aem1_v13.hypothesis_h_g3",
             "statement": "al menos una T que arrastre O2/O3 será SHARED con R_ref mientras R también cubre O2/O3",
             "unit": "candidatas de la chica de BASE y +POS",
             "holds_if": "existe T con fuga O2/O3, R_ref cubre O2/O3 y la propiedad es SHARED",
             "refuted_if": "R_ref cubre O2/O3 y todas las T con fuga O2/O3 son DISJOINT (y hay al menos una)",
             "otherwise": "INDETERMINATE (también si R no es evaluable)",
             "operationalization_by_claude": "«fuga O2/O3» = cobertura de O2 u O3 > 0,20; «R cubre O2/O3» = O2 y O3 ≥ 0,80 en R_ref"},
            {"id": "H-G4", "by": "ChatGPT (carta 003)", "function": "pragma_ae.aem1_v13.hypothesis_h_g4",
             "statement": "+POS_HAIR+SLEEVE conseguirá al menos una candidata que recupere a la vez pelo y mangas",
             "holds_if": "≥ 1/6 con target_hair_included y target_dark_sleeves_included TRUE en ambas llaves", "refuted_if": "0/6",
             "note": "no predice que eso baste para un PASS de separación"},
        ],
        "decision": {
            "acceptance": "solo por el protocolo de auditoría v2 rev. 1 §5 (doble llave y adjudicación técnica); ninguna métrica de este archivo acepta ni rechaza",
            "user_veto": True,
            "sam2_rejectable": False,
            "project_status": "INCONCLUSIVE_A_E0_REQUIRED",
            "phase_b": "BLOQUEADA",
        },
        "forbidden": [
            "reparar la máscara de la chica con la del prompt recíproco (objetivo − posterior)",
            "elegir semilla, salida o candidata por score",
            "combinar ramas (no hay combinación prerregistrada)",
            "cambiar prompts, caja o umbrales después de ver datos de la corrida",
            "ejecutar un caso INVALID_PERTURBATION",
            "FastAPI, localhost, YOLO-seg o BiRefNet; tocar la extensión",
        ],
        "outputs": {
            "zip": "PRAGMA_AEM1v13_<run_id>_PENDING_EXTERNAL_AUDIT.zip",
            "contents": ["aem1v13_config.json (prerregistro embebido, entorno, compuertas y luma)",
                         "aem1v13_calls.json (las llamadas ejecutadas, en orden)", "aem1v13_manifest.json (bytes y SHA-256)",
                         "aem1v13_report.json", "masks/<candidata>.png para BASE, +POS y RECIPROCAL (36)",
                         "aem1v13_perturbaciones.npz (174 máscaras en packbits, con SHA-256 por máscara en el manifiesto)"],
            "not_shown_in_colab": "el cuaderno no muestra máscaras, áreas, scores ni sentinelas: solo progreso e integridad",
        },
    }
    payload["content_sha256"] = canonical_hash(payload)
    return payload, specs, box


def design_sheets(image, payload, specs, box):
    """Material privado para la segunda llave: todos los prompts de v1.3 y sus perturbaciones."""
    import numpy as np
    from PIL import Image, ImageDraw

    OUT_LOCAL.mkdir(parents=True, exist_ok=True)
    tiles = []
    for pid, info in payload["new_prompts"].items():
        tiles.append((pid, tuple(info["xy"]), "prompt_positive", f"{info['material']} ({info['owner_expected']})"))
    for target, block in payload["branches"]["PERTURB_POINT"]["targets"].items():
        for p in block["perturbations"]:
            tag = "OK" if p["valid"] else "INVALIDA"
            tiles.append((f"{target}{p['id']}", tuple(p["xy"]), "prompt_positive" if p["valid"] else "drop_background",
                          f"perturbacion {tag}"))
    for sid, xy, group, desc in specs:
        if group.startswith("prompt"):
            tiles.append((sid, xy, group, desc))
    stats = sentinel_contact_sheet(image, tiles, OUT_LOCAL / "hoja_contactos_prompts_v1_3.png", columns=9)

    overview_box = (2000, 250, 3600, 2248)
    crop = Image.fromarray(np.ascontiguousarray(image[overview_box[1]:overview_box[3], overview_box[0]:overview_box[2]]))
    draw = ImageDraw.Draw(crop)

    def shift(x, y):
        return x - overview_box[0], y - overview_box[1]

    cb = payload["safety_constants"]["contact_box_xyxy"]
    draw.rectangle([*shift(cb[0], cb[1]), *shift(cb[2] - 1, cb[3] - 1)], outline=(255, 160, 0), width=5)
    draw.rectangle([*shift(box[0], box[1]), *shift(box[2], box[3])], outline=(255, 255, 0), width=3)
    for pid, info in payload["new_prompts"].items():
        w = info["declared_window_xyxy"]
        draw.rectangle([*shift(w[0], w[1]), *shift(w[2] - 1, w[3] - 1)], outline=(0, 200, 255), width=3)
        x, y = info["xy"]
        h = info["safe_square_half_px"]
        draw.rectangle([*shift(x - h, y - h), *shift(x + h, y + h)], outline=(0, 255, 0), width=3)
    colors = {"prompt_positive": (40, 90, 255), "prompt_negative_other_person": (255, 40, 40),
              "keep_subject": (60, 230, 60), "drop_other_person": (255, 0, 255), "drop_background": (0, 220, 255)}
    for sid, (x, y), group, _ in specs:
        cx, cy = shift(x, y)
        draw.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], outline=colors[group], width=4)
        draw.text((cx + 12, cy - 12), sid, fill=colors[group])
    for target, block in payload["branches"]["PERTURB_POINT"]["targets"].items():
        for p in block["perturbations"]:
            cx, cy = shift(*p["xy"])
            draw.point((cx, cy), fill=(0, 255, 0) if p["valid"] else (255, 0, 0))
            draw.rectangle([cx - 2, cy - 2, cx + 2, cy + 2], outline=(0, 255, 0) if p["valid"] else (255, 0, 0))
    for pid, info in payload["new_prompts"].items():
        cx, cy = shift(*info["xy"])
        draw.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], outline=(40, 90, 255), width=5)
        draw.text((cx + 14, cy + 4), pid, fill=(40, 90, 255))
    crop.save(OUT_LOCAL / "lamina_diseno_v1_3.png")
    return stats


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--image", help="ruta explícita de la foto")
    parser.add_argument("--check", action="store_true", help="no escribe: compara con el JSON versionado")
    args = parser.parse_args(argv)
    image = load_rgb(locate_image(args.image))
    gray = v.gray_of(image)
    dark = v.dark_map(gray)
    payload, specs, box = build(image, gray, dark)
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        same = OUT_JSON.read_text(encoding="utf-8") == text
        print("prerregistro reproducido byte a byte:", same)
        raise SystemExit(0 if same else 1)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(text, encoding="utf-8")
    design_sheets(image, payload, specs, box)
    for pid, info in payload["new_prompts"].items():
        print(pid, info["xy"], "cuadrado seguro", 2 * info["safe_square_half_px"] + 1, "px · margen", info["contact_box_margin_linf_px"],
              "· holdout más cercano", info["nearest_holdout"], "· luma", info["patch_luma_mean"])
    for target, block in payload["branches"]["PERTURB_POINT"]["targets"].items():
        print(f"perturbaciones de {target}: {block['valid_count']}/8 válidas",
              [p["id"] for p in block["perturbations"] if not p["valid"]])
    print("caja:", payload["branches"]["PERTURB_BOX"]["valid_count"], "de 6 válidas")
    print("máscaras:", payload["candidate_counts"])
    print("content_sha256:", payload["content_sha256"])
    print("escrito:", OUT_JSON.relative_to(ROOT), "· lámina privada en", OUT_LOCAL.relative_to(ROOT))


if __name__ == "__main__":
    main()
