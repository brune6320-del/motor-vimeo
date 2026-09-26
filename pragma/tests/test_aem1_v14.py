"""A-E(−1) v1.4: regla de H2, medidas prerregistradas, hipótesis H-C3/H-G5 y prerregistro congelado."""

import hashlib
import json
import unittest
from pathlib import Path

import numpy as np

from pragma_ae import aem1_v13 as v13
from pragma_ae import aem1_v13_audit as a13
from pragma_ae import aem1_v14 as w
from pragma_ae import aem1_v14_audit as audit

ROOT = Path(__file__).resolve().parents[1]
PREREG_PATH = ROOT / "aem1" / "PRERREGISTRO_A-E-menos-1_v1_4.json"
PREREG = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
PREREG13 = json.loads((ROOT / "aem1" / "PRERREGISTRO_A-E-menos-1_v1_3.json").read_text(encoding="utf-8"))
SHAPE = (2248, 4000)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rect(shape, x1, y1, x2, y2):
    m = np.zeros(shape, bool)
    m[y1:y2, x1:x2] = True
    return m


class H2Rule(unittest.TestCase):
    def test_common_region_is_the_intersection_of_the_unions(self):
        a, b = rect((50, 50), 0, 0, 20, 20), rect((50, 50), 30, 30, 40, 40)
        c = rect((50, 50), 10, 10, 35, 35)
        region = w.common_defect_region({0: [a, b], 1: [c]})
        self.assertEqual(int(region.sum()), 10 * 10 + 5 * 5)
        with self.assertRaises(ValueError):
            w.common_defect_region({0: [a], 1: []})

    def test_point_only_inside_region_and_deepest(self):
        dark = rect((400, 400), 100, 100, 300, 300)
        region = rect((400, 400), 180, 180, 240, 240)
        chosen = w.select_point_in_region(dark, region, holdouts=[], prompts=[], contact_box=(0, 0, 1, 1), min_half=7)
        x, y = chosen["xy"]
        self.assertTrue(region[y, x])
        self.assertEqual((x, y), (200, 200))          # el centro del material oscuro es el cuadrado mayor
        self.assertGreaterEqual(chosen["safe_half"], 99)
        self.assertEqual((x % 2, y % 2), (0, 0))
        off_centre = w.select_point_in_region(dark, rect((400, 400), 250, 250, 290, 290), [], [],
                                              contact_box=(0, 0, 1, 1))
        self.assertTrue(250 <= off_centre["xy"][0] < 290 and 250 <= off_centre["xy"][1] < 290)

    def test_none_when_the_region_is_too_thin_or_too_close(self):
        dark = rect((400, 400), 100, 100, 110, 300)
        region = rect((400, 400), 100, 100, 110, 300)
        self.assertIsNone(w.select_point_in_region(dark, region, [], [], contact_box=(0, 0, 1, 1), min_half=7))
        dark = rect((400, 400), 100, 100, 300, 300)
        near =w.select_point_in_region(dark, dark, holdouts=[(200, 200)], prompts=[], contact_box=(0, 0, 1, 1))
        self.assertGreaterEqual(v13.distance(near["xy"], (200, 200)), v13.HOLDOUT_DIST_MIN)


