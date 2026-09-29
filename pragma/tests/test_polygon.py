import unittest

import numpy as np

from pragma_ae.polygon import rasterize, rasterize_person


class Rasterize(unittest.TestCase):
    def test_axis_aligned_square_is_exact(self):
        m = rasterize([[[2, 3], [7, 3], [7, 9], [2, 9]]], (12, 12))
        self.assertEqual(int(m.sum()), 30)
        self.assertTrue(m[3:9, 2:7].all())
        self.assertFalse(m[2, 2] or m[9, 2] or m[3, 7])

    def test_vertex_order_does_not_matter(self):
        cw = rasterize([[[2, 3], [7, 3], [7, 9], [2, 9]]], (12, 12))
        ccw = rasterize([[[2, 9], [7, 9], [7, 3], [2, 3]]], (12, 12))
        self.assertTrue(np.array_equal(cw, ccw))

    def test_triangle_area_close_to_analytic(self):
        m = rasterize([[[0, 0], [200, 0], [0, 100]]], (120, 220))
        self.assertLess(abs(int(m.sum()) - 10000) / 10000, 0.01)

    def test_inner_ring_is_a_hole(self):
        outer = [[0, 0], [20, 0], [20, 20], [0, 20]]
        hole = [[5, 5], [15, 5], [15, 15], [5, 15]]
        m = rasterize([outer, hole], (25, 25))
        self.assertEqual(int(m.sum()), 400 - 100)
        self.assertFalse(m[10, 10])

    def test_clipped_to_image(self):
        m = rasterize([[[-10, -10], [5, -10], [5, 5], [-10, 5]]], (8, 8))
        self.assertEqual(int(m.sum()), 25)

    def test_pixel_center_convention(self):
        m = rasterize([[[0, 0], [2.4, 0], [2.4, 1], [0, 1]]], (2, 4))
        self.assertEqual(m[0].tolist(), [True, True, False, False])   # centro 2.5 > 2.4

    def test_bad_ring(self):
        with self.assertRaises(ValueError):
            rasterize([[[0, 0], [1, 1]]], (4, 4))

    def test_person_entry_with_uncertain(self):
        entry = {"rings": [[[0, 0], [10, 0], [10, 10], [0, 10]]],
                 "uncertain_rings": [[[8, 0], [12, 0], [12, 10], [8, 10]]]}
        r = rasterize_person(entry, (12, 14))
        self.assertEqual(int(r["mask"].sum()), 100)
        self.assertEqual(int(r["uncertain"].sum()), 40)
        self.assertFalse(rasterize_person({"rings": entry["rings"]}, (12, 14))["uncertain"].any())


class PolygonFileValidator(unittest.TestCase):
    """``work/validate_ae0_polygons.py``. ae0_002 llega al borde inferior de la foto, como las personas
    reales ae0_001 y ae0_002: ahí ``rasterize`` recortaría en silencio un vértice fuera de la imagen."""

    def setUp(self):
        import json
        import sys
        import tempfile
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "work"))
        from validate_ae0_polygons import check
        self.check, self.json = check, json
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ip, self.pp = Path(self.tmp.name) / "inv.json", Path(self.tmp.name) / "pol.json"
        self.ip.write_text(json.dumps({"objects": [
            {"id": "ae0_001", "concept_en": "person", "bbox": [100, 100, 300, 400]},
            {"id": "ae0_002", "concept_en": "person", "bbox": [3500, 1800, 3900, 2248]},
            {"id": "ae0_010", "concept_en": "clock", "bbox": [0, 0, 10, 10]}]}))
        key = {"auditor": "prueba", "blind_statement": "x", "created": "2026-09-27", "derivation": "AI_POLYGON_RASTER",
               "image_sha256": "8f6e3b6f5013265a45c7e89121e3f0a18e3386951e2e75378b28da6d02ec529d"}
        self.data = {"schema": "pragma.ae0_polygons", "key": key,
                     "persons": {"ae0_001": {"rings": sq(110, 110, 290, 390)},
                                 "ae0_002": {"rings": sq(3510, 1810, 3890, 2248)}}}

    def run_check(self):
        self.pp.write_text(self.json.dumps(self.data))
        return self.check(self.pp, self.ip)

    def test_validator_accepts_three_persons_and_rejects_missing(self):
        ok = self.run_check()
        self.assertTrue(ok["valid"], ok["errors"])
        self.assertEqual(ok["persons"]["ae0_001"]["area_px"], 180 * 280)
        del self.data["persons"]["ae0_002"]
        self.data["persons"]["ae0_001"] = {"rings": sq(0, 0, 900, 900)}
        bad = self.run_check()
        self.assertFalse(bad["valid"])
        self.assertEqual(len(bad["errors"]), 2)

    def test_uncertain_ring_huge_outside_person_bbox_rejects(self):
        # Máscara normal y vértices dentro de la foto; solo la caja de la zona incierta la delata.
        self.data["persons"]["ae0_001"]["uncertain_rings"] = sq(0, 0, 4000, 2248)
        bad = self.run_check()
        self.assertFalse(bad["valid"])
        self.assertEqual(len(bad["errors"]), 1)
        self.assertIn("ae0_001: la zona incierta", bad["errors"][0])

    def test_uncertain_ring_valid_boundary_band_passes(self):
        # Banda de 20 px que cruza el contorno (x = 110 y x = 290): la mitad queda fuera de la máscara.
        band = sq(100, 100, 300, 400) + sq(120, 120, 280, 380)
        self.data["persons"]["ae0_001"]["uncertain_rings"] = band
        ok = self.run_check()
        self.assertTrue(ok["valid"], ok["errors"])
        self.assertEqual(ok["persons"]["ae0_001"]["uncertain_px"], 200 * 300 - 160 * 260)
        self.assertEqual(ok["persons"]["ae0_001"]["uncertain_bbox"], [100, 100, 300, 400])

    def test_main_ring_vertex_outside_image_rejects(self):
        # y = 2270 queda dentro de la caja ± 40 pero fuera de la foto: recortado, pasaba el control de caja.
        self.data["persons"]["ae0_002"]["rings"] = sq(3510, 1810, 3890, 2270)
        bad = self.run_check()
        self.assertFalse(bad["valid"])
        self.assertEqual(len(bad["errors"]), 1)
        self.assertIn("ae0_002: rings[0]: 2 vértices fuera de la foto", bad["errors"][0])

    def test_uncertain_ring_vertex_outside_image_rejects(self):
        self.data["persons"]["ae0_002"]["uncertain_rings"] = sq(3500, 2200, 3900, 2270)
        bad = self.run_check()
        self.assertFalse(bad["valid"])
        self.assertEqual(len(bad["errors"]), 1)
        self.assertIn("ae0_002: uncertain_rings[0]: 2 vértices fuera de la foto", bad["errors"][0])

    def test_non_finite_vertex_rejects(self):
        ring = sq(110, 110, 290, 390)
        ring[0][2] = [float("nan"), 390]
        self.data["persons"]["ae0_001"]["rings"] = ring
        bad = self.run_check()
        self.assertFalse(bad["valid"])
        self.assertIn("ae0_001: rings[0]: 1 vértices no finitos", bad["errors"][0])

    def test_vertex_on_image_border_is_inside(self):
        self.data["persons"]["ae0_002"]["uncertain_rings"] = sq(3500, 2200, 3900, 2248)
        ok = self.run_check()
        self.assertTrue(ok["valid"], ok["errors"])


def sq(x1, y1, x2, y2):
    return [[[x1, y1], [x2, y1], [x2, y2], [x1, y2]]]


if __name__ == "__main__":
    unittest.main()
