import json
import random
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pragma_ae import ae1_stage1 as s1  # noqa: E402
from pragma_ae.keydiff import iou_with_uncertainty  # noqa: E402
from pragma_ae.masks import mask_bbox  # noqa: E402
from pragma_ae.metrics import GateParams, evaluate  # noqa: E402


class SetLevelBounds(unittest.TestCase):
    """R2 (ChatGPT 019): el veredicto se lee sobre el conjunto de propuestas, no sobre la mejor estimación."""

    def test_chatgpt_example_robust_pass_comes_from_another_proposal(self):
        rows = [{"iou_estimate": 0.75, "iou_min": 0.62, "iou_max": 0.80},
                {"iou_estimate": 0.72, "iou_min": 0.71, "iou_max": 0.74}]
        out = s1.set_level_verdict(rows)
        self.assertEqual(out["verdict"], "PASS")
        self.assertEqual((out["argmax_estimate"], out["argmax_min"]), (0, 1))

    def test_fail_only_when_no_proposal_can_reach_the_threshold(self):
        self.assertEqual(s1.set_level_verdict([{"iou_estimate": 0.6, "iou_min": 0.5, "iou_max": 0.69}])["verdict"], "FAIL")
        self.assertEqual(s1.set_level_verdict([{"iou_estimate": 0.6, "iou_min": 0.5, "iou_max": 0.70}])["verdict"],
                         "DEPENDS_ON_UNCERTAINTY")
        self.assertEqual(s1.set_level_verdict([])["verdict"], "FAIL")

    def test_fast_bounds_equal_keydiff(self):
        rng = np.random.default_rng(7)
        for _ in range(6):
            e = np.zeros((60, 80), bool); e[10:40, 15:55] = True
            u = np.zeros_like(e); u[5:45, 10:25] = rng.random((40, 15)) > 0.4
            p = np.zeros_like(e)
            y, x = rng.integers(0, 30), rng.integers(0, 40)
            p[y:y + 25, x:x + 35] = True
            ref = s1.PersonReference(e, u)
            got = s1.proposal_bounds(p, mask_bbox(p), int(p.sum()), ref)
            want = iou_with_uncertainty(p, e, u)
            self.assertEqual(got, {"iou_estimate": want["metric_all_pixels_estimate"],
                                   "iou_min": want["metric_all_pixels_min"], "iou_max": want["metric_all_pixels_max"]})

    def test_fast_bounds_for_a_disjoint_or_empty_proposal(self):
        e = np.zeros((30, 30), bool); e[5:15, 5:15] = True
        u = np.zeros_like(e); u[4:16, 4:6] = True
        far = np.zeros_like(e); far[25:29, 25:29] = True
        ref = s1.PersonReference(e, u)
        for p in (far, np.zeros_like(e)):
            want = iou_with_uncertainty(p, e, u)
            got = s1.proposal_bounds(p, mask_bbox(p), int(p.sum()), ref)
            self.assertEqual((got["iou_estimate"], got["iou_min"], got["iou_max"]),
                             (want["metric_all_pixels_estimate"], want["metric_all_pixels_min"], want["metric_all_pixels_max"]))


