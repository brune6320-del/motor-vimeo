"""A-E(−1) v1.3: plan de llamadas, auditoría (paquete ciego, consenso, hipótesis) y contratos congelados."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from pragma_ae import aem1_v13 as v
from pragma_ae import aem1_v13_audit as audit

ROOT = Path(__file__).resolve().parents[1]
PREREG = json.loads((ROOT / "aem1" / "PRERREGISTRO_A-E-menos-1_v1_3.json").read_text(encoding="utf-8"))
BASE_REF_PATH = ROOT / "auditoria" / "aem1_20260925T062504Z_256dba9f" / "BASE_V2_REFERENCE.json"
BASE_REF = json.loads(BASE_REF_PATH.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class CallPlan(unittest.TestCase):
    def setUp(self):
        self.plan = PREREG["call_plan"]
        self.by_id = {c["call_id"]: c for c in self.plan}

    def test_plan_is_rebuilt_exactly_from_the_prereg_inputs(self):
        prompts = {q["id"]: q["xy"] for q in PREREG["base_config"]["prompts"]}
        new = {k: n["xy"] for k, n in PREREG["new_prompts"].items()}
        perturb = {k: t["perturbations"] for k, t in PREREG["branches"]["PERTURB_POINT"]["targets"].items()}
        again = v.build_call_plan(prompts, new, PREREG["base_config"]["BOX"], perturb,
                                  PREREG["branches"]["PERTURB_BOX"]["perturbations"])
        self.assertEqual(again, self.plan)

    def test_counts(self):
        c = PREREG["candidate_counts"]
        self.assertEqual(len(self.plan), c["calls"])
        self.assertEqual(len(audit.candidates_of(self.plan)), c["total_masks"])
        self.assertEqual(sum(audit.is_png_candidate(x) for x in audit.candidates_of(self.plan)), 36)
        self.assertEqual(len(set(audit.candidates_of(self.plan))), c["total_masks"])

    def test_base_replicates_v1_2(self):
        self.assertEqual(self.by_id["BASE|point"]["points"], [[2588, 1785]])
        self.assertTrue(self.by_id["BASE|point"]["multimask_output"])
        self.assertEqual(self.by_id["BASE|box"]["box"], [2100, 300, 3500, 2247])
        pc = self.by_id["BASE|point+corrections|s1"]
        self.assertEqual(pc["point_ids"], ["P+1", "P-1", "P-2", "P-3"])
        self.assertEqual(pc["labels"], [1, 0, 0, 0])
        self.assertEqual(pc["mask_input_from"], {"call_id": "BASE|point", "index": 1})
        self.assertFalse(pc["multimask_output"])
        self.assertIsNone(pc["box"])
        self.assertEqual(self.by_id["BASE|box+corrections|s2"]["mask_input_from"], {"call_id": "BASE|box", "index": 2})

    def test_pos_branches_change_only_the_added_positive(self):
        for branch, extra in (("+POS_HAIR", ["H1"]), ("+POS_SLEEVE", ["S1"]), ("+POS_HAIR+SLEEVE", ["H1", "S1"])):
            for protocol in ("point+corrections", "box+corrections"):
                for k in range(3):
                    pos = self.by_id[f"{branch}|{protocol}|s{k}"]
                    base = self.by_id[f"BASE|{protocol}|s{k}"]
                    self.assertEqual(pos["mask_input_from"], base["mask_input_from"])      # semilla de BASE
                    self.assertEqual(pos["box"], base["box"])
                    self.assertEqual(pos["point_ids"], ["P+1"] + extra + ["P-1", "P-2", "P-3"])
                    self.assertEqual(pos["labels"], [1] * (1 + len(extra)) + [0, 0, 0])

    def test_reciprocal_and_perturbations(self):
        r = self.by_id["RECIPROCAL|R-corrections|s0"]
        self.assertEqual(r["point_ids"], ["P-1", "P-2", "P-3", "P+1", "H1", "S1"])
        self.assertEqual(r["labels"], [1, 1, 1, 0, 0, 0])
        chain = self.by_id["PERTURB_POINT|P+1|d+0+15|point+corrections|s1"]
        self.assertEqual(chain["mask_input_from"], {"call_id": "PERTURB_POINT|P+1|d+0+15|point", "index": 1})
        self.assertEqual(chain["points"][0], [2588, 1800])
        h = self.by_id["PERTURB_POINT|H1|d-15+15|box+corrections|s0"]
        self.assertEqual(h["points"][1], [3057, 607])
        self.assertEqual(h["points"][2], PREREG["new_prompts"]["S1"]["xy"])     # S1 fijo
        self.assertEqual(h["mask_input_from"], {"call_id": "BASE|box", "index": 0})
        self.assertNotIn("PERTURB_BOX|T+0+15|box", self.by_id)                   # INVALID_PERTURBATION no se ejecuta
        self.assertEqual(self.by_id["PERTURB_BOX|E15|box"]["box"], [2085, 285, 3515, 2247])

    def test_every_prompt_has_a_registered_luma(self):
        registered = {tuple(q["xy"]) for q in PREREG["base_config"]["prompts"]}
        registered |= {tuple(n["xy"]) for n in PREREG["new_prompts"].values()}
        registered |= {tuple(r["xy"]) for t in PREREG["branches"]["PERTURB_POINT"]["targets"].values() for r in t["perturbations"]}
        used = {tuple(p) for c in self.plan for p in c["points"]}
        self.assertLessEqual(used, registered)
        v12 = {"P+1": 249.3, "P-1": 125.6, "P-2": 56.8, "P-3": 90.9}          # preflight v1.2
        for q in PREREG["base_config"]["prompts"]:
            self.assertAlmostEqual(q["patch_luma_mean"], v12[q["id"]], delta=0.05)

    def test_perturbation_naming(self):
        rows = PREREG["branches"]["PERTURB_POINT"]["targets"]["P+1"]["perturbations"]
        self.assertTrue(all(r["linf_px"] == 15 for r in rows))
        self.assertEqual(sorted({r["euclidean_px"] for r in rows}), [15.0, 21.21])


class FrozenContracts(unittest.TestCase):
    def test_prereg_freezes_the_analysis_code_and_its_references(self):
        for path, digest in PREREG["analysis_implementation_sha256"].items():
            self.assertEqual(sha(ROOT / path), digest, f"{path} cambió después del prerregistro")
        ref = PREREG["branches"]["BASE"]["reproduction_check"]["reference"]
        self.assertEqual(sha(ROOT / ref["file"]), ref["sha256"])
        self.assertEqual(PREREG["status"], "PREREGISTERED")
        self.assertIn("GO_TO_BUILD", PREREG["cross_audit"]["result"])
        self.assertEqual({h["id"] for h in PREREG["hypotheses"]}, {"H-C1", "H-C2", "H-G1", "H-G2", "H-G3", "H-G4"})

    def test_base_v2_reference(self):
        self.assertEqual(BASE_REF["kind"], "REFERENCIA_NORMALIZADA_ADJUDICADA")
        self.assertEqual(len(BASE_REF["candidates"]), 12)
        self.assertEqual({n["label"] for n in BASE_REF["normalizations"]}, {"B", "D"})
        self.assertTrue(all(n["v2"] == "TRUE" and n["share_inside_A"] > 0.5 for n in BASE_REF["normalizations"]))
        self.assertEqual(BASE_REF["passing"], [])
        table = json.loads((ROOT / "auditoria" / "aem1_20260925T062504Z_256dba9f" / "aem1_tabla_desciegada.json").read_text())
        hashes = {row["packed_mask_sha256"] for row in table["candidates"]}
        self.assertEqual({c["packed_mask_sha256"] for c in BASE_REF["candidates"].values()}, hashes)
        self.assertEqual(BASE_REF["candidates"]["BASE|box|1"]["criteria"]["body_and_edges_complete"], "FALSE")   # F medido

    def test_ae1_contract_binds_the_inspected_sweep(self):
        contract = json.loads((ROOT / "ae1" / "CONTRATO_ANALISIS_A-E1.json").read_text(encoding="utf-8"))
        self.assertEqual(sha(ROOT / contract["sweep"]["file"]), contract["sweep"]["sha256"])
        self.assertEqual(contract["full_experiment"], "NOT_YET_FULLY_PREREGISTERED")
        self.assertIn("REQUIRED", contract["gates"]["A_E0_FROZEN"])


class BlindSheet(unittest.TestCase):
    def test_holes_are_measured_numbered_and_drawn(self):
        mask = np.zeros((2248, 4000), bool)
        mask[400:1800, 2300:3300] = True
        mask[600:660, 2500:2560] = False            # 3600 px
        mask[1200:1240, 2900:2940] = False          # 1600 px
        mask[1500:1510, 2600:2610] = False          # 100 px: por debajo del umbral
        holes = audit.holes_with_masks(mask)
        self.assertEqual([(h["number"], h["area"]) for h in holes], [(1, 3600), (2, 1600)])
        self.assertTrue(all(int(h["mask"].sum()) == h["area"] for h in holes))
        photo = np.full((2248, 4000, 3), 128, np.uint8)
        with tempfile.TemporaryDirectory() as tmp:
            listed = audit.blind_sheet(photo, mask, "C01", Path(tmp) / "c.png")
            self.assertTrue((Path(tmp) / "c.png").stat().st_size > 0)
        self.assertEqual([h["number"] for h in listed], [1, 2])


class Consensus(unittest.TestCase):
    def row(self, **over):
        base = {c: "TRUE" for c in audit.CRITERIA + audit.AUX}
        base.update(over)
        return base

    def test_reconcile_never_raises_a_criterion(self):
        screen = {"missed_keep": ["K2"], "leaked_other_person": [], "leaked_background": []}
        values, notes = audit.reconcile(self.row(), screen, {"1": "L"})
        self.assertEqual(values["body_and_edges_complete"], "FALSE")
        values, _ = audit.reconcile(self.row(other_person_excluded="FALSE"), {**screen, "missed_keep": []}, {"1": "D"})
        self.assertEqual(values["body_and_edges_complete"], "FALSE")
        self.assertEqual(values["other_person_excluded"], "FALSE")

    def test_discrepancy_needs_technical_adjudication(self):
        first = {"x": self.row()}
        second = {"x": self.row(background_excluded="FALSE")}
        values, pending = audit.consensus(first, second, {})
        self.assertEqual(pending, [("x", "background_excluded")])
        self.assertEqual(values["x"]["background_excluded"], "PENDING_ADJUDICATION")
        values, pending = audit.consensus(first, second, {("x", "background_excluded"): {"value": "FALSE"}})
        self.assertEqual((pending, values["x"]["background_excluded"]), ([], "FALSE"))


class Hypotheses(unittest.TestCase):
    def keys(self, branch, **fields):
        cands = [f"{branch}|{p}|s{k}" for p in ("point+corrections", "box+corrections") for k in range(3)]
        rows = {c: dict(fields) for c in cands}
        return {"claude": rows, "chatgpt": {c: dict(r) for c, r in rows.items()}}, cands

    def test_h_c1(self):
        judgments, cands = self.keys("+POS_HAIR", target_hair_included="TRUE", other_person_excluded="FALSE")
        self.assertEqual(v.hypothesis_h_c1(judgments, {c: False for c in cands}), "HOLDS")
        judgments, cands = self.keys("+POS_HAIR", target_hair_included="TRUE", other_person_excluded="TRUE")
        self.assertEqual(v.hypothesis_h_c1(judgments, {c: False for c in cands}), "REFUTED")
        self.assertEqual(v.hypothesis_h_c1(judgments, {c: True for c in cands}), "HOLDS")   # la fuga O2/O3 cuenta

    def test_h_c2_and_h_g2(self):
        self.assertEqual(v.hypothesis_h_c2(["STABLE", "UNSTABLE", "STABLE"]), "HOLDS")
        self.assertEqual(v.hypothesis_h_c2(["STABLE"] * 3), "REFUTED")
        self.assertEqual(v.hypothesis_h_c2(["STABLE", "NOT_EVALUABLE", "STABLE"]), "INDETERMINATE")
        self.assertEqual([v.hypothesis_h_g2(x) for x in ("STABLE", "UNSTABLE", "CONFLICT", "NOT_EVALUABLE")],
                         ["HOLDS", "HOLDS", "REFUTED", "INDETERMINATE"])

    def test_h_g1(self):
        judgments, cands = self.keys("+POS_SLEEVE", target_dark_sleeves_included="TRUE")
        base = {c.replace("+POS_SLEEVE", "BASE"): {"other_person_excluded": "TRUE"} for c in cands}
        consensus = {c: {"other_person_excluded": "TRUE"} for c in cands}
        self.assertEqual(v.hypothesis_h_g1(judgments, consensus, base), "HOLDS")
        consensus = {c: {"other_person_excluded": "FALSE"} for c in cands}
        self.assertEqual(v.hypothesis_h_g1(judgments, consensus, base), "REFUTED")      # 6 empeoran
        consensus = {c: {"other_person_excluded": "FALSE" if i < 3 else "TRUE"} for i, c in enumerate(cands)}
        self.assertEqual(v.hypothesis_h_g1(judgments, consensus, base), "INDETERMINATE")  # 3 empeoran

    def test_h_g3_and_h_g4(self):
        leaks = {"a": True, "b": False}
        self.assertEqual(v.hypothesis_h_g3("STABLE", True, leaks, {"a": "SHARED", "b": "DISJOINT"}), "HOLDS")
        self.assertEqual(v.hypothesis_h_g3("STABLE", True, leaks, {"a": "DISJOINT", "b": "SHARED"}), "REFUTED")
        self.assertEqual(v.hypothesis_h_g3("NOT_EVALUABLE", True, leaks, {"a": "SHARED", "b": "SHARED"}), "INDETERMINATE")
        self.assertEqual(v.hypothesis_h_g3("STABLE", True, {"a": False}, {"a": "DISJOINT"}), "INDETERMINATE")
        judgments, _ = self.keys("+POS_HAIR+SLEEVE", target_hair_included="TRUE", target_dark_sleeves_included="FALSE")
        self.assertEqual(v.hypothesis_h_g4(judgments), "REFUTED")
        judgments["claude"]["+POS_HAIR+SLEEVE|box+corrections|s2"]["target_dark_sleeves_included"] = "TRUE"
        self.assertEqual(v.hypothesis_h_g4(judgments), "REFUTED")                     # falta la otra llave
        judgments["chatgpt"]["+POS_HAIR+SLEEVE|box+corrections|s2"]["target_dark_sleeves_included"] = "TRUE"
        self.assertEqual(v.hypothesis_h_g4(judgments), "HOLDS")


class ReciprocalAndContinuous(unittest.TestCase):
    def test_reciprocal_stability_and_reference(self):
        box = (0, 0, 100, 100)
        a = np.zeros((100, 100), bool)
        a[20:80, 20:80] = True
        seeds = [("s0", a), ("s1", a.copy()), ("s2", np.roll(a, 30, axis=1))]
        out = v.reciprocal_stability(seeds, [("K1", (95, 50))], box)
        self.assertEqual(out["label"], "CONFLICT")      # s2 cubre K1 y las otras no
        out = v.reciprocal_stability(seeds[:2], [("K1", (95, 50))], box)
        self.assertEqual(out["label"], "STABLE")
        empty = [("s0", a), ("s1", np.zeros_like(a))]
        self.assertEqual(v.reciprocal_stability(empty, [], box)["label"], "NOT_EVALUABLE")
        self.assertEqual(v.reference_mask(seeds, [("O1", (90, 50)), ("O2", (60, 50))]), "s2")

    def test_conflict_records_continuous_margin(self):
        base = np.zeros((100, 100), bool)
        near = base.copy()
        near[44:48, 44:57] = True                         # cubre ~0,31 del parche 13×13 de O
        out = v.perturbation_stability(base, [("p", near)], [("O2", (50, 50))], (0, 0, 100, 100))
        self.assertEqual(out["label"], "CONFLICT")
        detail = out["o_flip_detail"][0]
        self.assertEqual(detail["sentinel"], "O2")
        self.assertAlmostEqual(detail["distance_to_threshold"], min(abs(0 - 0.2), abs(detail["perturbed"] - 0.2)), places=4)

    def test_ownership_directional_ratios(self):
        t = np.zeros((100, 100), bool)
        r = np.zeros((100, 100), bool)
        t[:, :10] = True                                  # T pequeña casi contenida en R enorme
        r[:, :90] = True
        out = v.ownership(t, r, (0, 0, 100, 100))
        self.assertEqual(out["label"], "SHARED")
        self.assertEqual(out["shared_over_target"], 1.0)
        self.assertLess(out["shared_over_reciprocal"], 0.2)


if __name__ == "__main__":
    unittest.main()
