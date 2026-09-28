"""A‑E1 etapa 1: plan de llamadas, integridad del ZIP y lector prerregistrado R1–R4 (ChatGPT 019).

Nada de este módulo ejecuta SAM 2. Define, antes de la corrida:

- el **plan de llamadas**: las 4 configuraciones AMG del sweep prerregistrado, con sus kwargs exactos;
- la **integridad** del ZIP que produce el cuaderno, sin devolver ningún resultado;
- el **lector** de la etapa 1, que nunca puede dar ``PASS_PROPOSALS`` (techo
  ``INCONCLUSIVE_GT_INCOMPLETE``):
  - **R1 · cribado de cajas.** Se dispara con un Tier A cuya mejor IoU de caja es < 0,5 en las cuatro
    configuraciones. Revisión ciega con las 3 mejores propuestas **por configuración** (≤ 12,
    deduplicadas por hash), sin configuración, score ni ranking. Hay
    ``CONFIRMED_BOX_SCREEN_FAILURE`` solo si las dos llaves dicen ``MISS``.
  - **R2 · personas, cotas a nivel de conjunto.** Para cada propuesta: ``iou_estimate``, ``iou_min`` e
    ``iou_max`` (las de ``keydiff.iou_with_uncertainty``). Los veredictos son:
    - ``PASS`` si max_p ``iou_min`` ≥ 0,70;
    - ``FAIL`` si max_p ``iou_max`` < 0,70;
    - ``DEPENDS_ON_UNCERTAINTY`` en otro caso.
  - **R3 · fusión y contacto** entre personas: diagnóstico ``FUSION_Q_ESTIMATE_BASED`` de
    ``metrics.evaluate``, sin early‑stop.
  - **R4 · decisión de etapa.** ``FAIL_COMPONENT`` si hay ≥ 1 ``CONFIRMED_BOX_SCREEN_FAILURE``, o ≥ 1
    persona con ``FAIL`` en las cuatro configuraciones. Si no, ``INCONCLUSIVE_GT_INCOMPLETE`` y se pasa a
    la etapa 2.

``metrics.py``, las máscaras y los umbrales del contrato congelado no cambian: este lector solo usa sus
funciones.
"""

from __future__ import annotations

import hashlib
import io
import json
import random
import zipfile
from pathlib import Path

import numpy as np

from .keydiff import iou_with_uncertainty  # noqa: F401  (referencia de las cotas; ver tests)
from .masks import as_bool, box_iou, mask_bbox, rle_decode

STAGE_THRESHOLD = 0.70          # GateParams.tier_a_mask_iou del contrato congelado
BOX_THRESHOLD = 0.50            # GateParams.tier_b_box_iou (cribado de cajas del contrato)
TOP_PER_CONFIG = 3
BLIND_SEED = 20260928
PERSONS = ("ae0_001", "ae0_002", "ae0_003")
TAG_IDS = ("ae0_044", "ae0_045")       # etiquetas con nombre: se tapan en toda lámina
TAG_PAD_PX = 10
KEY_ANSWERS = ("COVERS_OBJECT", "MISS", "CANNOT_DETERMINE")
H, W = 2248, 4000

CONFIG_KEYS = ("points_per_side", "pred_iou_thresh", "stability_score_thresh", "crop_n_layers",
               "crop_n_points_downscale_factor")
CONSTANT_KEYS = ("points_per_batch", "stability_score_offset", "mask_threshold", "box_nms_thresh",
                 "crop_nms_thresh", "crop_overlap_ratio", "point_grids", "min_mask_region_area",
                 "output_mode", "use_m2m", "multimask_output")
PPB_FALLBACK = (64, 32, 16)

CONFIG_JSON, CALLS_JSON, REPORT_JSON, MANIFEST_JSON = ("ae1s1_config.json", "ae1s1_calls.json",
                                                       "ae1s1_report.json", "ae1s1_manifest.json")


# ─── plan de llamadas ─────────────────────────────────────────────────────────────────────────

def _number(value):
    """``"512 / 1500"`` del sweep → 512/1500 exacto (el mismo float que el valor por defecto de SAM 2)."""
    if isinstance(value, str) and "/" in value:
        a, b = (float(v) for v in value.split("/"))
        return a / b
    return value


