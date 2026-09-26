"""Auditoría de una corrida A-E(−1) v1.4 (protocolo v2 rev. 1), en tres etapas separadas en el tiempo.

1. ``integrity``     (paso 2): bytes, hashes, prerregistro, plan de llamadas y congelado; sin resultados.
2. ``blind_package`` (paso 3): seis láminas ``N01…N06`` (las 3 semillas con H2 y las 3 de referencia,
   mezcladas), mapeo sellado en local y paquete para ChatGPT.
3. ``analyze``       (paso 7): consenso y adjudicación, reproducción de la referencia, cierre del
   agujero objetivo, agujeros nuevos, O, H-C3, H-G5, perturbación de H2 y descriptivos.

Reutiliza sin modificarlos los módulos congelados de v1.3 (láminas, sentinelas, reconciliación).
Escrito y probado antes de la corrida con un ZIP simulado; su SHA-256 queda en el prerregistro.
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
from . import aem1_v13 as v13
from . import aem1_v13_audit as a13
from . import aem1_v14 as w

CONFIG = "aem1v14_config.json"
CALLS = "aem1v14_calls.json"
MANIFEST = "aem1v14_manifest.json"
REPORT = "aem1v14_report.json"
NPZ = "aem1v14_perturbaciones.npz"
PNG_BRANCHES = ("BASE", w.REF_BRANCH, w.H2_BRANCH)
CRITERIA = a13.CRITERIA
AUX = a13.AUX
LABEL_PREFIX = "N"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_png_candidate(candidate_id: str) -> bool:
    return candidate_id.split("|", 1)[0] in PNG_BRANCHES


def load_masks(blobs: dict, candidate_ids) -> dict:
    from PIL import Image

    wanted = list(candidate_ids)
    out = {}
    npz = np.load(io.BytesIO(blobs[NPZ])) if any(not is_png_candidate(c) for c in wanted) else None
    for cid in wanted:
        if is_png_candidate(cid):
            with Image.open(io.BytesIO(blobs[f"masks/{a13.safe_name(cid)}.png"])) as handle:
                out[cid] = np.asarray(handle.convert("L")) > 127
        else:
            shape = tuple(int(x) for x in npz["__shape__"])
            bits = np.unpackbits(npz[a13.safe_name(cid)])[: shape[0] * shape[1]]
            out[cid] = bits.reshape(shape).astype(bool)
    return out


# ─── 1. integridad (sin resultados) ───────────────────────────────────────────────────────────

def integrity(zip_path, prereg: dict) -> dict:
    """Paso 2: ¿es este el ZIP del prerregistro v1.4, íntegro y producido en GPU real?"""
    zip_path = Path(zip_path)
    raw = zip_path.read_bytes()
    problems = []
    blobs = a13._read(zip_path)
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
    expected = a13.candidates_of(plan)
    if sorted(manifest.get("masks", {})) != sorted(expected):
        problems.append("el manifiesto no lista exactamente las candidatas del plan")
    else:
        try:
            masks = load_masks(blobs, expected)
        except (KeyError, ValueError, OSError) as exc:
            problems.append(f"máscara ausente o ilegible: {exc}")
        else:
            bad = [cid for cid in expected if masks[cid].shape != (2248, 4000)
                   or a13.packed_sha256(masks[cid]) != manifest["masks"][cid]]
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
                 or int(env.get("checkpoint_bytes", 0)) < a13.GPU_CHECKPOINT_MIN_BYTES)
    run_kind = "SIMULATED" if simulated else ("REAL_CPU" if env.get("device") != "cuda" else "REAL_GPU")
    if run_kind != "SIMULATED":
        if env.get("sam2_commit") != freeze["SAM2_GIT_COMMIT"]:
            problems.append("commit de SAM 2 distinto del congelado")
        if env.get("checkpoint_sha256") != freeze["CHECKPOINT_SHA256"] or env.get("checkpoint_bytes") != freeze["CHECKPOINT_BYTES"]:
            problems.append("checkpoint distinto del congelado")
    if problems:
        status = "INVALID_BUNDLE"
    else:
        status = {"SIMULATED": "SIMULATED_RUN_NOT_EVIDENCE", "REAL_CPU": "REAL_CPU_NOT_COMPARABLE"}.get(run_kind, "INTEGRITY_PASS")
    return {"status": status, "run_kind": run_kind, "problems": problems, "zip_sha256": sha(raw),
            "zip_bytes": len(raw), "run_id": config.get("run_id"), "prereg_content_sha256": config.get("prereg_content_sha256"),
            "environment": {k: env.get(k) for k in ("device", "device_name", "dtype", "torch", "python", "sam2_commit",
                                                    "checkpoint_sha256", "checkpoint_bytes", "image_sha256")},
            "calls": len(calls), "candidates": len(expected),
            "note": "sin datos de resultado: ni áreas, ni scores, ni sentinelas (protocolo v2 §2, paso 2)"}


# ─── 2. paquete ciego ─────────────────────────────────────────────────────────────────────────

def reproduction(masks: dict, prereg: dict) -> dict:
    """¿Reproduce v1.4 bit a bit las semillas BASE|box y la referencia de v1.3?"""
    expected = prereg["reference"]["v1_3_packed_mask_sha256"]
    exact = sorted(cid for cid, digest in expected.items() if a13.packed_sha256(masks[cid]) == digest)
    differs = sorted(set(expected) - set(exact))
    return {"label": "BIT_EXACT" if not differs else "NOT_BIT_EXACT", "bit_exact": exact, "not_bit_exact": differs}


def blind_ids() -> list:
    return w.seed_ids(w.REF_BRANCH) + w.seed_ids(w.H2_BRANCH)


LEEME_V14 = """# Paquete ciego · A‑E(−1) v1.4 · corrida {run_id}

