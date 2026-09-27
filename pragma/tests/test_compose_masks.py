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