def call_plan(sweep: dict) -> list:
    """Las 4 llamadas ``SAM2AutomaticMaskGenerator(model, **kwargs).generate(image)`` del sweep."""
    constants = {k: _number(sweep["constants"][k]) for k in CONSTANT_KEYS}
    if constants["output_mode"] != "uncompressed_rle":
        raise ValueError("el sweep fija output_mode = uncompressed_rle")
    plan = []
    for config in sweep["configs"]:
        kwargs = {**constants, **{k: config[k] for k in CONFIG_KEYS}}
        plan.append({"call_id": config["id"].split()[0], "config_id": config["id"], "generator_kwargs": kwargs,
                     "points_per_batch_fallback": list(PPB_FALLBACK)})
    if [c["call_id"] for c in plan] != ["AMG-0", "AMG-1", "AMG-2", "AMG-3"]:
        raise ValueError("el sweep no tiene las cuatro configuraciones prerregistradas en orden")
    return plan


# ─── integridad (sin resultados) ──────────────────────────────────────────────────────────────

def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def packed_sha256_rle(rle: dict) -> str:
    from .masks import packed_sha256
    return packed_sha256(rle_decode(rle))


def integrity(zip_path, protocol: dict, check_masks: bool = True) -> dict:
    """Comprueba el ZIP sin devolver datos de resultado.

    Estados: ``REAL_GPU_EVIDENCE``, ``SIMULATED_RUN_NOT_EVIDENCE``, ``REAL_CPU_NOT_EVIDENCE`` e
    ``INVALID_BUNDLE``.
    """
    zip_path = Path(zip_path)
    problems = []
    data = zip_path.read_bytes()
    out = {"status": None, "run_kind": None, "problems": problems, "zip_sha256": _sha(data), "zip_bytes": len(data),
           "run_id": None, "protocol_content_sha256": None, "environment": None, "calls": None,
           "note": "integridad sin resultados: ni número de máscaras, ni áreas, ni scores"}
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        problems.append("no es un ZIP")
        out["status"] = "INVALID_BUNDLE"
        return out
    names = set(archive.namelist())
    for required in (CONFIG_JSON, CALLS_JSON, REPORT_JSON, MANIFEST_JSON):
        if required not in names:
            problems.append(f"falta {required}")
    if problems:
        out["status"] = "INVALID_BUNDLE"
        return out
    manifest = json.loads(archive.read(MANIFEST_JSON))
    for name, meta in manifest["files"].items():
        if name not in names:
            problems.append(f"el manifiesto lista {name} y no está")
        elif _sha(archive.read(name)) != meta["sha256"] or len(archive.read(name)) != meta["bytes"]:
            problems.append(f"{name}: hash o tamaño distinto del manifiesto")
    extra = names - set(manifest["files"]) - {MANIFEST_JSON}
    if extra:
        problems.append(f"archivos fuera del manifiesto: {sorted(extra)[:3]}")
    config = json.loads(archive.read(CONFIG_JSON))
    calls = json.loads(archive.read(CALLS_JSON))
    out["run_id"] = config.get("run_id")
    out["protocol_content_sha256"] = config.get("protocol_content_sha256")
    env = config.get("environment", {})
    out["environment"] = {k: env.get(k) for k in ("device", "device_name", "dtype", "torch", "sam2_commit",
                                                  "checkpoint_sha256", "image_sha256")}
    if config.get("protocol_content_sha256") != protocol["content_sha256"]:
        problems.append("el cuaderno no embebe este protocolo")
    plan = {c["call_id"]: c for c in protocol["call_plan"]}
    if [c.get("call_id") for c in calls] != list(plan):
        problems.append("las llamadas ejecutadas no son las 4 del plan, en orden")
    for call in calls:
        want = plan.get(call.get("call_id"))
        if want is None:
            continue
        got = dict(call.get("generator_kwargs", {}))
        ppb = got.pop("points_per_batch", None)
        expected = {k: v for k, v in want["generator_kwargs"].items() if k != "points_per_batch"}
        if got != expected:
            problems.append(f"{call['call_id']}: kwargs distintos del plan")
        attempts = call.get("points_per_batch_attempts", [])
        if not attempts or attempts[-1] != ppb or attempts != list(PPB_FALLBACK[:len(attempts)]):
            problems.append(f"{call['call_id']}: points_per_batch fuera de la regla (solo baja por OOM: 64 → 32 → 16)")
        name = f"masks/{call['call_id']}.json"
        if name not in names:
            problems.append(f"falta {name}")
            continue
        if check_masks:
            payload = json.loads(archive.read(name))
            hashes = [m["packed_sha256"] for m in payload["masks"]]
            if hashes != manifest["masks"].get(call["call_id"]):
                problems.append(f"{name}: hashes distintos del manifiesto")
            else:
                for m in payload["masks"]:
                    if packed_sha256_rle(m["rle"]) != m["packed_sha256"]:
                        problems.append(f"{name}: una máscara no reproduce su hash")
                        break
    out["calls"] = [c.get("call_id") for c in calls]
    frozen = protocol["freeze"]
    simulated = env.get("torch") == "SIMULATED" or env.get("sam2_commit") == "SIMULATED"
    if not simulated:
        if env.get("sam2_commit") != frozen["SAM2_GIT_COMMIT"]:
            problems.append("SAM 2 no está en el commit congelado")
        if env.get("checkpoint_sha256") != frozen["CHECKPOINT_SHA256"]:
            problems.append("el checkpoint no es el congelado")
    if env.get("image_sha256") != frozen["IMAGE_SHA256"]:
        problems.append("la foto no es la de aceptación")
    if problems:
        out["status"], out["run_kind"] = "INVALID_BUNDLE", None
    elif simulated:
        out["status"], out["run_kind"] = "SIMULATED_RUN_NOT_EVIDENCE", "SIMULATED"
    elif env.get("device") != "cuda":
        out["status"], out["run_kind"] = "REAL_CPU_NOT_EVIDENCE", "REAL_CPU"
    else:
        out["status"], out["run_kind"] = "REAL_GPU_EVIDENCE", "REAL_GPU"
    return out


