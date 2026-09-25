"""Métricas A-E1 contra un inventario A-E0 congelado (independientes del modelo).

Operacionaliza PROJECT_STATE §9 y añade dos métricas propuestas (ver
``ae0/ONTOLOGIA_PROPUESTA.md`` · DEC-013-P):

- ``fusion_leak``: qué fracción de *otra* instancia Tier A absorbe la mejor propuesta
  de una instancia. Se normaliza por el área de la instancia invadida, no por la
  propia: un IoU global alto puede esconder que la máscara de la chica se llevó la
  mitad visible de la persona posterior (ver ``tests/test_metrics.py``).
- ``contact_leak``: la misma fuga medida solo en la franja donde dos instancias se
  tocan por oclusión, que es donde fallan los segmentadores (el caso v4).

Ningún umbral de aquí está ratificado; todos viven en ``GateParams`` y se registran
en el informe para que el veredicto se pueda recalcular.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .inventory import lineage
from .masks import area, as_bool, box_iou, dilate_square, intersection_area, mask_bbox


@dataclass(frozen=True)
class GateParams:
    # §9 (provisionales, pendientes de ratificación)
    tier_a_mask_iou: float = 0.70
    tier_b_box_iou: float = 0.50
    tier_b_recall: float = 0.90
    report_iou_levels: tuple = (0.50, 0.75)
    # DEC-013-P (propuestos en v1.1, pendientes de ratificación)
    fusion_leak_max: float = 0.10
    contact_band_px: int = 24
    contact_leak_max: float = 0.20
    # diagnósticos
    duplicate_iou: float = 0.70
    fragment_purity: float = 0.80


def _pair_iou(gt, gt_box, gt_area, prop, prop_box, prop_area):
    if gt_box is None or prop_box is None:
        return 0.0
    if box_iou(gt_box, prop_box) == 0.0:
        return 0.0
    inter = intersection_area(gt, prop, gt_box, prop_box)
    union = gt_area + prop_area - inter
    return inter / union if union else 0.0


def _fragmentation(gt, gt_area, proposals, boxes, areas, params):
    """Mínimo aproximado (voraz) de propuestas 'puras' cuya unión alcanza el IoU de Tier A."""
    pure = []
    for index, prop in enumerate(proposals):
        if areas[index] == 0:
            continue
        inter = intersection_area(gt, prop, None, boxes[index])
        if inter and inter / areas[index] >= params.fragment_purity:
            pure.append((inter, index))
    pure.sort(reverse=True)
    union = np.zeros_like(gt)
    for count, (_, index) in enumerate(pure, start=1):
        union |= proposals[index]
        inter = int(np.logical_and(union, gt).sum())
        iou = inter / (gt_area + int(union.sum()) - inter)
        if iou >= params.tier_a_mask_iou:
            return count
    return None


def evaluate(objects: list[dict], gt_masks: dict, proposals: list, params: GateParams = GateParams()) -> dict:
    """Compara propuestas (máscaras booleanas) con el inventario.

    ``objects``: lista de SceneObject (dicts del inventario congelado).
    ``gt_masks``: id → máscara booleana GT (al menos Tier A).
    ``proposals``: máscaras en el orden del ProposalRegistry; el índice es su ID local.
    """
    by_id = {o["id"]: o for o in objects}
    proposals = [as_bool(p) for p in proposals]
    boxes = [mask_bbox(p) for p in proposals]
    areas = [area(p) for p in proposals]

    per_object = {}
    for obj in objects:
        oid = obj["id"]
        if obj["tier"] not in ("A", "B"):
            continue
        row = {"tier": obj["tier"], "concept_en": obj["concept_en"], "has_gt_mask": oid in gt_masks}
        gt_box_declared = tuple(obj["bbox"])
        best_box = max(
            ((box_iou(gt_box_declared, b), i) for i, b in enumerate(boxes) if b is not None),
            default=(0.0, None),
        )
        row["best_box_iou"], row["best_box_proposal"] = best_box
        if oid in gt_masks:
            gt = as_bool(gt_masks[oid])
            gt_box, gt_area = mask_bbox(gt), area(gt)
            ious = [_pair_iou(gt, gt_box, gt_area, p, boxes[i], areas[i]) for i, p in enumerate(proposals)]
            # Oráculo de evaluación (mejor propuesta frente a la GT), no selector de producto (DEC-005).
            best = max(range(len(ious)), key=ious.__getitem__) if ious else None
            row["best_mask_iou"] = float(ious[best]) if best is not None else 0.0
            row["best_mask_proposal"] = best
            row["recall_at"] = {str(t): row["best_mask_iou"] >= t for t in params.report_iou_levels}
            row["duplicates"] = int(sum(v >= params.duplicate_iou for v in ious))
            row["fragments_needed"] = _fragmentation(gt, gt_area, proposals, boxes, areas, params)
        per_object[oid] = row

    # Fusión y contacto: solo para instancias con GT y mejor propuesta definida.
    fusion, contact = [], []
    tier_a_with_mask = [o["id"] for o in objects if o["tier"] == "A" and o["id"] in gt_masks]
    for oid in tier_a_with_mask:
        best = per_object[oid].get("best_mask_proposal")
        if best is None:
            continue
        prop, prop_box = proposals[best], boxes[best]
        excluded = lineage(by_id, oid)
        for other in tier_a_with_mask:
            if other == oid or other in excluded:
                continue
            other_mask = as_bool(gt_masks[other])
            other_area = area(other_mask)
            if not other_area:
                continue
            leak = intersection_area(prop, other_mask, prop_box, None) / other_area
            fusion.append({"object": oid, "invaded": other, "proposal": best, "leak": round(leak, 6),
                           "flag": leak >= params.fusion_leak_max})
        neighbours = set(by_id[oid].get("occluded_by", [])) | {
            o["id"] for o in objects if oid in o.get("occluded_by", [])
        }
        for other in sorted(neighbours & set(gt_masks)):
            if other in excluded:
                continue
            band = dilate_square(gt_masks[oid], params.contact_band_px) & as_bool(gt_masks[other])
            band_area = int(band.sum())
            if not band_area:
                continue
            leak = int(np.logical_and(prop, band).sum()) / band_area
            contact.append({"object": oid, "neighbour": other, "proposal": best, "band_px": band_area,
                            "leak": round(leak, 6), "flag": leak >= params.contact_leak_max})

    tier_a = [o["id"] for o in objects if o["tier"] == "A"]
    tier_b = [o["id"] for o in objects if o["tier"] == "B"]
    missing_gt = sorted(set(tier_a) - set(gt_masks))
    a_ok = [oid for oid in tier_a if per_object[oid].get("best_mask_iou", 0.0) >= params.tier_a_mask_iou]
    b_ok = [oid for oid in tier_b if per_object[oid]["best_box_iou"] >= params.tier_b_box_iou]
    b_recall = len(b_ok) / len(tier_b) if tier_b else 1.0
    # Cribado barato (solo cajas): una instancia Tier A sin ninguna propuesta con box-IoU ≥ 0,5 es un
    # fallo evidente del proponente aunque aún no existan todas las máscaras GT (etapa 1 del protocolo A-E0).
    box_screen_failures = [oid for oid in tier_a if per_object[oid]["best_box_iou"] < params.tier_b_box_iou]
    fused = [f for f in fusion if f["flag"]]
    contact_flags = [c for c in contact if c["flag"]]

    def verdict(extra_failures):
        if missing_gt:
            return "INCONCLUSIVE_GT_INCOMPLETE"
        failures = []
        if len(a_ok) < len(tier_a):
            failures.append("tier_a_mask_iou")
        if b_recall < params.tier_b_recall:
            failures.append("tier_b_box_recall")
        if fused:
            failures.append("tier_a_fusion")
        failures += extra_failures
        return "GATE_MET" if not failures else "GATE_NOT_MET:" + ",".join(failures)

    return {
        "params": asdict(params),
        "proposals": len(proposals),
        "per_object": per_object,
        "tier_a_recall": len(a_ok) / len(tier_a) if tier_a else 1.0,
        "tier_b_box_recall": b_recall,
        "fusion": fusion,
        "contact": contact,
        "missing_tier_a_gt": missing_gt,
        "tier_a_box_screen_failures": box_screen_failures,
        "gates": {
            # §9 con la cláusula 'ninguna máscara Tier A fusiona dos instancias' hecha medible.
            "section9_operational": verdict([]),
            # DEC-013-P: además, la franja de contacto por oclusión no puede fugarse.
            "proposed_v1_1": verdict(["contact_leak"] if contact_flags else []),
        },
        "note": ("Veredicto por corrida. FAIL_COMPONENT solo tras agotar el sweep prefijado; "
                 "el mejor IoU usa un oráculo de evaluación, no un selector de producto."),
    }