class Measures(unittest.TestCase):
    def setUp(self):
        self.ref = rect(SHAPE, 1000, 500, 1400, 1100)
        self.ref[700:760, 1150:1200] = False                     # agujero objetivo de 3000 px
        self.target = w.hole_containing(self.ref, (1170, 720))

    def test_target_hole(self):
        self.assertIsNotNone(self.target)
        self.assertEqual(self.target["area"], 3000)
        self.assertIsNone(w.hole_containing(self.ref, (1100, 600)))

    def test_closure(self):
        full = rect(SHAPE, 1000, 500, 1400, 1100)
        self.assertTrue(w.closure(self.target["mask"], full)["closed"])
        partial = full.copy()
        partial[700:760, 1150:1170] = False                      # quedan 1200 px encerrados
        result = w.closure(self.target["mask"], partial)
        self.assertFalse(result["closed"])
        self.assertEqual(result["residual_px"], 1200)
        opened = self.ref.copy()
        opened[700:760, 1150:1400] = False                       # el faltante deja de estar encerrado
        self.assertFalse(w.closure(self.target["mask"], opened)["closed"])
        small = full.copy()
        small[700:720, 1150:1170] = False                        # 400 px: por debajo del umbral
        self.assertTrue(w.closure(self.target["mask"], small)["closed"])

    def region(self):
        return w.h2_region(SHAPE, self.target["mask"], (1170, 720))   # objetivo dilatado: y 685–774, x 1135–1214

    def test_new_holes(self):
        region = self.region()
        moved = rect(SHAPE, 1000, 500, 1400, 1100)
        moved[900:950, 1050:1100] = False                        # pérdida nueva de 2500 px
        found = w.candidate_new_holes(moved, self.ref, region)
        self.assertEqual([(h["area"], h["new_loss_outside_px"]) for h in found], [(2500, 2500)])
        self.assertEqual(found[0]["fraction_inside_reference"], 1.0)
        # Material que ya faltaba (abierto al exterior en la referencia) y ahora queda encerrado: no es nuevo.
        ref_open = rect(SHAPE, 1000, 500, 1400, 1100)
        ref_open[900:950, 1000:1100] = False
        enclosed = rect(SHAPE, 1000, 500, 1400, 1100)
        enclosed[900:950, 1030:1100] = False
        self.assertEqual(w.candidate_new_holes(enclosed, ref_open, region), [])

    # Las cuatro pruebas que pidió ChatGPT 006 antes de regenerar el prerregistro.
    def test_chatgpt006_a_touches_region_by_one_pixel_plus_1500_new_outside_counts(self):
        mask = rect(SHAPE, 1000, 500, 1400, 1100)
        mask[775:805, 1150:1200] = False                          # 1500 px fuera de la región
        mask[774, 1175] = False                                   # 1 px dentro de la región, conectado
        found = w.candidate_new_holes(mask, self.ref, self.region())
        self.assertEqual([(h["area"], h["new_loss_outside_px"], h["touches_region"]) for h in found], [(1501, 1500, True)])

    def test_chatgpt006_b_1200_new_outside_with_only_40_percent_inside_reference_counts(self):
        ref = self.ref.copy()
        ref[900:936, 1030:1080] = False                           # 1800 px que ya faltaban
        mask = rect(SHAPE, 1000, 500, 1400, 1100)
        mask[900:960, 1030:1080] = False                          # agujero de 3000 px: 1200 nuevos
        found = w.candidate_new_holes(mask, ref, self.region())
        self.assertEqual([(h["new_loss_outside_px"], h["fraction_inside_reference"]) for h in found], [(1200, 0.4)])

    def test_chatgpt006_c_only_900_new_outside_does_not_count(self):
        ref = self.ref.copy()
        ref[900:920, 1030:1080] = False                           # 1000 px que ya faltaban
        mask = rect(SHAPE, 1000, 500, 1400, 1100)
        mask[900:938, 1030:1080] = False                          # agujero de 1900 px: 900 nuevos
        self.assertEqual([h["area"] for h in a13.holes_with_masks(mask)], [1900])
        self.assertEqual(w.candidate_new_holes(mask, ref, self.region()), [])

    def test_chatgpt006_d_preexisting_hole_without_new_loss_does_not_count(self):
        ref = self.ref.copy()
        ref[900:936, 1030:1080] = False
        mask = rect(SHAPE, 1000, 500, 1400, 1100)
        mask[900:936, 1030:1080] = False                          # el mismo agujero, sin pérdida nueva
        self.assertEqual(w.candidate_new_holes(mask, ref, self.region()), [])

    def test_hole_touching_region_counts_only_its_loss_outside(self):
        near = rect(SHAPE, 1000, 500, 1400, 1100)
        near[765:780, 1150:1200] = False                          # 500 px dentro y 250 fuera
        near[765:800, 1150:1200] = False                          # ahora 500 dentro y 1250 fuera
        found = w.candidate_new_holes(near, self.ref, self.region())
        self.assertEqual([h["new_loss_outside_px"] for h in found], [1250])
        small = rect(SHAPE, 1000, 500, 1400, 1100)
        small[760:775, 1120:1200] = False                         # 1200 px: 975 dentro de la región y 225 fuera
        self.assertEqual([h["area"] for h in a13.holes_with_masks(small)], [1200])
        self.assertEqual(w.candidate_new_holes(small, self.ref, self.region()), [])

    def test_region_without_target_is_a_square(self):
        region = w.h2_region((100, 100), None, (50, 50))
        self.assertEqual(int(region.sum()), 31 * 31)

    def test_measure_o(self):
        dark = np.zeros(SHAPE, bool)
        m = np.zeros(SHAPE, bool)
        m[350:352, 2650:2653] = True                             # 6 px en el núcleo del moño
        self.assertEqual(w.measure_o(m, dark)["core_px"], 0)     # no cuenta si no es material oscuro
        dark[:] = True
        self.assertEqual(w.measure_o(m, dark)["core_px"], 6)
        self.assertEqual(w.measure_o(m, dark)["o_by_measurement"], "FALSE")
        shoulder = np.zeros(SHAPE, bool)
        shoulder[980:1100, 2400:2520] = True                     # toca la fila inferior: es la chica
        self.assertEqual(w.measure_o(shoulder, dark)["core_px"], 0)
        shoulder[900:905, 2450:2455] = True                      # isla separada: posterior
        self.assertEqual(w.measure_o(shoulder, dark)["shoulder_separate_px"], 25)

    def test_o_worse(self):
        self.assertTrue(w.o_worse("TRUE", "FALSE", 0, 0))
        self.assertFalse(w.o_worse("TRUE", "TRUE", 0, 3))
        self.assertTrue(w.o_worse("FALSE", "FALSE", 5, 6))
        self.assertFalse(w.o_worse("FALSE", "FALSE", 5, 5))