# ─── carga de propuestas (memmap: 4000×2248 por máscara sin llenar la RAM) ────────────────────

class ProposalSet:
    """Las máscaras de una configuración, decodificadas en un memmap en disco."""

    def __init__(self, call_id: str, payload: dict, store_dir: Path):
        self.call_id = call_id
        self.meta = [{k: v for k, v in m.items() if k != "rle"} for m in payload["masks"]]
        n = len(payload["masks"])
        store_dir.mkdir(parents=True, exist_ok=True)
        path = store_dir / f"{call_id}.bool"
        self.array = np.memmap(path, dtype=bool, mode="w+", shape=(max(n, 1), H, W))
        for i, m in enumerate(payload["masks"]):
            self.array[i] = rle_decode(m["rle"])
        self.array.flush()
        self.masks = [self.array[i] for i in range(n)]
        self.boxes = [mask_bbox(m) for m in self.masks]
        self.areas = [int(m.sum()) for m in self.masks]
        self.hashes = [m["packed_sha256"] for m in payload["masks"]]


def load_proposals(zip_path, store_dir) -> dict:
    with zipfile.ZipFile(zip_path) as archive:
        calls = json.loads(archive.read(CALLS_JSON))
        return {c["call_id"]: ProposalSet(c["call_id"], json.loads(archive.read(f"masks/{c['call_id']}.json")),
                                          Path(store_dir))
                for c in calls}


# ─── R1 · cribado de cajas ────────────────────────────────────────────────────────────────────

def box_ranking(declared_box, boxes) -> list:
    """(IoU de caja, índice) de mayor a menor; empates por índice menor (igual que ``evaluate``)."""
    scores = [(box_iou(tuple(declared_box), b) if b is not None else 0.0, i) for i, b in enumerate(boxes)]
    return sorted(scores, key=lambda t: (-t[0], t[1]))


def box_screen(objects: list, boxes_by_config: dict) -> dict:
    """Por Tier A: mejor IoU de caja en cada configuración y si dispara R1 (< 0,5 en las cuatro)."""
    out = {}
    for obj in objects:
        if obj["tier"] != "A":
            continue
        per = {}
        for call_id, boxes in boxes_by_config.items():
            ranking = box_ranking(obj["bbox"], boxes)
            per[call_id] = {"best_box_iou": ranking[0][0] if ranking else 0.0,
                            "top": [i for _, i in ranking[:TOP_PER_CONFIG]]}
        out[obj["id"]] = {"per_config": per,
                          "trigger": all(v["best_box_iou"] < BOX_THRESHOLD for v in per.values())}
    return out


