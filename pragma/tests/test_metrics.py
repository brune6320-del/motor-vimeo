"""El contrato §9 con IoU como único criterio no detecta el fallo documentado en v4.

Escena sintética a 1/10 de escala con las proporciones reales de P1070614.JPG:
la chica ocupa ~15,6 % de la foto (área aceptada en v4) y la persona posterior deja
visible una fracción pequeña detrás de ella. Una propuesta que añade a la chica la
mitad visible de la persona posterior — exactamente el defecto auditado en v4 —
mantiene IoU ≈ 0,94 con la GT de la chica mientras absorbe ~58 % de la otra persona.
"""

import unittest

import numpy as np

from pragma_ae.metrics import GateParams, evaluate

H, W = 225, 400


def scene():
    girl = np.zeros((H, W), bool)
    girl[43:225, 240:317] = True          # 14 014 px = 15,6 % de la imagen (área aceptada en v4: 15,56 %)
    back = np.zeros((H, W), bool)
    back[31:118, 225:262] = True          # la persona posterior, detrás de la chica
    back &= ~girl                         # GT modal: solo lo visible (~1,4 % de la imagen)
    man = np.zeros((H, W), bool)
    man[28:225, 26:120] = True
    objects = [
        {"id": "ae0_001", "tier": "A", "concept_en": "person", "bbox": [26, 28, 120, 225], "parent_id": None, "occluded_by": []},
        {"id": "ae0_002", "tier": "A", "concept_en": "person", "bbox": [240, 43, 317, 225], "parent_id": None, "occluded_by": []},
        {"id": "ae0_003", "tier": "A", "concept_en": "person", "bbox": [225, 31, 262, 118], "parent_id": None, "occluded_by": ["ae0_002"]},
        {"id": "ae0_010", "tier": "B", "concept_en": "clock", "bbox": [278, 8, 300, 34], "parent_id": None, "occluded_by": []},
        {"id": "ae0_011", "tier": "C", "concept_en": "hand", "bbox": [290, 60, 317, 130], "parent_id": "ae0_002", "occluded_by": []},
    ]
    return objects, {"ae0_001": man, "ae0_002": girl, "ae0_003": back}


def clock_proposal():
    m = np.zeros((H, W), bool)
    m[8:34, 278:300] = True
    return m


class SceneProportions(unittest.TestCase):
    def test_scene_matches_real_case(self):
        _, gt = scene()
        self.assertAlmostEqual(gt["ae0_002"].mean(), 0.1556, delta=0.002)
        self.assertTrue(0.010 < gt["ae0_003"].mean() < 0.020)


class FusionLoophole(unittest.TestCase):
    def test_v4_like_contamination_passes_iou_but_not_fusion(self):
        objects, gt = scene()
        back_rows = np.flatnonzero(gt["ae0_003"].any(axis=1))
        half_back = gt["ae0_003"].copy()
        half_back[back_rows[len(back_rows) // 2]:, :] = False   # mitad superior visible: cabello + hombro
        contaminated_girl = gt["ae0_002"] | half_back
        proposals = [gt["ae0_001"], contaminated_girl, gt["ae0_003"], clock_proposal()]
        report = evaluate(objects, gt, proposals, GateParams(contact_band_px=3, fusion_erosion_px=1))  # escala 1/10

        girl = report["per_object"]["ae0_002"]
        self.assertGreater(girl["best_mask_iou"], 0.90)            # el IoU casi no se mueve…
        self.assertTrue(all(report["per_object"][o]["best_mask_iou"] >= 0.70 for o in ("ae0_001", "ae0_002", "ae0_003")))
        leak = next(f for f in report["fusion"] if f["object"] == "ae0_002" and f["invaded"] == "ae0_003")
        self.assertGreaterEqual(leak["leak"], 0.40)                # …pero se llevó ~la mitad de la otra persona
        self.assertTrue(leak["flag"])
        self.assertEqual(report["gates"]["section9_operational"], "GATE_NOT_MET:tier_a_fusion")
        contact = next(c for c in report["contact"] if c["object"] == "ae0_002" and c["neighbour"] == "ae0_003")
        self.assertTrue(contact["flag"])
        self.assertIn("contact_leak", report["gates"]["proposed_v1_1"])

    def test_clean_proposals_meet_gates(self):
        objects, gt = scene()
        proposals = [gt["ae0_001"], gt["ae0_002"], gt["ae0_003"], clock_proposal()]
        report = evaluate(objects, gt, proposals, GateParams(contact_band_px=3, fusion_erosion_px=1))  # escala 1/10
        self.assertEqual(report["gates"]["section9_operational"], "GATE_MET")
        self.assertEqual(report["gates"]["proposed_v1_1"], "GATE_MET")
        self.assertEqual(report["per_object"]["ae0_002"]["fragments_needed"], 1)

    def test_part_whole_is_not_fusion(self):
        objects, gt = scene()
        hand = np.zeros((H, W), bool)
        hand[60:130, 290:317] = True
        gt_with_part = dict(gt, ae0_011=hand & gt["ae0_002"])
        objects = [dict(o, tier="A") if o["id"] == "ae0_011" else o for o in objects]
        proposals = [gt["ae0_001"], gt["ae0_002"], gt["ae0_003"], clock_proposal(), gt_with_part["ae0_011"]]
        report = evaluate(objects, gt_with_part, proposals, GateParams(contact_band_px=3))
        self.assertFalse(any(f["flag"] for f in report["fusion"]
                             if {f["object"], f["invaded"]} == {"ae0_002", "ae0_011"}))

    def test_missing_tier_a_gt_is_inconclusive(self):
        objects, gt = scene()
        del gt["ae0_003"]
        report = evaluate(objects, gt, [gt["ae0_001"], gt["ae0_002"]])
        self.assertEqual(report["gates"]["section9_operational"], "INCONCLUSIVE_GT_INCOMPLETE")

    def test_box_screen_flags_evident_failure_without_masks(self):
        objects, gt = scene()
        only_people_gt = {"ae0_001": gt["ae0_001"], "ae0_002": gt["ae0_002"]}   # etapa 1: faltan máscaras
        report = evaluate(objects, only_people_gt, [gt["ae0_001"], gt["ae0_002"], clock_proposal()])
        self.assertEqual(report["gates"]["section9_operational"], "INCONCLUSIVE_GT_INCOMPLETE")
        self.assertEqual(report["tier_a_box_screen_failures"], ["ae0_003"])     # nadie propuso a la posterior

    def test_fragmented_object_counts_pieces(self):
        objects, gt = scene()
        top, bottom = gt["ae0_002"].copy(), gt["ae0_002"].copy()
        top[134:, :] = False
        bottom[:134, :] = False
        report = evaluate(objects, gt, [gt["ae0_001"], top, bottom, gt["ae0_003"], clock_proposal()])
        self.assertLess(report["per_object"]["ae0_002"]["best_mask_iou"], 0.70)
        self.assertEqual(report["per_object"]["ae0_002"]["fragments_needed"], 2)
        self.assertIn("tier_a_mask_iou", report["gates"]["section9_operational"])


if __name__ == "__main__":
    unittest.main()