class Hypotheses(unittest.TestCase):
    @staticmethod
    def seeds(*rows):
        keys = ("evaluable", "closed", "o_worse", "new_d")
        return {f"s{i}": dict(zip(keys, row)) for i, row in enumerate(rows)}

    def test_h_c3(self):
        self.assertEqual(w.hypothesis_h_c3(self.seeds((1, 1, 0, 0), (1, 1, 0, 0), (1, 0, 0, 0))), "HOLDS")
        self.assertEqual(w.hypothesis_h_c3(self.seeds((1, 1, 1, 0), (1, 1, 0, 0), (1, 0, 0, 0))), "REFUTED")
        self.assertEqual(w.hypothesis_h_c3(self.seeds((0, 0, 0, 0), (1, 1, 0, 0), (1, 0, 0, 0))), "INDETERMINATE")

    def test_h_g5(self):
        self.assertEqual(w.hypothesis_h_g5(self.seeds((1, 1, 0, 0), (1, 1, 0, 0), (1, 0, 0, 0))), "HOLDS")
        self.assertEqual(w.hypothesis_h_g5(self.seeds((1, 1, 0, 1), (1, 1, 0, 1), (1, 0, 0, 0))), "REFUTED")
        self.assertEqual(w.hypothesis_h_g5(self.seeds((1, 0, 1, 0), (1, 0, 1, 0), (1, 1, 0, 0))), "REFUTED")
        self.assertEqual(w.hypothesis_h_g5(self.seeds((1, 1, 0, 1), (1, 1, 0, 0), (1, 0, 0, 0))), "INDETERMINATE")
        self.assertEqual(w.hypothesis_h_g5(self.seeds((1, 0, 0, 0), (1, 0, 0, 0), (1, 1, 0, 0))), "INDETERMINATE")


