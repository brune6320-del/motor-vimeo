"""Diseño A-E(−1) v1.3 (ChatGPT 002 · Claude 003): perturbaciones, validez, propiedad y prerregistro."""

import hashlib
import json
import unittest
from pathlib import Path

import numpy as np

from pragma_ae import aem1_v13 as v
from pragma_ae.aem1_audit import run_components
from pragma_ae.masks import components, enclosed_holes

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "aem1" / "PRERREGISTRO_A-E-menos-1_v1_3.json"
BASE_BOX = (2100, 300, 3500, 2247)
SIZE = (4000, 2248)


class PointPerturbations(unittest.TestCase):
    def test_ring_is_deterministic_linf_15_axial_first(self):
        rows = v.point_perturbations((2588, 1785))
        self.assertEqual(len(rows), 8)
        self.assertEqual([(r["dx"], r["dy"]) for r in rows[:4]], [(15, 0), (-15, 0), (0, 15), (0, -15)])
        self.assertTrue(all(max(abs(r["dx"]), abs(r["dy"])) == 15 for r in rows))
        self.assertEqual(len({r["id"] for r in rows}), 8)
        self.assertEqual(rows, v.point_perturbations((2588, 1785)))

    def test_validity_rules(self):
        holdouts = [(1000, 1000)]
        ok, reasons = v.validate_perturbed_point((1000, 1100), SIZE, holdouts)
        self.assertTrue(ok, reasons)
        ok, reasons = v.validate_perturbed_point((1000, 1050), SIZE, holdouts)
        self.assertFalse(ok)
        self.assertTrue(all(r.startswith("INVALID_PERTURBATION") for r in reasons))
        ok, _ = v.validate_perturbed_point((2920, 800), SIZE, [])   # 20 px L∞ de la caja de contacto
        self.assertFalse(ok)
        ok, _ = v.validate_perturbed_point((-3, 800), SIZE, [])
        self.assertFalse(ok)
        dark = np.zeros((SIZE[1], SIZE[0]), bool)
        ok, reasons = v.validate_perturbed_point((1000, 1600), SIZE, [], dark=dark)
        self.assertFalse(ok)
        self.assertIn("material oscuro", reasons[0])


class BoxPerturbations(unittest.TestCase):
    def test_three_separate_families(self):
        rows = {r["id"]: r for r in v.box_perturbations(BASE_BOX, SIZE)}
        self.assertEqual(sorted({r["family"] for r in rows.values()}), ["CONTRACT", "EXPAND", "TRANSLATE"])
        self.assertFalse(rows["T+0+15"]["valid"])            # y2 = 2262 sale de la imagen: nunca se recorta
        self.assertIn("INVALID_PERTURBATION", rows["T+0+15"]["reason"])
        self.assertEqual(sum(r["valid"] for r in rows.values()), 5)
        self.assertEqual(rows["E15"]["box"], [2085, 285, 3515, 2247])
        self.assertEqual(rows["E15"]["sides_fixed_at_image_border"], ["y2"])
        self.assertEqual(rows["C15"]["box"], [2115, 315, 3485, 2232])
        self.assertEqual(rows["T-15+0"]["box"], [2085, 300, 3485, 2247])


class SafePoint(unittest.TestCase):
    def setUp(self):
        self.dark = np.zeros((400, 600), bool)
        self.dark[100:261, 300:461] = True            # cuadrado oscuro 161×161, centro (380, 180)
        self.box = (0, 0, 200, 400)                   # «caja de contacto» sintética a la izquierda

    def test_picks_the_deepest_point(self):
        found = v.select_safe_point(self.dark, (250, 50, 550, 350), [], [], contact_box=self.box, grid=1)
        self.assertEqual(found["safe_half"], 80)
        self.assertEqual(found["xy"], [380, 180])      # el centro gana la meseta de la tolerancia

    def test_constraints_exclude_the_centre(self):
        dark = np.zeros((400, 600), bool)
        dark[50:350, 250:590] = True                   # 340×300, centro (420, 200)
        found = v.select_safe_point(dark, (250, 50, 590, 350), [(420, 200)], [], contact_box=self.box, grid=1)
        self.assertIsNotNone(found)
        self.assertGreaterEqual(v.distance(found["xy"], (420, 200)), v.HOLDOUT_DIST_MIN)
        self.assertGreaterEqual(found["safe_half"], v.SAFE_HALF_MIN)

    def test_none_when_material_too_thin(self):
        dark = np.zeros((400, 600), bool)
        dark[190:211, 300:500] = True                 # franja de 21 px: semilado 10 < 21
        self.assertIsNone(v.select_safe_point(dark, (250, 50, 550, 350), [], [], contact_box=self.box, grid=1))

    def test_box_margin(self):
        self.assertLessEqual(v.box_margin((2500, 800), v.CONTACT_BOX), 0)
        self.assertEqual(v.box_margin((2940, 800), v.CONTACT_BOX), 41)   # x2 = 2900 semiabierta: último píxel 2899
        self.assertEqual(v.box_margin((2500, 1340), v.CONTACT_BOX), 41)


