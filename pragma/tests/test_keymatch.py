import unittest

from pragma_ae.keymatch import containment, match_keys


def obj(oid, bbox, name="x", concept="thing", kind="instance", tier="A", occlusion="low", truncation="none",
        parent=None, occluded_by=()):
    return {"id": oid, "canonical_name": name, "concept_en": concept, "kind": kind, "tier": tier, "bbox": list(bbox),
            "occlusion": occlusion, "truncation": truncation, "parent_id": parent, "occluded_by": list(occluded_by)}


class MatchKeys(unittest.TestCase):
    def test_identical_keys_match_fully(self):
        a = [obj("ae0_001", (0, 0, 100, 200), concept="person"), obj("ae0_002", (300, 300, 364, 380))]
        m = match_keys({"objects": a}, {"objects": [dict(o) for o in a]})
        s = m["summary"]
        self.assertEqual((s["matched"], s["a_only"], s["b_only"], s["box_auto"]), (2, 0, 0, 2))
        self.assertEqual(m["matched"][0]["reference_bbox"], [0, 0, 100, 200])
        self.assertEqual(s["pairs_with_disagreements"], 0)

    def test_independent_numbering_is_irrelevant(self):
        a = [obj("ae0_001", (0, 0, 100, 100)), obj("ae0_002", (500, 500, 600, 600))]
        b = [obj("ae0_007", (502, 498, 601, 600)), obj("ae0_003", (1, 0, 100, 101))]
        m = match_keys({"objects": a}, {"objects": b})
        pairs = {(p["a_id"], p["b_id"]) for p in m["matched"]}
        self.assertEqual(pairs, {("ae0_001", "ae0_003"), ("ae0_002", "ae0_007")})

    def test_loose_box_goes_to_adjudication_and_attributes_are_listed(self):
        a = [obj("ae0_001", (0, 0, 100, 100), tier="A", occlusion="low")]
        b = [obj("ae0_001", (0, 0, 100, 150), tier="B", occlusion="high")]
        [p] = match_keys({"objects": a}, {"objects": b})["matched"]
        self.assertEqual(p["box_status"], "BOX_ADJUDICATE")
        self.assertIsNone(p["reference_bbox"])
        self.assertEqual(p["disagreements"], {"tier": ["A", "B"], "occlusion": ["low", "high"]})

    def test_greedy_is_one_to_one_by_descending_iou(self):
        a = [obj("ae0_001", (0, 0, 100, 100)), obj("ae0_002", (10, 0, 110, 100))]
        b = [obj("ae0_009", (10, 0, 110, 100))]
        m = match_keys({"objects": a}, {"objects": b})
        self.assertEqual([(p["a_id"], p["b_id"]) for p in m["matched"]], [("ae0_002", "ae0_009")])
        self.assertEqual([u["id"] for u in m["a_only"]], ["ae0_001"])

    def test_unmatched_person_is_high_priority_and_partition_hint(self):
        a = [obj("ae0_001", (0, 0, 400, 1000), concept="person")]
        b = [obj("ae0_001", (100, 100, 180, 180), concept="hand", kind="part")]
        m = match_keys({"objects": a}, {"objects": b})
        [u] = m["a_only"]
        self.assertEqual(u["priority"], "HIGH_PERSON")
        [v] = m["b_only"]
        self.assertTrue(v["max_containment"]["partition_hint"])
        self.assertEqual(m["summary"]["unmatched_persons"], 1)

    def test_relations_are_translated_through_the_matching(self):
        a = [obj("ae0_001", (0, 0, 400, 1000), concept="person"),
             obj("ae0_002", (100, 100, 180, 180), kind="part", tier="C", parent="ae0_001"),
             obj("ae0_003", (300, 0, 700, 1000), concept="person", occluded_by=["ae0_001"])]
        b = [obj("ae0_010", (0, 0, 400, 1000), concept="person"),
             obj("ae0_011", (100, 100, 180, 180), kind="part", tier="C", parent="ae0_010"),
             obj("ae0_012", (300, 0, 700, 1000), concept="person", occluded_by=[])]
        m = match_keys({"objects": a}, {"objects": b})
        by = {p["a_id"]: p for p in m["matched"]}
        self.assertNotIn("parent_id", by["ae0_002"]["disagreements"])
        self.assertEqual(by["ae0_003"]["disagreements"], {"occluded_by": [["ae0_001"], []]})

    def test_duplicate_ids_rejected(self):
        a = [obj("ae0_001", (0, 0, 10, 10)), obj("ae0_001", (20, 20, 30, 30))]
        with self.assertRaises(ValueError):
            match_keys({"objects": a}, {"objects": []})

    def test_containment(self):
        self.assertEqual(containment((0, 0, 100, 100), (10, 10, 20, 20)), 1.0)
        self.assertEqual(containment((0, 0, 10, 10), (20, 20, 30, 30)), 0.0)


if __name__ == "__main__":
    unittest.main()
