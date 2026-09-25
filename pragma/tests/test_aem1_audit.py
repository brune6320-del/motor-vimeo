import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

from pragma_ae import EXPECTED_IMAGE_SHA256
from pragma_ae.aem1_audit import _patch_coverage, audit_zip, packed_mask_sha256, run_components, write_verdict

W, H = 4000, 2248
CRITERIA_TRUE = {"correct_subject": True, "body_and_edges_complete": True,
                 "other_person_excluded": True, "background_excluded": True}


def _sha(data):
    import hashlib
    return hashlib.sha256(data).hexdigest()


def synthetic_bundle(path, sam2_commit="abc123", checkpoint_bytes=898_083_611, device="cuda"):
    """ZIP con el mismo formato que exporta la celda 10 del cuaderno (una propuesta, una candidata)."""
    mask = np.zeros((H, W), bool)
    mask[430:2248, 2150:3420] = True
    mask[300:430, 2636:2790] = False
    config = {
        "config_revision": "1.2", "patch_radius": 6, "keep_min_coverage": 0.8, "drop_max_coverage": 0.2,
        "holdout_keep_subject": [{"sentinel_id": "K1", "xy": [2835, 635]}],
        "holdout_drop_other_person": [{"sentinel_id": "O2", "xy": [2700, 380]}],
        "holdout_drop_background": [{"sentinel_id": "B2", "xy": [1735, 1635]}],
    }
    digest = _sha(json.dumps(config, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    coverage = {"keep_subject": {"K1": _patch_coverage(mask, (2835, 635), 6)},
                "drop_other_person": {"O2": _patch_coverage(mask, (2700, 380), 6)},
                "drop_background": {"B2": _patch_coverage(mask, (1735, 1635), 6)}}
    buffer = io.BytesIO()
    Image.fromarray(mask.astype(np.uint8) * 255).save(buffer, format="PNG")
    files = {
        "aem1_box_x_c0_alpha.png": buffer.getvalue(),
        "aem1_config.json": json.dumps({"config_digest": digest, "config": config}).encode(),
        "aem1_report.json": json.dumps({
            "run_id": "TEST", "case_status": "PENDING_EXTERNAL_AUDIT", "project_status": "INCONCLUSIVE_A_E0_REQUIRED",
            "phase_b_blocked": True, "sam2_rejectable": False, "configuration": config,
            "environment": {"image_sha256": EXPECTED_IMAGE_SHA256, "sam2_commit": sam2_commit,
                            "checkpoint_bytes": checkpoint_bytes, "device": device},
            "proposals": {"box": {"protocol": "box", "config_digest": digest, "candidate_scores": [0.9],
                                  "alpha_files": ["aem1_box_x_c0_alpha.png"],
                                  "candidate_metrics": [{"coverage": coverage}]}},
        }).encode(),
    }
    manifest = {"entries": [{"name": n, "bytes": len(b), "sha256": _sha(b)} for n, b in sorted(files.items())]}
    with zipfile.ZipFile(path, "w") as archive:
        for name, blob in files.items():
            archive.writestr(name, blob)
        archive.writestr("aem1_manifest.json", json.dumps(manifest))
    return mask


class Components(unittest.TestCase):
    def test_blobs_and_holes(self):
        m = np.zeros((40, 50), bool)
        m[5:20, 5:20] = True
        m[10:14, 10:14] = False          # un agujero
        m[25:35, 30:45] = True           # segunda componente
        comps = run_components(m)
        self.assertEqual(len(comps), 2)
        holes = [a for a, touches in run_components(~m) if not touches]
        self.assertEqual(holes, [16])

    def test_diagonal_is_not_4_connected(self):
        m = np.zeros((4, 4), bool)
        m[0, 0] = m[1, 1] = True
        self.assertEqual(len(run_components(m)), 2)


class AuditBundle(unittest.TestCase):
    def test_clean_bundle_passes_and_tamper_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ok.zip"
            mask = synthetic_bundle(path)
            result = audit_zip(path)
            self.assertTrue(result["integrity"]["pass"], result["integrity"])
            self.assertEqual(result["run_kind"], "REAL_GPU")
            row = result["candidates"][0]
            self.assertTrue(row["sentinels_match_report"])
            self.assertEqual(row["packed_mask_sha256"], packed_mask_sha256(mask))
            self.assertTrue(row["sentinel_screen_pass"])

            tampered = Path(tmp) / "tampered.zip"
            with zipfile.ZipFile(path) as src, zipfile.ZipFile(tampered, "w") as dst:
                for name in src.namelist():
                    blob = src.read(name)
                    if name == "aem1_report.json":
                        blob = blob.replace(b'"case_status": "PENDING_EXTERNAL_AUDIT"', b'"case_status": "PASS"')
                    dst.writestr(name, blob)
            self.assertFalse(audit_zip(tampered)["integrity"]["pass"])

    def test_simulated_run_is_never_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sim.zip"
            synthetic_bundle(path, sam2_commit="SIMULATED", checkpoint_bytes=41, device="cpu")
            auto = audit_zip(path)
            self.assertEqual(auto["run_kind"], "SIMULATED")
            verdict = write_verdict(auto, "box#0", CRITERIA_TRUE, "", "test", ["prueba"])
            self.assertEqual(verdict["case_status"], "SIMULATED_RUN_NOT_EVIDENCE")

    def test_verdict_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ok.zip"
            synthetic_bundle(path)
            auto = audit_zip(path)
            ok = write_verdict(auto, "box#0", CRITERIA_TRUE, "", "auditor", ["todo en su sitio"])
            self.assertEqual(ok["case_status"], "SEPARATION_DEMONSTRATED_UNDER_FIXED_AEM1_PROTOCOL")
            failing = dict(CRITERIA_TRUE, other_person_excluded=False)
            with self.assertRaises(ValueError):
                write_verdict(auto, "box#0", failing, "", "auditor", [])
            bad = write_verdict(auto, "box#0", failing, "se lleva el pelo recogido", "auditor", [])
            self.assertEqual(bad["case_status"], "INCONCLUSIVE_SELECTED_OUTPUT_FAILED")
            self.assertNotEqual(ok["inspection_token"], bad["inspection_token"])
            with self.assertRaises(ValueError):
                write_verdict(auto, "box#7", CRITERIA_TRUE, "", "auditor", [])


if __name__ == "__main__":
    unittest.main()