class BoxScreen(unittest.TestCase):
    def objects(self):
        base = {"canonical_name": "x", "concept_en": "thing", "kind": "instance", "occlusion": "none",
                "truncation": "none", "parent_id": None, "occluded_by": [], "gt_required": False, "gt_mask": None,
                "ignore_reason": None, "review": []}
        return [dict(base, id="ae0_101", tier="A", bbox=[10, 10, 30, 30]),
                dict(base, id="ae0_102", tier="A", bbox=[40, 5, 70, 25]),
                dict(base, id="ae0_103", tier="B", bbox=[0, 40, 20, 60])]

    def test_trigger_needs_all_four_configs_below_half(self):
        good, bad = (10, 10, 30, 30), (0, 0, 80, 60)
        boxes = {c: [bad] for c in ("AMG-0", "AMG-1", "AMG-2", "AMG-3")}
        screen = s1.box_screen(self.objects(), boxes)
        self.assertTrue(screen["ae0_101"]["trigger"])
        self.assertNotIn("ae0_103", screen)                      # solo Tier A
        boxes["AMG-2"] = [bad, good]
        self.assertFalse(s1.box_screen(self.objects(), boxes)["ae0_101"]["trigger"])

    def test_best_box_iou_equals_evaluate(self):
        rng = np.random.default_rng(3)
        masks = []
        for _ in range(7):
            m = np.zeros((60, 80), bool)
            y, x = rng.integers(0, 40), rng.integers(0, 60)
            m[y:y + rng.integers(5, 20), x:x + rng.integers(5, 20)] = True
            masks.append(m)
        objs = self.objects()
        ev = evaluate(objs, {}, masks, GateParams())
        screen = s1.box_screen(objs, {"AMG-0": [mask_bbox(m) for m in masks]})
        for oid in ("ae0_101", "ae0_102"):
            self.assertEqual(screen[oid]["per_config"]["AMG-0"]["best_box_iou"], ev["per_object"][oid]["best_box_iou"])

    def test_candidates_are_top3_per_config_deduplicated(self):
        row = {"per_config": {c: {"best_box_iou": 0.1, "top": [0, 1, 2]} for c in ("AMG-0", "AMG-1", "AMG-2", "AMG-3")}}
        hashes = {"AMG-0": ["a", "b", "c"], "AMG-1": ["a", "d", "e"], "AMG-2": ["f", "g", "h"], "AMG-3": ["i", "j", "a"]}
        cands = s1.blind_candidates(row, hashes)
        self.assertEqual(len(cands), 10)                          # «a» aparece tres veces
        self.assertEqual(len(next(c for c in cands if c["packed_sha256"] == "a")["sources"]), 3)
        self.assertLessEqual(len(cands), 12)

    def test_triage_two_miss_only_escalates(self):
        """ChatGPT 020: MISS en el triaje (3 por configuración) no es MISS sobre todas las propuestas."""
        a = {"R1": "MISS", "R2": "MISS", "R3": "MISS", "R4": "COVERS_OBJECT"}
        b = {"R1": "MISS", "R2": "CANNOT_DETERMINE", "R3": "COVERS_OBJECT"}
        out = s1.combine_r1_keys(a, b, "TRIAGE")
        self.assertEqual(out["R1"], "ESCALATE_TO_EXHAUSTIVE")
        self.assertEqual((out["R2"], out["R3"]), ("NOT_CONFIRMED", "NOT_CONFIRMED"))
        self.assertEqual(out["R4"], "PENDING_SECOND_KEY")
        with self.assertRaises(ValueError):
            s1.combine_r1_keys({"R1": "MAYBE"}, {"R1": "MISS"}, "TRIAGE")

    def test_exhaustive_miss_counts_only_after_all_pages(self):
        full = {"answer": "MISS", "reviewed_all_pages": True}
        self.assertEqual(s1.combine_r1_keys({"o": full}, {"o": full}, "EXHAUSTIVE")["o"], "CONFIRMED_BOX_SCREEN_FAILURE")
        for partial in ({"answer": "MISS", "reviewed_all_pages": False}, {"answer": "MISS"}, "MISS"):
            self.assertEqual(s1.combine_r1_keys({"o": full}, {"o": partial}, "EXHAUSTIVE")["o"], "NOT_CONFIRMED")
        for other in ("COVERS_OBJECT", "CANNOT_DETERMINE"):
            self.assertEqual(s1.combine_r1_keys({"o": full}, {"o": {"answer": other}}, "EXHAUSTIVE")["o"],
                             "NOT_CONFIRMED")

    def test_resolution_needs_both_phases(self):
        miss = {"answer": "MISS", "reviewed_all_pages": True}
        triage = ({"ae0_012": "MISS", "ae0_029": "MISS"}, {"ae0_012": "MISS", "ae0_029": "COVERS_OBJECT"})
        r = s1.r1_resolution(["ae0_012", "ae0_029"], triage)
        self.assertEqual(r["state"], {"ae0_012": "PENDING_EXHAUSTIVE_REVIEW", "ae0_029": "NOT_CONFIRMED"})
        self.assertEqual(r["escalated"], ["ae0_012"])
        self.assertEqual(s1.r1_resolution(["ae0_012", "ae0_029"])["state"]["ae0_012"], "PENDING_TRIAGE_REVIEW")
        done = s1.r1_resolution(["ae0_012", "ae0_029"], triage, ({"ae0_012": miss}, {"ae0_012": miss}))
        self.assertEqual(done["state"]["ae0_012"], "CONFIRMED_BOX_SCREEN_FAILURE")
        with self.assertRaises(ValueError):          # la fase exhaustiva solo cubre objetos escalados
            s1.r1_resolution(["ae0_012", "ae0_029"], triage, ({"ae0_029": miss}, {"ae0_029": miss}))

    def test_exhaustive_set_reaches_a_mask_below_the_triage(self):
        """El escenario de ChatGPT 020: caja de inventario holgada y la máscara buena, 5.ª por IoU de caja."""
        obj = [100, 100, 200, 200]
        good = (140, 130, 165, 185)                           # la máscara del objeto, más estrecha que la caja
        decoys = [(100, 100, 160, 160), (120, 100, 190, 160), (100, 130, 170, 190), (130, 120, 190, 180)]
        far, touching = (300, 300, 320, 320), (200, 100, 250, 150)   # esta solo toca el borde: no corta
        boxes = {"AMG-0": decoys + [good, far, touching, None], "AMG-1": [good]}
        hashes = {"AMG-0": ["d1", "d2", "d3", "d4", "good", "far", "touch", "empty"], "AMG-1": ["good"]}
        ranking = s1.box_ranking(obj, boxes["AMG-0"])
        self.assertTrue(all(iou < s1.BOX_THRESHOLD for iou, _ in ranking))
        self.assertNotIn(4, [i for _, i in ranking[:s1.TOP_PER_CONFIG]])
        cands = s1.exhaustive_candidates(obj, boxes, hashes)
        self.assertEqual([c["packed_sha256"] for c in cands], ["d1", "d2", "d3", "d4", "good"])
        self.assertEqual(next(c for c in cands if c["packed_sha256"] == "good")["sources"],
                         [{"call_id": "AMG-0", "index": 4}, {"call_id": "AMG-1", "index": 0}])

    def test_pages_have_no_cap(self):
        self.assertEqual([len(p) for p in s1.paginate(list(range(30)))], [12, 12, 6])
        self.assertEqual(sum(len(p) for p in s1.paginate(list(range(250)))), 250)
        self.assertEqual(s1.paginate([]), [[]])

    def test_key_from_answers_maps_labels_and_checks_covering_labels(self):
        mapping = {"objects": {"R01": {"object_id": "ae0_012", "candidates": [{"label": "R01-X01"}]}}}
        answers = {"objects": {"R01": {"answer": "COVERS_OBJECT", "covering_labels": ["R01-X01"],
                                       "reviewed_all_pages": True}}}
        self.assertEqual(s1.key_from_answers(answers, mapping),
                         {"ae0_012": {"answer": "COVERS_OBJECT", "reviewed_all_pages": True}})
        answers["objects"]["R01"]["covering_labels"] = ["R02-X01"]
        with self.assertRaises(ValueError):
            s1.key_from_answers(answers, mapping)