Para: ChatGPT (segunda llave). De: Claude. **Privado:** son recortes de una foto de personas reales.

Protocolo: `auditoria/PROTOCOLO_AUDITORIA_AEM1_v2.md` (rev. 1), SHA‑256 `{protocol_sha256}`.
Mapeo sellado: SHA‑256 `{mapping_sha256}`. **Ninguna carta acompaña a este paquete** y no se ha
revelado ningún resultado. Hay {n} láminas, de `{first}` a `{last}`. Algunas pueden repetir máscaras
que ya juzgaste en una corrida anterior: júzgalas de nuevo, sin consultar juicios previos.

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


def blind_package(zip_path, photo, out_dir, prereg, protocol_path, rng=None) -> dict:
    """Paso 3. Escribe en ``out_dir`` (local): láminas, mapeo sellado, plantilla y el ZIP del paquete."""
    from PIL import Image

    rng = rng or secrets.SystemRandom()
    out_dir = Path(out_dir)
    sheets_dir = out_dir / "laminas"
    sheets_dir.mkdir(parents=True, exist_ok=True)
    blobs = a13._read(zip_path)
    order = blind_ids()
    rng.shuffle(order)
    labels = [f"{LABEL_PREFIX}{i:02d}" for i in range(1, len(order) + 1)]
    masks = load_masks(blobs, order)
    mapping, holes = {}, {}
    for label, cid in zip(labels, order):
        holes[label] = a13.blind_sheet(photo, masks[cid], label, sheets_dir / f"candidata_{label}.png")
        mapping[label] = {"candidate_id": cid, "packed_mask_sha256": a13.packed_sha256(masks[cid])}
    mapping_bytes = json.dumps({"mapping": mapping, "holes": holes}, indent=2, sort_keys=True).encode()
    (out_dir / "sealed_mapping.json").write_bytes(mapping_bytes)
    template = {"schema": "pragma.aem1v14_blind_judgments", "schema_version": "0.1.0",
                "package_sha256": "<SHA-256 del ZIP que juzgaste>", "auditor": "<quién>",
                "candidates": {label: {"criteria": {c: "TRUE|FALSE|UNSURE" for c in CRITERIA},
                                       "aux": {x: "TRUE|FALSE|UNSURE" for x in AUX},
                                       "holes": {str(h["number"]): "D|L" for h in holes[label]},
                                       "notes": ""} for label in labels}}
    template_bytes = (json.dumps(template, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    protocol_sha = sha(Path(protocol_path).read_bytes())
    run_id = json.loads(blobs[CONFIG])["run_id"]
    leeme = LEEME_V14.format(run_id=run_id, protocol_sha256=protocol_sha, mapping_sha256=sha(mapping_bytes),
                             n=len(labels), first=labels[0], last=labels[-1]).encode("utf-8")
    package = out_dir / f"PRAGMA_AEM1v14_paquete_ciego_{run_id}.zip"
    sheet_hashes = {}
    with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in (("LEEME.md", leeme), ("plantilla_juicios.json", template_bytes)):
            archive.writestr(zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0)), data)
        for label in labels:
            buffer = io.BytesIO()
            Image.open(sheets_dir / f"candidata_{label}.png").convert("RGB").save(buffer, "JPEG", quality=92)
            data = buffer.getvalue()
            sheet_hashes[f"candidata_{label}.jpg"] = sha(data)
            archive.writestr(zipfile.ZipInfo(f"candidata_{label}.jpg", date_time=(2026, 1, 1, 0, 0, 0)), data)
    summary = {"package": package.name, "package_sha256": sha(package.read_bytes()),
               "sealed_mapping_sha256": sha(mapping_bytes), "protocol_sha256": protocol_sha,
               "sheets_sha256": sheet_hashes, "labels": labels, "n": len(labels)}
    (out_dir / "blind_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


# ─── 3. análisis (después de las dos llaves) ──────────────────────────────────────────────────

def _hole_consensus(first: dict, second: dict) -> dict:
    out = {}
    for number in sorted(set(first) | set(second), key=int):
        a, b = first.get(number), second.get(number)
        out[number] = a if a == b else "DISAGREE"
    return out


def analyze(zip_path, prereg, mapping, first_raw, second_raw, dark, adjudications=None) -> dict:
    """Paso 7. ``first_raw``/``second_raw``: juicios ciegos por etiqueta (N01…) de cada llave.

    ``adjudications``: {(candidata, campo): {"value": …, "kind": …}} para lo que la medición
    prerregistrada no resuelve (§5.2). Campo ``hole:<n>`` para un agujero D/L en disputa.
    """
    adjudications = dict(adjudications or {})
    blobs = a13._read(zip_path)
    plan = prereg["call_plan"]
    base_config = prereg["base_config"]
    h2 = tuple(prereg["new_prompts"]["H2"]["xy"])
    all_ids = a13.candidates_of(plan)
    masks = load_masks(blobs, all_ids)
    o_points = [(s["id"], s["xy"]) for s in base_config["holdouts"]["drop_other_person"]]
    screens = {cid: a13.sentinel_screen(masks[cid], base_config) for cid in all_ids}
    ref_ids, h2_ids = w.seed_ids(w.REF_BRANCH), w.seed_ids(w.H2_BRANCH)
    repro = reproduction(masks, prereg)
    relevant = set(h2_ids) | {cid for cid in ref_ids if cid in repro["not_bit_exact"]}

    # Llaves por candidata, reconciliadas con sentinelas y agujeros D (protocolo v2 §4).
    label_to_cid = {label: row["candidate_id"] for label, row in mapping["mapping"].items()}
    cid_to_label = {cid: label for label, cid in label_to_cid.items()}
    raw = {"claude": {label_to_cid[k]: val for k, val in first_raw["candidates"].items()},
           "chatgpt": {label_to_cid[k]: val for k, val in second_raw["candidates"].items()}}
    flat = {key: {cid: a13.reconcile(a13._flat(j), screens[cid], j.get("holes", {}))[0] for cid, j in rows.items()}
            for key, rows in raw.items()}
    holes = {cid: _hole_consensus(raw["claude"][cid].get("holes", {}), raw["chatgpt"][cid].get("holes", {}))
             for cid in raw["claude"]}

    # Adjudicación prerregistrada: O por medición; auxiliares sin consenso no se adjudican.
    measured = {cid: w.measure_o(masks[cid], dark) for cid in ref_ids + h2_ids}
    auto = {}
    for cid in raw["claude"]:
        for field in CRITERIA + AUX:
            a, b = flat["claude"][cid].get(field), flat["chatgpt"][cid].get(field)
            if a == b or (cid, field) in adjudications:
                continue
            if field == "other_person_excluded":
                auto[(cid, field)] = {"value": measured[cid]["o_by_measurement"], "kind": "medicion_prerregistrada",
                                      "evidence": measured[cid]}
            elif field in AUX:
                auto[(cid, field)] = {"value": "NO_CONSENSO", "kind": "regla_prerregistrada"}
    adjudications_all = {**auto, **adjudications}
    agreed, pending_all = a13.consensus(flat["claude"], flat["chatgpt"], adjudications_all)
    pending = [(c, f) for c, f in pending_all if c in relevant]
    for cid, table in holes.items():
        for number, value in table.items():
            key = (cid, f"hole:{number}")
            if value == "DISAGREE" and key in adjudications_all:
                table[number] = adjudications_all[key]["value"]

    # Referencia por semilla: v1.3 congelada si es bit a bit; si no, el consenso de esta corrida.
    ref_frozen = prereg["reference"]["judgments"]
    per_seed, descriptive = {}, {}
    for k, (ref_cid, new_cid) in enumerate(zip(ref_ids, h2_ids)):
        ref_mask, new_mask = masks[ref_cid], masks[new_cid]
        if ref_cid in repro["bit_exact"]:
            ref_o = ref_frozen[f"s{k}"]["other_person_excluded"]
            ref_d = set(ref_frozen[f"s{k}"]["d_holes"])
            ref_source = "v1.3 (doble llave y adjudicación aceptadas)"
        else:
            ref_o = agreed[ref_cid]["other_person_excluded"]
            ref_d = {n for n, val in holes[ref_cid].items() if val == "D"}
            ref_source = "v1.4 (la referencia no fue bit a bit)"
        target = w.hole_containing(ref_mask, h2)
        evaluable = target is not None and str(target["number"]) in ref_d
        region = w.h2_region(ref_mask.shape, target["mask"] if target else None, h2)
        close = w.closure(target["mask"], new_mask) if evaluable else None
        new_holes = w.candidate_new_holes(new_mask, ref_mask, region)
        new_status = [holes[new_cid].get(str(h["number"])) for h in new_holes]
        for h, status in zip(new_holes, new_status):
            if status == "DISAGREE":
                pending.append((new_cid, f"hole:{h['number']}"))
        o_new = agreed[new_cid]["other_person_excluded"]
        worse = w.o_worse(ref_o, o_new, measured[ref_cid]["core_px"], measured[new_cid]["core_px"]) \
            if o_new in ("TRUE", "FALSE") else None
        per_seed[f"s{k}"] = {
            "reference": ref_cid, "reference_source": ref_source, "candidate": new_cid,
            "label": cid_to_label.get(new_cid), "reference_label_v14": cid_to_label.get(ref_cid),
            "evaluable": evaluable,
            "target_hole": None if target is None else {"number": target["number"], "area": target["area"],
                                                         "bbox": list(target["bbox"]), "consensus_d": evaluable},
            "closure": close, "closed": bool(close and close["closed"]),
            "new_holes_candidates": [{**h, "consensus": s} for h, s in zip(new_holes, new_status)],
            "new_d": any(s == "D" for s in new_status),
            "o_reference": ref_o, "o_new": o_new,
            "core_px_reference": measured[ref_cid]["core_px"], "core_px_new": measured[new_cid]["core_px"],
            "o_worse": bool(worse),
        }
        upper = w.hole_containing(ref_mask, w.UPPER_PROBE)
        descriptive[f"s{k}"] = {
            "global_change": w.global_change(ref_mask, new_mask, region),
            "upper_strip": None if upper is None else {"reference_hole": {"number": upper["number"], "area": upper["area"]},
                                                        **w.closure(upper["mask"], new_mask)},
        }

    # Perturbación de H2 (informa): estabilidad y cierre bajo cada perturbación válida.
    stability = {}
    for k, new_cid in enumerate(h2_ids):
        rows = [(call["perturbation"], masks[call["candidates"][0]]) for call in plan
                if call["branch"] == "PERTURB_POINT" and call["call_id"].endswith(f"|s{k}")]
        result = v13.perturbation_stability(masks[new_cid], rows, o_points)
        target = per_seed[f"s{k}"]["target_hole"]
        if per_seed[f"s{k}"]["evaluable"]:
            t_mask = w.hole_containing(masks[ref_ids[k]], h2)["mask"]
            result["closed_under_perturbation"] = {pid: w.closure(t_mask, m)["closed"] for pid, m in rows}
        stability[new_cid] = result
    family = v13.worst(r["label"] for r in stability.values())

    hypotheses = {}
    if pending:
        hypotheses = {"H-C3": "PENDING_ADJUDICATION", "H-G5": "PENDING_ADJUDICATION"}
    else:
        hypotheses = {"H-C3": w.hypothesis_h_c3(per_seed), "H-G5": w.hypothesis_h_g5(per_seed)}

    passing = sorted(cid for cid in h2_ids if all(agreed[cid][c] == "TRUE" for c in CRITERIA))

    def non_true(cid):
        return sum(flat[key][cid][c] != "TRUE" for key in flat for c in CRITERIA)
    ranking = sorted(h2_ids, key=lambda c: (non_true(c), len(screens[c]["missed_keep"]), cid_to_label.get(c, c)))

    # Retest (descriptivo): cada llave frente a su propio juicio v1.3 de la misma máscara.
    retest = {}
    for k, ref_cid in enumerate(ref_ids):
        if ref_cid not in repro["bit_exact"]:
            continue
        before = ref_frozen[f"s{k}"]["keys_v1_3"]
        retest[f"s{k}"] = {key: {c: {"v1_3": before[key][c], "v1_4": flat[key][ref_cid][c],
                                     "same": before[key][c] == flat[key][ref_cid][c]} for c in CRITERIA}
                           for key in ("claude", "chatgpt")}

    if pending:
        case = "PENDING_TECHNICAL_ADJUDICATION"
    elif passing:
        case = "PASS_FULL_SUBJECT_UNDER_FIXED_AEM1_PROTOCOL"
    else:
        case = "INCONCLUSIVE_SELECTED_OUTPUT_FAILED"
    closure_rule = {"PASS_FULL_SUBJECT_UNDER_FIXED_AEM1_PROTOCOL": "AEM1_CLOSED_DEMONSTRATED",
                    "INCONCLUSIVE_SELECTED_OUTPUT_FAILED": "AEM1_CLOSED_INCONCLUSIVE"}.get(case, "OPEN_PENDING_ADJUDICATION")
    return {
        "schema": "pragma.aem1v14_analysis", "schema_version": "0.1.0",
        "case_status": case, "aem1_closure": closure_rule, "passing": passing,
        "best_attempt": ranking[0], "pending_adjudication": [f"{c}.{f}" for c, f in pending],
        "adjudications": {f"{c}.{f}": val for (c, f), val in adjudications_all.items()},
        "reproduction": repro, "consensus": agreed, "holes_consensus": holes, "keys_reconciled": flat,
        "sentinels": screens, "per_seed": per_seed, "hypotheses": hypotheses,
        "perturbation": {"per_seed": stability, "family_summary": family},
        "descriptive_preregistered": {"per_seed": descriptive, "retest_same_mask": retest},
        "sam2_rejectable": False, "project_status": "INCONCLUSIVE_A_E0_REQUIRED",
    }
