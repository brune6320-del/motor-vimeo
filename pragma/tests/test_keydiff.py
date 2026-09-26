import unittest

import numpy as np

from pragma_ae.keydiff import (compare_keys, compose_reference, erode_square, exterior, labels, masked_iou,
                               opening, public_report)
from pragma_ae.masks import components, dilate_square, enclosed_holes


def person(shape=(120, 160)):
    """Silueta sintética: torso + cabeza + un lóbulo lateral de pelo que llega a la silueta."""
    m = np.zeros(shape, bool)
    m[40:110, 50:110] = True       # torso
    m[15:45, 65:95] = True         # cabeza
    m[20:60, 95:108] = True        # lóbulo lateral (pelo junto al mentón)
    return m


class Primitives(unittest.TestCase):
    def test_labels_match_components(self):
        rng = np.random.default_rng(3)
        m = rng.random((40, 50)) > 0.6
        self.assertEqual(int(labels(m).max()), len(components(m)))

    def test_erosion_and_opening(self):
        m = np.zeros((20, 20), bool)
        m[5:15, 5:15] = True
        m[0:20, 18] = True            # franja de 1 px que toca el marco
        self.assertEqual(int(erode_square(m, 1).sum()), 64)
        opened = opening(m, 1)
        self.assertEqual(int(opened.sum()), 100)
        self.assertFalse(opened[:, 18].any())

    def test_exterior_excludes_holes(self):
        m = np.zeros((20, 20), bool)
        m[4:16, 4:16] = True
        m[8:12, 8:12] = False
        ext = exterior(m)
        self.assertFalse(ext[9, 9])
        self.assertTrue(ext[0, 0])


class CompareKeys(unittest.TestCase):
    def test_identical_keys(self):
        a = person()
        d = compare_keys(a, a.copy())
        self.assertEqual(d["summary"]["xor_px"], 0)
        self.assertEqual(d["components"], [])

    def test_tracing_jitter_is_thin_not_a_discrepancy(self):
        a = person()
        b = dilate_square(a, 1)      # la otra llave traza 1 px más afuera en toda la silueta
        d = compare_keys(a, b)
        self.assertGreater(d["summary"]["xor_px"], 100)
        self.assertEqual(d["components"], [])
        self.assertEqual(d["summary"]["thin_px"], d["summary"]["xor_px"])

    def test_open_loss_like_n04_is_found_although_no_hole_exists(self):
        a = person()
        b = a.copy()
        b[20:40, 95:108] = False     # a B le falta el lóbulo alto, abierto al exterior
        self.assertEqual(enclosed_holes(b, 1), [])     # un detector de agujeros no ve nada
        d = compare_keys(a, b)
        self.assertEqual(len(d["components"]), 1)
        c = d["components"][0]
        self.assertEqual((c["id"], c["kind"], c["missing_from"]), ("A1", "THICK", "B"))
        self.assertEqual(c["open_or_enclosed"], "OPEN")
        self.assertTrue(c["touches_mask_exterior"])
        self.assertTrue(c["touches_consensus"])
        self.assertIsNone(c["semantic_adjudication"])

    def test_enclosed_hole_is_marked_enclosed(self):
        a = person()
        b = a.copy()
        b[60:80, 70:90] = False
        d = compare_keys(a, b)
        [c] = d["components"]
        self.assertEqual((c["kind"], c["area_px"], c["open_or_enclosed"]), ("THICK", 400, "ENCLOSED"))
        self.assertFalse(c["touches_mask_exterior"])

    def test_tiny_detached_island_survives_tolerance(self):
        a = person()
        b = a.copy()
        b[10, 20:23] = True          # isla de 3 px lejos de la silueta (otra persona)
        d = compare_keys(a, b, tolerance_px=2)
        [c] = d["components"]
        self.assertEqual((c["id"], c["kind"], c["area_px"], c["missing_from"]), ("B1", "ISLAND", 3, "A"))
        self.assertFalse(c["touches_consensus"])
        self.assertEqual(c["open_or_enclosed"], "OPEN")

    def test_small_attached_bump_is_thin(self):
        a = person()
        b = a.copy()
        b[108:110, 70:72] = False    # mordisco de 2×2 en el contorno
        d = compare_keys(a, b)
        self.assertEqual(d["components"], [])
        self.assertEqual(d["summary"]["thin_px"], 4)

    def test_systematic_offset_is_one_thick_component(self):
        a = person()
        b = dilate_square(a, 5)
        d = compare_keys(a, b, tolerance_px=2)
        self.assertEqual(d["summary"]["n_thick"], 1)
        self.assertEqual(d["components"][0]["missing_from"], "A")

    def test_small_attached_thick_is_listed_but_optional(self):
        a = person()
        b = a.copy()
        b[100:110, 60:66] = False     # mordisco de 10×6 = 60 px en el borde inferior
        d = compare_keys(a, b)
        [c] = d["components"]
        self.assertEqual((c["kind"], c["area_px"], c["requires_adjudication"]), ("THICK", 60, False))
        self.assertEqual(d["summary"]["auto_uncertain_px"], 60)
        ref = compose_reference(d, {})
        self.assertEqual(ref["uncertain_area_px"], 60)
        self.assertTrue(ref["mask"][100, 62])          # a ≤ 2 px del consenso
        self.assertFalse(ref["mask"][109, 62])

    def test_image_border(self):
        a = np.zeros((50, 50), bool); a[10:50, 10:40] = True
        b = a.copy(); b[40:50, 10:40] = False
        [c] = compare_keys(a, b)["components"]
        self.assertTrue(c["touches_image_border"])

    def test_partition_of_xor_on_random_masks(self):
        rng = np.random.default_rng(11)
        for _ in range(5):
            a = dilate_square(rng.random((60, 70)) > 0.985, 3)
            b = dilate_square(rng.random((60, 70)) > 0.985, 3)
            s = compare_keys(a, b)["summary"]
            self.assertEqual(s["adjudicable_px"] + s["thin_px"], s["xor_px"])
            self.assertEqual(s["a_only_px"] + s["b_only_px"], s["xor_px"])

    def test_public_report_is_serializable(self):
        import json
        a = person(); b = a.copy(); b[10, 20:23] = True
        json.dumps(public_report(compare_keys(a, b)))

    def test_size_mismatch(self):
        with self.assertRaises(ValueError):
            compare_keys(np.zeros((4, 4), bool), np.zeros((4, 5), bool))