class Ownership(unittest.TestCase):
    def test_labels(self):
        box = (0, 0, 100, 100)
        t = np.zeros((100, 100), bool)
        r = np.zeros((100, 100), bool)
        t[:, :50] = True
        r[:, 50:] = True
        self.assertEqual(v.ownership(t, r, box)["label"], "DISJOINT")
        r[:, 45:] = True                               # 500 px compartidos / 5000 = 0,10
        self.assertEqual(v.ownership(t, r, box)["label"], "SHARED")
        r[:] = False
        r[:, 49:] = True                               # 100 / 5000 = 0,02 → DISJOINT (≤)
        self.assertEqual(v.ownership(t, r, box)["label"], "DISJOINT")
        r[:, 48:] = True                               # 0,04
        self.assertEqual(v.ownership(t, r, box)["label"], "MARGINAL")
        self.assertEqual(v.ownership(t, np.zeros_like(t), box)["label"], "NOT_EVALUABLE")

    def test_interpretation_table(self):
        f = v.interpret_reciprocal
        self.assertEqual(f(True, "UNSTABLE", "SHARED", True), "NO_INFERENCE")
        self.assertEqual(f(True, "STABLE", "SHARED", True), "OWNERSHIP_AMBIGUOUS")
        self.assertEqual(f(True, "STABLE", "DISJOINT", False), "BUN_ATTRIBUTED_TO_TARGET_BY_BOTH")
        self.assertEqual(f(False, "STABLE", "DISJOINT", True), "SEPARATION_CONSISTENT_BOTH_WAYS")
        self.assertEqual(f(False, "STABLE", "SHARED", True), "MIXED")


class Stability(unittest.TestCase):
    def setUp(self):
        self.base = np.zeros((200, 200), bool)
        self.base[50:150, 50:150] = True
        self.o = [("O2", (180, 20))]

    def test_stable_unstable_conflict_not_evaluable(self):
        shifted = np.roll(self.base, 2, axis=1)
        self.assertEqual(v.perturbation_stability(self.base, [("a", shifted)], self.o, (0, 0, 200, 200))["label"], "STABLE")
        half = self.base.copy()
        half[:, 100:] = False
        self.assertEqual(v.perturbation_stability(self.base, [("a", half)], self.o, (0, 0, 200, 200))["label"], "UNSTABLE")
        leak = self.base.copy()
        leak[10:30, 170:190] = True                    # cubre el parche de O2 → cambia el cribado
        out = v.perturbation_stability(self.base, [("a", shifted), ("b", leak)], self.o, (0, 0, 200, 200))
        self.assertEqual(out["label"], "CONFLICT")
        self.assertEqual(out["o_flip"], ["b"])
        self.assertEqual(v.perturbation_stability(self.base, [], self.o)["label"], "NOT_EVALUABLE")
        self.assertEqual(v.worst(["STABLE", "UNSTABLE", "NOT_EVALUABLE"]), "UNSTABLE")
        self.assertEqual(v.worst(["NOT_EVALUABLE"]), "NOT_EVALUABLE")


class Holes(unittest.TestCase):
    def test_enclosed_holes_area_and_bbox(self):
        m = np.ones((60, 80), bool)
        m[10:20, 30:45] = False                        # agujero cerrado 10×15 = 150 px
        m[0:5, 0:5] = False                            # toca el borde: no es agujero
        holes = enclosed_holes(m)
        self.assertEqual(len(holes), 1)
        self.assertEqual(holes[0]["area"], 150)
        self.assertEqual(holes[0]["bbox"], (30, 10, 45, 20))
        self.assertEqual(enclosed_holes(m, min_area=151), [])

    def test_components_match_the_audit_implementation(self):
        rng = np.random.default_rng(7)
        m = rng.random((70, 90)) > 0.55
        ours = sorted((c["area"], c["touches_border"]) for c in components(m))
        theirs = sorted(run_components(m))
        self.assertEqual(ours, theirs)
        self.assertEqual(sum(c["area"] for c in components(m)), int(m.sum()))