class StageDecision(unittest.TestCase):
    """R4 (ChatGPT 019): basta una persona con FAIL robusto en las cuatro configuraciones."""

    def configs(self, *verdicts):
        return dict(zip(("AMG-0", "AMG-1", "AMG-2", "AMG-3"), verdicts))

    def test_one_person_failing_everywhere_is_enough(self):
        r2 = {"ae0_001": self.configs("FAIL", "FAIL", "FAIL", "FAIL"),
              "ae0_002": self.configs("PASS", "PASS", "PASS", "PASS"), "ae0_003": self.configs(*["PASS"] * 4)}
        out = s1.stage_decision({}, r2)
        self.assertEqual(out["decision"], "FAIL_COMPONENT")
        self.assertEqual(out["persons_fail_all_configs"], ["ae0_001"])

    def test_depends_or_partial_fail_never_fails(self):
        r2 = {"ae0_001": self.configs("FAIL", "FAIL", "FAIL", "DEPENDS_ON_UNCERTAINTY"),
              "ae0_002": self.configs(*["DEPENDS_ON_UNCERTAINTY"] * 4)}
        self.assertEqual(s1.stage_decision({}, r2)["decision"], "INCONCLUSIVE_GT_INCOMPLETE")

    def test_confirmed_box_screen_failure_fails_and_pending_waits(self):
        self.assertEqual(s1.stage_decision({"ae0_020": "CONFIRMED_BOX_SCREEN_FAILURE"}, {})["decision"], "FAIL_COMPONENT")
        for pending in ("PENDING_TRIAGE_REVIEW", "PENDING_EXHAUSTIVE_REVIEW", "PENDING_SECOND_KEY"):
            self.assertEqual(s1.stage_decision({"ae0_020": pending}, {})["decision"], "PENDING_R1_REVIEW")
        self.assertEqual(s1.stage_decision({"ae0_020": "NOT_CONFIRMED"}, {})["decision"], "INCONCLUSIVE_GT_INCOMPLETE")

    def test_triage_outcome_is_never_a_final_state(self):
        with self.assertRaises(ValueError):
            s1.stage_decision({"ae0_020": "ESCALATE_TO_EXHAUSTIVE"}, {})