def blind_candidates(screen_row: dict, hashes_by_config: dict) -> list:
    """Las 3 mejores por configuración, deduplicadas por hash (≤ 12). Cada una recuerda su origen."""
    seen, out = {}, []
    for call_id, row in screen_row["per_config"].items():
        for rank, index in enumerate(row["top"]):
            h = hashes_by_config[call_id][index]
            if h in seen:
                seen[h]["sources"].append({"call_id": call_id, "index": index, "rank": rank})
                continue
            entry = {"packed_sha256": h, "sources": [{"call_id": call_id, "index": index, "rank": rank}]}
            seen[h] = entry
            out.append(entry)
    return out


def confirm_box_screen(key_a: dict, key_b: dict) -> dict:
    """Por objeto: ``CONFIRMED_BOX_SCREEN_FAILURE`` solo si las dos llaves dicen ``MISS``."""
    out = {}
    for oid in sorted(set(key_a) | set(key_b)):
        a, b = key_a.get(oid), key_b.get(oid)
        for v in (a, b):
            if v is not None and v not in KEY_ANSWERS:
                raise ValueError(f"{oid}: respuesta inválida {v!r}")
        if a == "MISS" and b == "MISS":
            out[oid] = "CONFIRMED_BOX_SCREEN_FAILURE"
        elif a is None or b is None:
            out[oid] = "PENDING_SECOND_KEY"
        else:
            out[oid] = "NOT_CONFIRMED"
    return out


# ─── R2 · cotas a nivel de conjunto ───────────────────────────────────────────────────────────

class PersonReference:
    """Estimación E y zona incierta U de una persona, con lo que las cotas necesitan precalculado."""

    def __init__(self, estimate, uncertain):
        self.e, self.u = as_bool(estimate), as_bool(uncertain)
        self.f = self.e & ~self.u
        self.e_area, self.f_area, self.u_area = int(self.e.sum()), int(self.f.sum()), int(self.u.sum())
        self.region = mask_bbox(self.e | self.u)


def proposal_bounds(p, p_box, p_area, ref: PersonReference) -> dict:
    """Los tres valores de ``keydiff.iou_with_uncertainty`` para una propuesta, sin recorrer la foto entera.

    Toda intersección con E, F o U cae dentro de la caja de E ∪ U; el resto sale de las áreas.
    """
    pe = pf = pu = 0
    if p_box is not None and ref.region is not None and box_iou(p_box, ref.region) > 0:
        x1, y1 = max(p_box[0], ref.region[0]), max(p_box[1], ref.region[1])
        x2, y2 = min(p_box[2], ref.region[2]), min(p_box[3], ref.region[3])
        if x1 < x2 and y1 < y2:
            s = np.s_[y1:y2, x1:x2]
            pp = np.asarray(p[s], dtype=bool)
            pe, pf, pu = int((pp & ref.e[s]).sum()), int((pp & ref.f[s]).sum()), int((pp & ref.u[s]).sum())
    p_or_e = p_area + ref.e_area - pe
    p_or_f = p_area + ref.f_area - pf
    u_out = ref.u_area - pu
    return {
        "iou_estimate": round(pe / p_or_e, 6) if p_or_e else 0.0,
        "iou_min": round(pf / (p_or_f + u_out), 6) if p_or_f + u_out else 0.0,
        "iou_max": round((pf + pu) / p_or_f, 6) if p_or_f else 0.0,
    }


def set_level_verdict(rows: list, threshold: float = STAGE_THRESHOLD) -> dict:
    """``rows``: una fila por propuesta con ``iou_estimate``, ``iou_min`` e ``iou_max``. Empates: índice menor."""
    if not rows:
        return {"verdict": "FAIL", "best_estimate": 0.0, "best_robust_min": 0.0, "best_possible_max": 0.0,
                "argmax_estimate": None, "argmax_min": None, "argmax_max": None, "proposals": 0}

    def arg(key):
        return max(range(len(rows)), key=lambda i: (rows[i][key], -i))
    ie, imin, imax = arg("iou_estimate"), arg("iou_min"), arg("iou_max")
    best_min, best_max = rows[imin]["iou_min"], rows[imax]["iou_max"]
    verdict = "PASS" if best_min >= threshold else ("FAIL" if best_max < threshold else "DEPENDS_ON_UNCERTAINTY")
    return {"verdict": verdict, "best_estimate": rows[ie]["iou_estimate"], "best_robust_min": best_min,
            "best_possible_max": best_max, "argmax_estimate": ie, "argmax_min": imin, "argmax_max": imax,
            "proposals": len(rows)}


