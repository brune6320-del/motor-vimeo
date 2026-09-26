"""Comparación de dos llaves de inventario A‑E0 (DEC‑024), con la regla fijada ANTES de ver ninguna llave.

Cada llave es un inventario ``pragma.scene_inventory`` hecho por un auditor distinto, cada uno con su
propia numeración ``ae0_NNN``. Los objetos se emparejan por geometría y los atributos se comparan
después. El código dice qué coincide y qué no; la adjudicación dice qué significa (igual que DEC‑025
con las máscaras).

Regla:
1. **Emparejamiento:** son candidatos los pares (a, b) con IoU de caja ≥ ``MATCH_IOU`` (0,5). Se
   emparejan de forma voraz por IoU descendente; los empates se rompen por (id de A, id de B). Es
   uno a uno y determinista.
2. **Pares emparejados:**
   - caja: con IoU ≥ ``AUTO_BOX_IOU`` (0,85), la caja de referencia es la media redondeada de las
     dos (``BOX_AUTO_MEAN``); si no, ``BOX_ADJUDICATE``;
   - atributos ``kind``, ``tier``, ``occlusion`` y ``truncation``: cada desacuerdo se lista;
   - relaciones ``parent_id`` y ``occluded_by``: se traducen por el emparejamiento y se comparan.
3. **Sin pareja:** ``A_ONLY_OBJECT`` o ``B_ONLY_OBJECT``. Se adjudica como ``INCLUDE``,
   ``EXCLUDE`` (con motivo) o ``SAME_AS:<id>`` (es el mismo objeto con una caja muy distinta).
   - Como pista se listan el candidato de mayor IoU y la **contención** (fracción de la caja menor
     dentro de la mayor). Una contención ≥ 0,9 sugiere una partición distinta: un entero en una
     llave y sus partes en la otra.
4. **Personas:** una persona (``concept_en == "person"``) sin pareja es prioridad alta, porque toda
   persona es A con máscara obligatoria (R1).
"""

from __future__ import annotations

MATCH_IOU = 0.5
AUTO_BOX_IOU = 0.85
CONTAINMENT_HINT = 0.9
ATTRIBUTES = ("kind", "tier", "occlusion", "truncation")
UNMATCHED_ADJUDICATIONS = ("INCLUDE", "EXCLUDE", "SAME_AS")


def box_iou(a, b) -> float:
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union else 0.0


def containment(a, b) -> float:
    """Fracción de la caja menor que cae dentro de la otra."""
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    smaller = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
    return ix * iy / smaller if smaller else 0.0


def _objects(key: dict) -> list:
    return key["objects"] if isinstance(key, dict) else list(key)


def _is_person(obj) -> bool:
    return str(obj.get("concept_en", "")).strip().lower() == "person"


def match_keys(key_a, key_b, match_iou: float = MATCH_IOU, auto_box_iou: float = AUTO_BOX_IOU) -> dict:
    a_objs, b_objs = _objects(key_a), _objects(key_b)
    a_by, b_by = {o["id"]: o for o in a_objs}, {o["id"]: o for o in b_objs}
    if len(a_by) != len(a_objs) or len(b_by) != len(b_objs):
        raise ValueError("ids repetidos dentro de una llave")
    candidates = sorted(((box_iou(a["bbox"], b["bbox"]), a["id"], b["id"]) for a in a_objs for b in b_objs),
                        key=lambda c: (-c[0], c[1], c[2]))
    a_to_b, b_to_a, pairs = {}, {}, []
    for iou, aid, bid in candidates:
        if iou < match_iou:
            break
        if aid in a_to_b or bid in b_to_a:
            continue
        a_to_b[aid], b_to_a[bid] = bid, aid
        pairs.append((iou, aid, bid))

    matched = []
    for iou, aid, bid in sorted(pairs, key=lambda p: p[1]):
        a, b = a_by[aid], b_by[bid]
        box_status = "BOX_AUTO_MEAN" if iou >= auto_box_iou else "BOX_ADJUDICATE"
        disagreements = {f: [a.get(f), b.get(f)] for f in ATTRIBUTES if a.get(f) != b.get(f)}
        parent_a = a.get("parent_id")
        parent_b = b.get("parent_id")
        if (a_to_b.get(parent_a) if parent_a else None) != parent_b:
            disagreements["parent_id"] = [parent_a, parent_b]
        occ_a = sorted(a_to_b.get(x, f"A:{x}") for x in a.get("occluded_by") or [])
        occ_b = sorted(b.get("occluded_by") or [])
        if occ_a != occ_b:
            disagreements["occluded_by"] = [sorted(a.get("occluded_by") or []), occ_b]
        matched.append({
            "a_id": aid, "b_id": bid, "iou": round(iou, 4), "box_status": box_status,
            "reference_bbox": [round((p + q) / 2) for p, q in zip(a["bbox"], b["bbox"])] if box_status == "BOX_AUTO_MEAN" else None,
            "names": [a.get("canonical_name"), b.get("canonical_name")],
            "disagreements": disagreements,
        })

    def unmatched(objs, other, side):
        out = []
        for o in objs:
            if (side == "A" and o["id"] in a_to_b) or (side == "B" and o["id"] in b_to_a):
                continue
            best = max(((box_iou(o["bbox"], p["bbox"]), containment(o["bbox"], p["bbox"]), p["id"]) for p in other),
                       default=(0.0, 0.0, None))
            contain = max(((containment(o["bbox"], p["bbox"]), p["id"]) for p in other), default=(0.0, None))
            out.append({
                "id": o["id"], "side": f"{side}_ONLY_OBJECT", "name": o.get("canonical_name"),
                "kind": o.get("kind"), "tier": o.get("tier"), "bbox": o["bbox"],
                "priority": "HIGH_PERSON" if _is_person(o) else "NORMAL",
                "best_candidate": {"id": best[2], "iou": round(best[0], 4)},
                "max_containment": {"id": contain[1], "fraction": round(contain[0], 4),
                                    "partition_hint": contain[0] >= CONTAINMENT_HINT},
                "adjudication": None,
            })
        return out

    a_only, b_only = unmatched(a_objs, b_objs, "A"), unmatched(b_objs, a_objs, "B")
    summary = {
        "rule": {"match_iou": match_iou, "auto_box_iou": auto_box_iou, "attributes": list(ATTRIBUTES)},
        "n_a": len(a_objs), "n_b": len(b_objs), "matched": len(matched),
        "a_only": len(a_only), "b_only": len(b_only),
        "coverage_of_a": round(len(matched) / len(a_objs), 4) if a_objs else 0.0,
        "coverage_of_b": round(len(matched) / len(b_objs), 4) if b_objs else 0.0,
        "box_auto": sum(m["box_status"] == "BOX_AUTO_MEAN" for m in matched),
        "box_adjudicate": sum(m["box_status"] == "BOX_ADJUDICATE" for m in matched),
        "pairs_with_disagreements": sum(bool(m["disagreements"]) for m in matched),
        "unmatched_persons": sum(u["priority"] == "HIGH_PERSON" for u in a_only + b_only),
    }
    return {"summary": summary, "matched": matched, "a_only": a_only, "b_only": b_only}
