import unittest

import numpy as np

import itertools

from pragma_ae.keydiff import (compare_keys, compose_reference, contour_tiles, erode_square, exterior,
                               iou_with_uncertainty, labels, midline_estimate, opening, public_report)
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
        self.assertTrue(ref["reference_estimate_mask"][100, 62])    # más cerca del consenso
        self.assertFalse(ref["reference_estimate_mask"][109, 62])   # más cerca del fondo común

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
        est = ref["reference_estimate_mask"]
        self.assertTrue(est[30, 100])
        self.assertFalse(est[10, 21])
        self.assertEqual(ref["uncertain_area_px"], 4)
        self.assertTrue(ref["uncertain_mask"][109, 71])
        self.assertTrue(est[108, 70])                # más cerca del consenso que del fondo
        self.assertEqual(ref["estimate_policy"], "MIDLINE")
        unsure = compose_reference(self.d, {"A1": "UNCERTAIN_INCLUDE", "B1": "UNCERTAIN_EXCLUDE"})
        self.assertTrue(unsure["reference_estimate_mask"][30, 100])
        self.assertFalse(unsure["reference_estimate_mask"][10, 21])
        self.assertEqual(unsure["uncertain_area_px"], 4 + 260 + 3)

    def test_metrics_report_estimate_bounds_and_without_uncertain(self):
        ref = compose_reference(self.d, {"A1": "INCLUDE", "B1": "EXCLUDE"})
        m = iou_with_uncertainty(self.b, ref["reference_estimate_mask"], ref["uncertain_mask"])
        self.assertEqual(set(m), {"metric_all_pixels_estimate", "metric_all_pixels_min", "metric_all_pixels_max",
                                  "metric_excluding_uncertain", "uncertain_area_px", "uncertain_fraction"})
        self.assertLessEqual(m["metric_all_pixels_min"], m["metric_all_pixels_estimate"])
        self.assertLessEqual(m["metric_all_pixels_estimate"], m["metric_all_pixels_max"])
        self.assertEqual(m["uncertain_area_px"], 4)

    def test_unknown_policy(self):
        with self.assertRaises(ValueError):
            compose_reference(self.d, {"A1": "INCLUDE", "B1": "EXCLUDE"}, estimate_policy="MEAN")


class UncertaintyEstimate(unittest.TestCase):
    """ChatGPT 009 §2–3: dentro de lo incierto no se inventa verdad; el estimador declara su política."""

    @staticmethod
    def shifted(dx):
        a = np.zeros((30, 40), bool); a[10:20, 10:20] = True
        b = np.zeros((30, 40), bool); b[10:20, 10 + dx:20 + dx] = True
        return a, b

    def test_two_equal_rectangles_shifted_1px_must_not_silently_become_union_without_declared_union_policy(self):
        a, b = self.shifted(1)
        d = compare_keys(a, b)
        self.assertEqual((d["summary"]["thin_px"], d["components"]), (20, []))
        default = compose_reference(d, {})
        self.assertEqual(default["estimate_policy"], "MIDLINE")
        self.assertEqual(int(default["reference_estimate_mask"].sum()), 100)     # ni 90 ni 110
        self.assertEqual(default["uncertain_area_px"], 20)
        union = compose_reference(d, {}, estimate_policy="UNION")
        self.assertEqual((union["estimate_policy"], int(union["reference_estimate_mask"].sum())), ("UNION", 110))
        inter = compose_reference(d, {}, estimate_policy="INTERSECTION")
        self.assertEqual(int(inter["reference_estimate_mask"].sum()), 90)

    def test_midline_of_a_2px_shift_is_the_1px_shift(self):
        a, b = self.shifted(2)
        est = compose_reference(compare_keys(a, b), {})["reference_estimate_mask"]
        expected = np.zeros_like(a); expected[10:20, 11:21] = True
        self.assertTrue(np.array_equal(est[11:19], expected[11:19]))     # interior: línea media exacta
        self.assertLessEqual(int((est ^ expected).sum()), 4)             # esquinas equidistantes: tablero

    def test_midline_does_not_favor_either_key(self):
        a, b = self.shifted(1)
        ab = compose_reference(compare_keys(a, b), {})["reference_estimate_mask"]
        ba = compose_reference(compare_keys(b, a), {})["reference_estimate_mask"]
        self.assertTrue(np.array_equal(ab, ba))
        self.assertEqual(int((ab & a).sum()), int((ab & b).sum()))

    def test_midline_estimate_only_touches_targets(self):
        a, b = self.shifted(3)
        bg = ~(a | b)
        targets = a ^ b
        est = midline_estimate(a & b, bg, targets)
        self.assertFalse((est & ~targets).any())

    def test_bounds_are_exact_by_brute_force(self):
        rng = np.random.default_rng(5)
        for _ in range(40):
            shape = (5, 6)
            p = rng.random(shape) > 0.5
            u = np.zeros(shape, bool)
            u.flat[rng.choice(u.size, size=int(rng.integers(0, 9)), replace=False)] = True
            f = (rng.random(shape) > 0.5) & ~u
            if not (p | f).any():
                continue
            cells = list(zip(*np.nonzero(u)))
            values = []
            for bits in itertools.product((False, True), repeat=len(cells)):
                ref = f.copy()
                for (y, x), bit in zip(cells, bits):
                    ref[y, x] = bit
                inter, union = int((p & ref).sum()), int((p | ref).sum())
                values.append(inter / union if union else 0.0)
            m = iou_with_uncertainty(p, f, u)
            self.assertAlmostEqual(m["metric_all_pixels_min"], min(values), places=6)
            self.assertAlmostEqual(m["metric_all_pixels_max"], max(values), places=6)

    def test_no_uncertainty_collapses_the_interval(self):
        a, _ = self.shifted(0)
        m = iou_with_uncertainty(a, a, np.zeros_like(a))
        self.assertEqual((m["metric_all_pixels_min"], m["metric_all_pixels_max"]), (1.0, 1.0))


class ContourTiles(unittest.TestCase):
    def test_tiles_cover_every_contour_pixel_and_mark_challenges(self):
        ref = person((300, 400))
        ref[150:250, 100:300] = True
        unc = np.zeros_like(ref); unc[200, 100] = True
        tiles = contour_tiles(ref, unc, zones={"pelo": [(60, 10, 120, 50)]}, size=128, overlap=16)
        covered = np.zeros_like(ref)
        for t in tiles:
            x1, y1, x2, y2 = t["box"]
            covered[y1:y2, x1:x2] = True
        contour = ref & ~erode_square(ref, 1)
        self.assertFalse((contour & ~covered).any())
        self.assertTrue(any(t["challenge"] and t["uncertain_px"] for t in tiles))
        self.assertTrue(any("pelo" in t["zones"] for t in tiles))
        self.assertTrue(all(t["contour_px"] > 0 for t in tiles))

    def test_image_frame_is_not_contour(self):
        ref = np.zeros((64, 64), bool); ref[:, :] = True
        self.assertEqual(contour_tiles(ref, size=32, overlap=0), [])


if __name__ == "__main__":
    unittest.main()