def person_r2(proposals: ProposalSet, ref: PersonReference) -> dict:
    rows = [proposal_bounds(m, b, a, ref) for m, b, a in zip(proposals.masks, proposals.boxes, proposals.areas)]
    return set_level_verdict(rows)


# ─── R4 · decisión de etapa ───────────────────────────────────────────────────────────────────

def stage_decision(r1_confirmed: dict, r2: dict) -> dict:
    """``r2``: persona → configuración → veredicto. ``r1_confirmed``: objeto → estado de R1."""
    confirmed = sorted(o for o, s in r1_confirmed.items() if s == "CONFIRMED_BOX_SCREEN_FAILURE")
    pending = sorted(o for o, s in r1_confirmed.items() if s == "PENDING_SECOND_KEY")
    robust_fail = sorted(p for p, per in r2.items() if per and all(v == "FAIL" for v in per.values()))
    if confirmed or robust_fail:
        decision = "FAIL_COMPONENT"
    elif pending:
        decision = "PENDING_R1_REVIEW"
    else:
        decision = "INCONCLUSIVE_GT_INCOMPLETE"
    return {"decision": decision, "confirmed_box_screen_failures": confirmed,
            "persons_fail_all_configs": robust_fail, "r1_pending": pending,
            "next": {"FAIL_COMPONENT": "el componente AMG falla con el sweep agotado: no se pagan las 35 máscaras",
                     "INCONCLUSIVE_GT_INCOMPLETE": "etapa 2: máscaras de los 35 Tier A restantes, por doble llave",
                     "PENDING_R1_REVIEW": "faltan llaves de R1"}[decision],
            "ceiling": "INCONCLUSIVE_GT_INCOMPLETE: la etapa 1 nunca da PASS_PROPOSALS"}


# ─── paquete ciego de R1 ──────────────────────────────────────────────────────────────────────

def _blackout_tags(crop, origin, tag_boxes):
    x0, y0 = origin
    for tx1, ty1, tx2, ty2 in tag_boxes:
        ax1, ay1 = max(tx1 - TAG_PAD_PX - x0, 0), max(ty1 - TAG_PAD_PX - y0, 0)
        ax2, ay2 = min(tx2 + TAG_PAD_PX - x0, crop.shape[1]), min(ty2 + TAG_PAD_PX - y0, crop.shape[0])
        if ax1 < ax2 and ay1 < ay2:
            crop[ay1:ay2, ax1:ax2] = 0
    return crop


