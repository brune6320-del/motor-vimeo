import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "work"))
from validate_ae0_key import check  # noqa: E402

PHOTO = "8f6e3b6f5013265a45c7e89121e3f0a18e3386951e2e75378b28da6d02ec529d"


def person(oid, bbox, tier="A"):
    return {"id": oid, "canonical_name": f"persona {oid}", "synonyms": [], "concept_en": "person", "kind": "instance",
            "tier": tier, "bbox": bbox, "bbox_source": "ai_visual_estimate", "occlusion": "low", "truncation": "low",
            "parent_id": None, "occluded_by": [], "gt_required": True, "gt_mask": None, "ignore_reason": None,
            "review": [], "notes": ""}


BASE = {"schema": "pragma.scene_inventory", "schema_version": "0.1.0", "status": "DRAFT_UNVERIFIED",
        "image": {"sha256": PHOTO, "width": 4000, "height": 2248},
        "ontology": {"version": "0.2", "ratified": False, "document": "RATIFICACION_ONTOLOGIA_v0_2.md",
                     "min_short_side_px": 32, "tier_a_min_short_side_px": 64},
        "key": {"auditor": "prueba", "blind_statement": "sintético", "image_sha256": PHOTO, "ontology": "v0.2",
                "created": "2026-09-26"},
        "objects": [person("ae0_001", [100, 100, 600, 2000])]}


class Ae0Key(unittest.TestCase):
    def run_check(self, data):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "llave.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            return check(path)

    def test_valid_key(self):
        report = self.run_check(BASE)
        self.assertTrue(report["valid_key"], report["errors"])
        self.assertEqual(report["persons"], ["ae0_001"])

    def test_key_block_is_required(self):
        data = copy.deepcopy(BASE); del data["key"]
        self.assertFalse(self.run_check(data)["valid_key"])

    def test_person_must_be_tier_a_and_reviews_closed(self):
        data = copy.deepcopy(BASE)
        data["objects"][0]["tier"] = "B"
        data["objects"][0]["review"] = ["bbox"]
        errors = " ".join(self.run_check(data)["errors"])
        self.assertIn("tier A", errors)
        self.assertIn("review", errors)

    def test_wrong_photo(self):
        data = copy.deepcopy(BASE); data["key"]["image_sha256"] = "0" * 64
        self.assertFalse(self.run_check(data)["valid_key"])


if __name__ == "__main__":
    unittest.main()