class Preregistration(unittest.TestCase):
    """Invariantes del prerregistro versionado que se comprueban sin la foto."""

    @classmethod
    def setUpClass(cls):
        cls.p = json.loads(PREREG.read_text(encoding="utf-8"))

    def test_content_hash(self):
        body = {k: val for k, val in self.p.items() if k != "content_sha256"}
        digest = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(digest, self.p["content_sha256"])

    def test_protocol_v2_is_the_frozen_one(self):
        path = ROOT / self.p["blind_audit"]["protocol"]
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), self.p["blind_audit"]["protocol_sha256"])

    def test_new_prompts_respect_every_distance(self):
        holdouts = [h["xy"] for g in self.p["base_config"]["holdouts"].values() for h in g]
        prompts = [q["xy"] for q in self.p["base_config"]["prompts"]]
        new = self.p["new_prompts"]
        self.assertEqual(sorted(new), ["H1", "S1"])
        for pid, info in new.items():
            self.assertGreaterEqual(v.box_margin(info["xy"], v.CONTACT_BOX), v.CONTACT_MARGIN_MIN, pid)
            self.assertGreaterEqual(min(v.distance(info["xy"], h) for h in holdouts), v.HOLDOUT_DIST_MIN, pid)
            others = prompts + [o["xy"] for k, o in new.items() if k != pid]
            self.assertGreaterEqual(min(v.distance(info["xy"], q) for q in others), v.PROMPT_DIST_MIN, pid)
            self.assertGreaterEqual(info["safe_square_half_px"], v.SAFE_HALF_MIN, pid)
            self.assertGreaterEqual(info["safe_square_dark_fraction"], v.DARK_FRACTION_MIN, pid)
            x1, y1, x2, y2 = info["declared_window_xyxy"]
            self.assertTrue(x1 <= info["xy"][0] < x2 and y1 <= info["xy"][1] < y2, pid)
            for key in ("owner_expected", "patch_luma_mean", "patch_luma_std", "image_sha256",
                        "frontier_distance_lower_bound_px"):
                self.assertIn(key, info)

    def test_perturbations_as_declared(self):
        holdouts = [h["xy"] for g in self.p["base_config"]["holdouts"].values() for h in g]
        targets = self.p["branches"]["PERTURB_POINT"]["targets"]
        for name, block in targets.items():
            expected = v.point_perturbations(block["base_xy"])
            self.assertEqual([r["xy"] for r in block["perturbations"]], [r["xy"] for r in expected], name)
            for row in block["perturbations"]:
                if row["valid"]:
                    self.assertGreaterEqual(min(v.distance(row["xy"], h) for h in holdouts), v.PERTURBED_HOLDOUT_DIST_MIN)
                    self.assertGreaterEqual(v.box_margin(row["xy"], v.CONTACT_BOX), v.PERTURBED_CONTACT_MARGIN_MIN)
        boxes = self.p["branches"]["PERTURB_BOX"]["perturbations"]
        self.assertEqual(boxes, v.box_perturbations(self.p["base_config"]["BOX"], SIZE))

    def test_counts_and_prohibitions(self):
        c = self.p["candidate_counts"]
        self.assertEqual(c["total_masks"], c["BASE"] + c["+POS"] + c["RECIPROCAL"] + c["PERTURB_POINT"] + c["PERTURB_BOX"])
        self.assertEqual(c["+POS"], 3 * 2 * 3)
        self.assertFalse(self.p["decision"]["sam2_rejectable"])
        self.assertTrue(any("objetivo − posterior" in f for f in self.p["forbidden"]))
        self.assertIn("NINGUNA", self.p["combination"])
        # Las ramas +POS cambian solo la llamada de corrección: mismos negativos y semillas de BASE.
        base_pc = self.p["branches"]["BASE"]["protocols"]["point+corrections:s{0,1,2}"]
        for branch in ("+POS_HAIR", "+POS_SLEEVE", "+POS_HAIR+SLEEVE"):
            pc = self.p["branches"][branch]["protocols"]["point+corrections:s{0,1,2}"]
            self.assertEqual([q for q, lab in zip(pc["points"], pc["labels"]) if lab == 0],
                             [q for q, lab in zip(base_pc["points"], base_pc["labels"]) if lab == 0])
            self.assertEqual(pc["points"][0], "P+1")


class DoubleKeyRecord(unittest.TestCase):
    def test_record_matches_both_keys(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("double_key_aem1", ROOT / "work" / "double_key_aem1.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        run = ROOT / "auditoria" / "aem1_20260925T062504Z_256dba9f"
        first = json.loads((run / "juicios_crudos.json").read_text(encoding="utf-8"))
        second = json.loads((run / "segunda_llave_chatgpt.json").read_text(encoding="utf-8"))
        record = json.loads((run / "doble_llave.json").read_text(encoding="utf-8"))
        again = module.compare(first, second)
        self.assertEqual(again["cells"], record["cells"])
        self.assertEqual(record["agreement"]["cells_agree"], 42)
        self.assertTrue(record["verdict_agree"])
        self.assertEqual(record["passing"], {"claude": [], "chatgpt": []})
        self.assertFalse(any(d["verdict_relevant"] for d in record["disagreements"]))
        self.assertEqual(record["adjudication_post_unblinding"]["passing"], [])
        self.assertEqual(hashlib.sha256((run / "juicios_crudos.json").read_bytes()).hexdigest(),
                         "e8286d21e54846346ea1e070cb5675ed04af28a80730b49ea6f418ea4b842673")


if __name__ == "__main__":
    unittest.main()