class Prereg(unittest.TestCase):
    def test_content_hash_and_status(self):
        body = {k: val for k, val in PREREG.items() if k != "content_sha256"}
        digest = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(digest, PREREG["content_sha256"])
        self.assertEqual(PREREG["status"], "PREREGISTERED")

    def test_analysis_code_is_frozen(self):
        for path, digest in PREREG["analysis_implementation_sha256"].items():
            self.assertEqual(sha(ROOT / path), digest, path)
        for path in ("pragma_ae/aem1_v13.py", "pragma_ae/aem1_v13_audit.py", "pragma_ae/masks.py"):
            self.assertEqual(PREREG["analysis_implementation_sha256"][path], PREREG13["analysis_implementation_sha256"][path])

    def test_plan_is_rebuilt_exactly(self):
        prompts = {q["id"]: q["xy"] for q in PREREG["base_config"]["prompts"]}
        prompts.update({k: n["xy"] for k, n in PREREG["new_prompts"].items()})
        again = w.build_call_plan(prompts, PREREG["base_config"]["BOX"],
                                  PREREG["branches"]["PERTURB_POINT"]["targets"]["H2"]["perturbations"])
        self.assertEqual(again, PREREG["call_plan"])
        counts = PREREG["candidate_counts"]
        self.assertEqual(len(again), counts["calls"])
        self.assertEqual(len(a13.candidates_of(again)), counts["total_masks"])

    def test_reference_calls_equal_v1_3_and_only_h2_is_added(self):
        v13_plan = {c["call_id"]: c for c in PREREG13["call_plan"]}
        for call in PREREG["call_plan"]:
            if call["branch"] in ("BASE", w.REF_BRANCH):
                twin = v13_plan[call["call_id"]]
                for field in ("points", "labels", "box", "mask_input_from", "multimask_output", "candidates"):
                    self.assertEqual(call[field], twin[field], (call["call_id"], field))
            if call["branch"] == w.H2_BRANCH:
                self.assertEqual(call["point_ids"], ["P+1", "H1", "S1", "H2", "P-1", "P-2", "P-3"])

    def test_h2_is_inside_the_common_defect_of_every_reference_seed(self):
        h2 = PREREG["new_prompts"]["H2"]
        self.assertNotEqual(h2["xy"], list(w.UPPER_PROBE))
        for seed, info in h2["inside_target_hole_of_each_reference_seed"].items():
            x1, y1, x2, y2 = info["target_hole"]["bbox"]
            self.assertTrue(x1 <= h2["xy"][0] < x2 and y1 <= h2["xy"][1] < y2, seed)
            self.assertIn(str(info["target_hole"]["number"]), PREREG["reference"]["judgments"][seed]["d_holes"])
        prompts = [q["xy"] for q in PREREG["base_config"]["prompts"]] + [PREREG["new_prompts"][k]["xy"] for k in ("H1", "S1")]
        holdouts = [s["xy"] for g in PREREG["base_config"]["holdouts"].values() for s in g]
        self.assertTrue(all(v13.distance(h2["xy"], p) >= v13.PROMPT_DIST_MIN for p in prompts))
        self.assertTrue(all(v13.distance(h2["xy"], p) >= v13.HOLDOUT_DIST_MIN for p in holdouts))
        self.assertGreaterEqual(v13.box_margin(h2["xy"], v13.CONTACT_BOX), v13.CONTACT_MARGIN_MIN)
        self.assertGreaterEqual(h2["safe_square_half_px"], w.H2_SAFE_HALF_MIN)

    def test_reference_judgments_match_the_closed_v1_3_record(self):
        judgments = PREREG["reference"]["judgments"]
        self.assertEqual([judgments[s]["v1_3_label"] for s in ("s0", "s1", "s2")], ["C03", "C01", "C10"])
        self.assertEqual([judgments[s]["other_person_excluded"] for s in ("s0", "s1", "s2")], ["FALSE", "TRUE", "TRUE"])
        self.assertTrue(all(judgments[s]["body_and_edges_complete"] == "FALSE" for s in judgments))
        self.assertEqual(PREREG["reference"]["v1_3_closure"]["AEM1_v1_3"], "CLOSED_INCONCLUSIVE")

    def test_stop_rule_and_pass_contract(self):
        decision = PREREG["decision"]
        self.assertIn("se cierra con v1.4", decision["stop_rule"])
        self.assertFalse(decision["sam2_rejectable"])
        self.assertEqual(decision["phase_b"], "BLOQUEADA")
        self.assertIn("Cerrar la franja no basta", decision["acceptance"])
        self.assertEqual({h["id"] for h in PREREG["hypotheses"]}, {"H-C3", "H-G5"})

    def test_blind_package_has_the_six_candidates(self):
        self.assertEqual(sorted(audit.blind_ids()),
                         sorted(w.seed_ids(w.REF_BRANCH) + w.seed_ids(w.H2_BRANCH)))
        self.assertTrue(all(audit.is_png_candidate(c) for c in audit.blind_ids()))
        self.assertFalse(audit.is_png_candidate("PERTURB_POINT|H2|d-15+0|box+corrections|s0"))


if __name__ == "__main__":
    unittest.main()