class PrecisionGate(unittest.TestCase):
    """ChatGPT 020: solo cuenta una corrida CUDA en bfloat16 con capacidad ≥ 8."""

    def bundle(self, **env_changes):
        import hashlib
        import tempfile
        import zipfile
        protocol = json.loads((ROOT / "ae1" / "AE1_STAGE1_READING_PROTOCOL.json").read_text(encoding="utf-8"))
        frozen = protocol["freeze"]
        env = {"device": "cuda", "device_name": "NVIDIA L4", "cuda_capability": [8, 9], "dtype": "bfloat16",
               "torch": "2.8.0+cu126", "sam2_commit": frozen["SAM2_GIT_COMMIT"],
               "checkpoint_sha256": frozen["CHECKPOINT_SHA256"], "image_sha256": frozen["IMAGE_SHA256"]}
        env.update(env_changes)
        env = {k: v for k, v in env.items() if v != "DROP"}
        calls = [{"call_id": c["call_id"], "config_id": c["config_id"], "generator_kwargs": dict(c["generator_kwargs"]),
                  "points_per_batch_attempts": [64]} for c in protocol["call_plan"]]
        items = {s1.CONFIG_JSON: {"run_id": "T", "protocol_content_sha256": protocol["content_sha256"], "environment": env},
                 s1.CALLS_JSON: calls, s1.REPORT_JSON: {"run_id": "T"}}
        items.update({f"masks/{c['call_id']}.json": {"call_id": c["call_id"], "masks": []} for c in calls})
        data = {n: json.dumps(v).encode() for n, v in items.items()}
        manifest = {"files": {n: {"bytes": len(d), "sha256": hashlib.sha256(d).hexdigest()} for n, d in data.items()},
                    "masks": {c["call_id"]: [] for c in calls}}
        data[s1.MANIFEST_JSON] = json.dumps(manifest).encode()
        path = Path(tempfile.mkdtemp()) / "bundle.zip"
        with zipfile.ZipFile(path, "w") as z:
            for n, d in data.items():
                z.writestr(n, d)
        return s1.integrity(path, protocol)

    def test_bf16_with_capability_8_or_more_is_evidence(self):
        for cap in ([8, 9], [8, 0], [9, 0]):                   # L4, A100, H100
            out = self.bundle(cuda_capability=cap)
            self.assertEqual(out["status"], "REAL_GPU_EVIDENCE", out["problems"])
            self.assertEqual(out["environment"]["cuda_capability"], cap)

    def test_fp16_gpu_is_not_evidence(self):
        out = self.bundle(device_name="Tesla T4", cuda_capability=[7, 5], dtype="float16")
        self.assertEqual(out["status"], "REAL_GPU_DIFFERENT_PRECISION_NOT_EVIDENCE")

    def test_capability_is_required_and_must_match_the_dtype(self):
        self.assertEqual(self.bundle(cuda_capability="DROP")["status"], "INVALID_BUNDLE")
        self.assertEqual(self.bundle(dtype="float16")["status"], "INVALID_BUNDLE")
        self.assertEqual(self.bundle(cuda_capability=[7, 5])["status"], "INVALID_BUNDLE")

    def test_cpu_is_not_evidence(self):
        out = self.bundle(device="cpu", device_name="CPU", cuda_capability=None, dtype="float32")
        self.assertEqual(out["status"], "REAL_CPU_NOT_EVIDENCE")


class Protocol(unittest.TestCase):
    def test_call_plan_is_the_preregistered_sweep(self):
        sweep = json.loads((ROOT / "ae1" / "SWEEP_PRERREGISTRO_A-E1.json").read_text(encoding="utf-8"))
        plan = s1.call_plan(sweep)
        self.assertEqual([c["call_id"] for c in plan], ["AMG-0", "AMG-1", "AMG-2", "AMG-3"])
        for call, config in zip(plan, sweep["configs"]):
            for k in s1.CONFIG_KEYS:
                self.assertEqual(call["generator_kwargs"][k], config[k])
            self.assertEqual(call["generator_kwargs"]["crop_overlap_ratio"], 512 / 1500)
            self.assertEqual(call["generator_kwargs"]["output_mode"], "uncompressed_rle")

    def test_protocol_binds_frozen_contract_sweep_a_e0_and_reader(self):
        import hashlib
        protocol = json.loads((ROOT / "ae1" / "AE1_STAGE1_READING_PROTOCOL.json").read_text(encoding="utf-8"))
        for key in ("contract", "sweep", "a_e0", "reader"):
            ref = protocol["binds"][key]
            self.assertEqual(hashlib.sha256((ROOT / ref["file"]).read_bytes()).hexdigest(), ref["sha256"], key)
        self.assertEqual(protocol["stage"]["ceiling"], "INCONCLUSIVE_GT_INCOMPLETE")
        self.assertEqual(protocol["call_plan"], s1.call_plan(
            json.loads((ROOT / protocol["binds"]["sweep"]["file"]).read_text(encoding="utf-8"))))


if __name__ == "__main__":
    unittest.main()