class ComposeReference(unittest.TestCase):
    def setUp(self):
        self.a = person()
        self.b = self.a.copy()
        self.b[20:40, 95:108] = False      # A1: lóbulo que falta en B
        self.b[10, 20:23] = True           # B1: isla en otra persona
        self.b[108:110, 70:72] = False     # thin
        self.d = compare_keys(self.a, self.b)

    def test_every_component_must_be_adjudicated(self):
        with self.assertRaises(ValueError):
            compose_reference(self.d, {"A1": "INCLUDE"})
        with self.assertRaises(ValueError):
            compose_reference(self.d, {"A1": "INCLUDE", "B1": "MAYBE"})

    def test_three_states(self):
        ref = compose_reference(self.d, {"A1": "INCLUDE", "B1": "EXCLUDE"})
        self.assertTrue(ref["mask"][30, 100])
        self.assertFalse(ref["mask"][10, 21])
        self.assertEqual(ref["uncertain_area_px"], 4)
        self.assertTrue(ref["uncertain_mask"][109, 71])
        self.assertTrue(ref["mask"][108, 70])        # línea media: a ≤ t px del consenso
        unsure = compose_reference(self.d, {"A1": "UNCERTAIN_INCLUDE", "B1": "UNCERTAIN_EXCLUDE"})
        self.assertTrue(unsure["mask"][30, 100])
        self.assertFalse(unsure["mask"][10, 21])
        self.assertEqual(unsure["uncertain_area_px"], 4 + 260 + 3)

    def test_metrics_report_all_pixels_and_without_uncertain(self):
        ref = compose_reference(self.d, {"A1": "INCLUDE", "B1": "EXCLUDE"})
        m = masked_iou(self.b, ref["mask"], ref["uncertain_mask"])
        self.assertLess(m["metric_all_pixels"], m["metric_excluding_uncertain"] + 1e-9)
        self.assertEqual(m["uncertain_area_px"], 4)
        self.assertIn("uncertain_fraction", m)
        self.assertEqual(set(masked_iou(self.a, ref["mask"])), {"metric_all_pixels"})


if __name__ == "__main__":
    unittest.main()
