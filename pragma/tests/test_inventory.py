import copy
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from pragma_ae import EXPECTED_IMAGE_SHA256
from pragma_ae import inventory as inv
from pragma_ae.masks import packed_sha256

ROOT = Path(__file__).resolve().parents[1]
W, H = 4000, 2248


def obj(i, **kw):
    base = {"id": f"ae0_{i:03d}", "canonical_name": f"objeto {i}", "synonyms": [], "concept_en": "thing",
            "kind": "instance", "tier": "A", "bbox": [100, 100, 400, 400], "bbox_source": "test",
            "occlusion": "none", "truncation": "none", "parent_id": None, "occluded_by": [],
            "gt_required": False, "gt_mask": None, "ignore_reason": None, "review": [], "notes": ""}
    base.update(kw)
    return base


def document(objects, status="HUMAN_REVIEWED", ratified=True):
    return {"schema": inv.SCHEMA, "schema_version": inv.SCHEMA_VERSION, "status": status,
            "image": {"sha256": EXPECTED_IMAGE_SHA256, "width": W, "height": H},
            "ontology": {"ratified": ratified, "min_short_side_px": 32, "tier_a_min_short_side_px": 64},
            "objects": objects}


class InventoryContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        mask = np.zeros((H, W), bool)
        mask[200:1200, 500:900] = True
        Image.fromarray(mask.astype(np.uint8) * 255).save(self.dir / "persona.png")
        self.mask_entry = {"path": "persona.png", "mask_sha256": packed_sha256(mask)}

    def tearDown(self):
        self.tmp.cleanup()

    def person(self, **kw):
        return obj(1, concept_en="person", canonical_name="persona", bbox=[480, 180, 920, 1220],
                   gt_required=True, gt_mask=copy.deepcopy(self.mask_entry), **kw)

    def test_committed_draft_is_valid_draft(self):
        path = ROOT / "ae0" / "scene_inventory.draft.json"
        result = inv.validate(inv.load(path), path.parent)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["state"], "A_E0_DRAFT")
        self.assertFalse(result["evaluation_allowed"])
        people = [o for o in inv.load(path)["objects"] if o["concept_en"] == "person"]
        self.assertEqual(len(people), 3)
        self.assertTrue(all(p["tier"] == "A" and p["gt_required"] for p in people))

    def test_person_must_be_tier_a_with_gt(self):
        doc = document([obj(1, concept_en="person", tier="B")])
        errors = inv.validate(doc, self.dir)["errors"]
        self.assertTrue(any("Tier A" in e for e in errors))
        self.assertTrue(any("gt_required" in e for e in errors))

    def test_structural_errors(self):
        doc = document([
            obj(1, bbox=[10, 10, 5, 50]),
            obj(2, parent_id="ae0_999"),
            obj(3, occluded_by=["ae0_003"]),
            obj(4, tier="IGNORE"),
            obj(5, kind="part"),
        ])
        errors = " | ".join(inv.validate(doc, self.dir)["errors"])
        for fragment in ("fuera de la imagen", "no existe", "a sí mismo", "ignore_reason", "kind=part"):
            self.assertIn(fragment, errors)

    def test_parent_cycle_detected(self):
        doc = document([obj(1, parent_id="ae0_002", kind="part", tier="C"),
                        obj(2, parent_id="ae0_001", kind="part", tier="C")])
        self.assertTrue(any("ciclo" in e for e in inv.validate(doc, self.dir)["errors"]))

    def test_state_ladder_and_freeze(self):
        doc = document([self.person()], ratified=False)
        self.assertEqual(inv.validate(doc, self.dir)["state"], "A_E0_PENDING_RATIFICATION")
        doc["ontology"]["ratified"] = True
        doc["objects"][0]["review"] = ["bbox"]
        self.assertEqual(inv.validate(doc, self.dir)["state"], "A_E0_PENDING_REVIEW_ITEMS")
        doc["objects"][0]["review"] = []
        missing = copy.deepcopy(doc)
        missing["objects"][0]["gt_mask"] = None
        self.assertEqual(inv.validate(missing, self.dir)["state"], "A_E0_PENDING_GT")
        self.assertEqual(inv.validate(doc, self.dir)["state"], "A_E0_READY_TO_FREEZE")

        with self.assertRaises(ValueError):
            inv.freeze(doc, self.dir, frozen_by="  ")
        frozen = inv.freeze(doc, self.dir, frozen_by="revisora")
        result = inv.validate(frozen, self.dir)
        self.assertEqual(result["state"], "A_E0_FROZEN")
        self.assertTrue(result["evaluation_allowed"])

        tampered = copy.deepcopy(frozen)
        tampered["objects"][0]["bbox"][0] += 1
        self.assertEqual(inv.validate(tampered, self.dir)["state"], "A_E0_INVALID")

    def test_gt_hash_and_extent_are_enforced(self):
        wrong_hash = self.person()
        wrong_hash["gt_mask"]["mask_sha256"] = "0" * 64
        self.assertTrue(any("mask_sha256" in e for e in inv.validate(document([wrong_hash]), self.dir)["errors"]))
        outside = self.person()
        outside["bbox"] = [480, 180, 700, 700]
        self.assertTrue(any("se sale" in e for e in inv.validate(document([outside]), self.dir)["errors"]))

    def test_draft_cannot_freeze(self):
        doc = document([self.person()], status="DRAFT_UNVERIFIED")
        with self.assertRaises(ValueError):
            inv.freeze(doc, self.dir, frozen_by="x")

    def test_canonical_hash_ignores_key_order(self):
        doc = document([self.person()])
        shuffled = json.loads(json.dumps(doc, sort_keys=True))
        self.assertEqual(inv.content_sha256(doc), inv.content_sha256(shuffled))


if __name__ == "__main__":
    unittest.main()