def blind_package(zip_path, photo, objects, screen, proposals: dict, out_dir, rng=None) -> dict:
    """Láminas ciegas de R1: por objeto disparado, sus candidatas sin configuración, score ni ranking.

    Devuelve el resumen y escribe ``sealed_mapping.json`` (no va a ChatGPT) y el ZIP ciego.
    """
    from PIL import Image, ImageDraw
    rng = rng or random.Random(BLIND_SEED)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    by_id = {o["id"]: o for o in objects}
    tags = [by_id[t]["bbox"] for t in TAG_IDS if t in by_id]
    hashes = {c: p.hashes for c, p in proposals.items()}
    triggered = sorted(o for o, row in screen.items() if row["trigger"])
    mapping, files, template = {"objects": {}}, {}, {"keys_answer_per_object": list(KEY_ANSWERS), "objects": {}}
    for n, oid in enumerate(triggered, 1):
        label_obj = f"R{n:02d}"
        cands = blind_candidates(screen[oid], hashes)
        rng.shuffle(cands)
        x1, y1, x2, y2 = by_id[oid]["bbox"]
        pad = max(40, int(0.3 * max(x2 - x1, y2 - y1)))
        cx1, cy1, cx2, cy2 = max(0, x1 - pad), max(0, y1 - pad), min(W, x2 + pad), min(H, y2 + pad)
        base = _blackout_tags(np.asarray(photo)[cy1:cy2, cx1:cx2].astype(np.float32).copy(), (cx1, cy1), tags)
        scale = min(1.0, 420 / max(cx2 - cx1, cy2 - cy1))
        cw, ch = max(1, round((cx2 - cx1) * scale)), max(1, round((cy2 - cy1) * scale))
        thumb_scale = 200 / W
        tw, th = round(W * thumb_scale), round(H * thumb_scale)
        full = _blackout_tags(np.asarray(photo).astype(np.float32).copy(), (0, 0), tags)
        thumb_base = np.asarray(Image.fromarray(full.astype(np.uint8)).resize((tw, th), Image.BILINEAR)).astype(np.float32)
        panels = []
        ref = Image.fromarray(base.clip(0, 255).astype(np.uint8)).resize((cw, ch), Image.LANCZOS)
        d = ImageDraw.Draw(ref)
        d.rectangle([(x1 - cx1) * scale, (y1 - cy1) * scale, (x2 - cx1) * scale, (y2 - cy1) * scale], outline=(0, 255, 0), width=2)
        panels.append(("objeto", ref, None))
        entries = []
        for k, cand in enumerate(cands, 1):
            label = f"{label_obj}-K{k:02d}"
            src = cand["sources"][0]
            mask = proposals[src["call_id"]].masks[src["index"]]
            crop_mask = np.asarray(mask[cy1:cy2, cx1:cx2], dtype=bool)
            ov = base * 0.55
            ov[crop_mask] = base[crop_mask] * 0.4 + np.array([255, 0, 200]) * 0.6
            img = Image.fromarray(ov.clip(0, 255).astype(np.uint8)).resize((cw, ch), Image.LANCZOS)
            dd = ImageDraw.Draw(img)
            dd.rectangle([(x1 - cx1) * scale, (y1 - cy1) * scale, (x2 - cx1) * scale, (y2 - cy1) * scale], outline=(0, 255, 0), width=1)
            small = np.asarray(Image.fromarray(np.asarray(mask, dtype=np.uint8) * 255).resize((tw, th), Image.NEAREST)) > 0
            tb = thumb_base * 0.5
            tb[small] = tb[small] * 0.3 + np.array([255, 0, 200]) * 0.7
            timg = Image.fromarray(tb.clip(0, 255).astype(np.uint8))
            ImageDraw.Draw(timg).rectangle([cx1 * thumb_scale, cy1 * thumb_scale, cx2 * thumb_scale, cy2 * thumb_scale],
                                           outline=(0, 255, 0), width=1)
            panels.append((label, img, timg))
            entries.append({"label": label, **cand})
        cols = 3
        cell_w, cell_h = cw + tw + 12, max(ch, th) + 22
        rows_n = (len(panels) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * cell_w, rows_n * cell_h), (20, 20, 20))
        ds = ImageDraw.Draw(sheet)
        for i, (label, img, timg) in enumerate(panels):
            px, py = (i % cols) * cell_w, (i // cols) * cell_h
            ds.text((px + 4, py + 4), label if label != "objeto" else f"{label_obj} · {by_id[oid]['canonical_name']}",
                    fill=(240, 240, 240))
            sheet.paste(img, (px, py + 20))
            if timg is not None:
                sheet.paste(timg, (px + cw + 6, py + 20))
        name = f"{label_obj}.png"
        buf = io.BytesIO()
        sheet.save(buf, format="PNG")
        files[name] = buf.getvalue()
        mapping["objects"][label_obj] = {"object_id": oid, "candidates": entries}
        template["objects"][label_obj] = {"object": by_id[oid]["canonical_name"], "answer": None,
                                          "covering_labels": [], "note": ""}
    leeme = LEEME_R1.format(n=len(triggered))
    files["LEEME.md"] = leeme.encode("utf-8")
    files["plantilla_respuesta.json"] = (json.dumps(template, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    package = out_dir / "PRAGMA_AE1S1_revision_ciega_R1.zip"
    with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as z:
        for name, payload in sorted(files.items()):
            z.writestr(name, payload)
    mapping_bytes = (json.dumps(mapping, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
    (out_dir / "sealed_mapping.json").write_bytes(mapping_bytes)
    return {"package": package.name, "package_sha256": _sha(package.read_bytes()), "objects": len(triggered),
            "labels": sorted(mapping["objects"]), "sealed_mapping_sha256": _sha(mapping_bytes)}


LEEME_R1 = """# PRAGMA · A‑E1 etapa 1 · revisión ciega del cribado de cajas (R1)

Hay {n} objeto(s). Cada lámina `Rnn.png` tiene:

- **objeto:** un recorte de la foto con la caja del objeto en verde;
- **candidatas `Rnn-Kmm`:** máscaras propuestas por un segmentador automático, en magenta. A la
  izquierda, el mismo recorte; a la derecha, la foto entera en miniatura con el recorte en verde.

Las candidatas van en orden aleatorio, sin su origen, sin puntuación y sin ranking. Los rectángulos
negros tapan etiquetas con nombre a propósito.

**Pregunta por objeto:** ¿alguna candidata es una máscara de ESTE objeto? Es decir, que cubra su
parte visible y que lo que añade o deja fuera sea menor (borde, sombra, un reflejo).

- `COVERS_OBJECT`: sí. Indica cuál o cuáles en `covering_labels`.
- `MISS`: ninguna lo es, porque son otra cosa, lo cubren solo en parte o lo mezclan con mucho más.
- `CANNOT_DETERMINE`: no se puede decidir con estas imágenes.

Responde rellenando `plantilla_respuesta.json`. Responde solo con estas imágenes: no abras el
repositorio ni otras cartas.
"""


# ─── análisis completo (tras las llaves de R1) ────────────────────────────────────────────────

def analyze(zip_path, protocol: dict, inventory: dict, gt_dir, store_dir, r1_keys=None) -> dict:
    """Lectura completa de la etapa 1. Con disparadores de R1 sin sus dos llaves, se detiene antes de R2."""
    from PIL import Image
    from .metrics import GateParams, evaluate
    status = integrity(zip_path, protocol, check_masks=True)
    if status["status"] == "INVALID_BUNDLE":
        return {"integrity": status, "stage1": "INVALID_BUNDLE"}
    proposals = load_proposals(zip_path, store_dir)
    objects = inventory["objects"]
    screen = box_screen(objects, {c: p.boxes for c, p in proposals.items()})
    triggered = sorted(o for o, row in screen.items() if row["trigger"])
    r1 = {}
    if triggered:
        if not r1_keys:
            return {"integrity": status, "r1": {"triggered": triggered, "state": "PENDING_BLIND_REVIEW"},
                    "stage1": "PENDING_R1_REVIEW",
                    "note": "R2 y R3 no se calculan hasta archivar las dos llaves de R1 (protocolo, orden)"}
        r1 = confirm_box_screen(*r1_keys)
    gt, refs = {}, {}
    for obj in objects:
        entry = obj.get("gt_mask")
        if entry:
            e = np.asarray(Image.open(Path(gt_dir) / Path(entry["path"]).name).convert("L")) > 0
            u = np.asarray(Image.open(Path(gt_dir) / Path(entry["uncertain_path"]).name).convert("L")) > 0
            gt[obj["id"]] = e
            refs[obj["id"]] = PersonReference(e, u)
    per_config, r2 = {}, {p: {} for p in refs}
    for call_id, props in proposals.items():
        ev = evaluate(objects, gt, props.masks, GateParams())
        persons = {}
        for oid, ref in refs.items():
            row = person_r2(props, ref)
            r2[oid][call_id] = row["verdict"]
            persons[oid] = row
        per_config[call_id] = {
            "gate": ev["gates"]["section9_operational"], "proposals": ev["proposals"],
            "missing_tier_a_gt": len(ev["missing_tier_a_gt"]),
            "tier_a_box_screen_failures": ev["tier_a_box_screen_failures"],
            "r2_persons": persons,
            "r3": {"label": "FUSION_Q_ESTIMATE_BASED", "fusion": ev["fusion"], "contact": ev["contact"]},
        }
    decision = stage_decision({o: r1.get(o, "PENDING_SECOND_KEY") for o in triggered}, r2)
    return {"integrity": status, "r1": {"triggered": triggered, "confirmation": r1},
            "per_config": per_config, "r2_summary": r2, "r4": decision, "stage1": decision["decision"]}
