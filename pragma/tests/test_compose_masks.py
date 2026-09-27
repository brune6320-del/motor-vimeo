import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "work"))
from ae0_compose_masks import exclusive_persons  # noqa: E402


class CrossPersonExclusivity(unittest.TestCase):
    def test_shared_pixels_leave_both_estimates_and_become_uncertain(self):
        a = np.zeros((10, 10), bool); a[2:6, 2:6] = True
        b = np.zeros((10, 10), bool); b[4:8, 4:8] = True
        u = np.zeros((10, 10), bool)
        out = exclusive_persons({"p1": {"estimate": a, "uncertain": u}, "p2": {"estimate": b, "uncertain": u.copy()}})
        shared = a & b
        self.assertEqual(int(shared.sum()), 4)
        for oid in ("p1", "p2"):
            self.assertFalse((out[oid]["estimate"] & shared).any())
            self.assertTrue(out[oid]["uncertain"][shared].all())
            self.assertEqual(out[oid]["shared_px"], 4)
        self.assertEqual(int(out["p1"]["estimate"].sum()), 16 - 4)
        self.assertFalse((out["p1"]["estimate"] & out["p2"]["estimate"]).any())

    def test_disjoint_persons_are_untouched(self):
        a = np.zeros((6, 6), bool); a[0:2, 0:2] = True
        b = np.zeros((6, 6), bool); b[3:5, 3:5] = True
        u = np.zeros((6, 6), bool)
        out = exclusive_persons({"p1": {"estimate": a, "uncertain": u}, "p2": {"estimate": b, "uncertain": u}})
        self.assertTrue(np.array_equal(out["p1"]["estimate"], a))
        self.assertFalse(out["p2"]["uncertain"].any())
        self.assertEqual(out["p1"]["shared_px"], 0)


if __name__ == "__main__":
    unittest.main()


class EvidencePatches(unittest.TestCase):
    def setUp(self):
        from ae0_compose_masks import apply_patch
        self.apply = apply_patch
        self.est = np.zeros((40, 40), bool); self.est[10:30, 10:30] = True
        self.unc = np.zeros((40, 40), bool); self.unc[0:40, 0:20] = True

    def sq(self, x1, y1, x2, y2):
        return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]

    def test_certain_removes_uncertainty_but_keeps_estimate_and_boundary_band(self):
        est, unc, n = self.apply(self.est, self.unc, {"verdict": "CERTAIN", "polygon": self.sq(0, 0, 20, 40), "margin_px": 2})
        self.assertTrue(np.array_equal(est, self.est))
        self.assertTrue(unc[20, 10])                  # sobre el contorno: la banda sigue incierta
        self.assertFalse(unc[20, 3])                  # fondo lejos del contorno: ya cierto
        self.assertFalse(unc[20, 15])                 # primer plano lejos del contorno: ya cierto
        self.assertGreater(n, 0)

    def test_include_exclude_and_uncertain_include(self):
        est, unc, _ = self.apply(self.est, self.unc, {"verdict": "EXCLUDE", "polygon": self.sq(10, 10, 15, 30)})
        self.assertFalse(est[20, 12] or unc[20, 12])
        est, unc, _ = self.apply(self.est, self.unc, {"verdict": "INCLUDE", "polygon": self.sq(30, 10, 35, 30)})
        self.assertTrue(est[20, 32] and not unc[20, 32])
        est, unc, _ = self.apply(self.est, self.unc, {"verdict": "UNCERTAIN_INCLUDE", "polygon": self.sq(30, 10, 35, 30)})
        self.assertTrue(est[20, 32] and unc[20, 32])
        with self.assertRaises(ValueError):
            self.apply(self.est, self.unc, {"verdict": "MAYBE", "polygon": self.sq(0, 0, 5, 5)})
