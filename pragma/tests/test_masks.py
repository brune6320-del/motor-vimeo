import unittest

import numpy as np

from pragma_ae.masks import (box_iou, dilate_square, intersection_area, mask_bbox, mask_iou,
                             packed_sha256, rle_decode, rle_encode)


class MaskPrimitives(unittest.TestCase):
    def test_bbox_is_half_open(self):
        m = np.zeros((10, 12), bool)
        m[2:5, 3:7] = True
        self.assertEqual(mask_bbox(m), (3, 2, 7, 5))
        self.assertIsNone(mask_bbox(np.zeros((4, 4), bool)))

    def test_iou_and_intersection(self):
        a = np.zeros((20, 20), bool); a[0:10, 0:10] = True
        b = np.zeros((20, 20), bool); b[5:15, 5:15] = True
        self.assertEqual(intersection_area(a, b), 25)
        self.assertAlmostEqual(mask_iou(a, b), 25 / 175)
        self.assertAlmostEqual(box_iou((0, 0, 10, 10), (5, 5, 15, 15)), 25 / 175)
        self.assertEqual(box_iou((0, 0, 5, 5), (5, 5, 9, 9)), 0.0)

    def test_dilation_matches_bruteforce(self):
        rng = np.random.default_rng(7)
        m = rng.random((31, 37)) > 0.97
        for radius in (0, 1, 3):
            expected = np.zeros_like(m)
            for y, x in zip(*np.nonzero(m)):
                expected[max(0, y - radius):y + radius + 1, max(0, x - radius):x + radius + 1] = True
            np.testing.assert_array_equal(dilate_square(m, radius), expected)

    def test_rle_roundtrip_column_major(self):
        rng = np.random.default_rng(3)
        for shape in ((5, 7), (1, 1), (13, 4)):
            m = rng.random(shape) > 0.5
            rle = rle_encode(m)
            self.assertEqual(sum(rle["counts"]), m.size)
            np.testing.assert_array_equal(rle_decode(rle), m)
        # Empieza por ceros: una máscara que arranca en 1 lleva un 0 inicial.
        full = np.ones((2, 2), bool)
        self.assertEqual(rle_encode(full)["counts"], [0, 4])
        # Orden por columnas.
        m = np.array([[1, 0], [1, 0]], bool)
        self.assertEqual(rle_encode(m)["counts"], [0, 2, 2])

    def test_packed_hash_depends_on_shape(self):
        a = np.zeros((2, 8), bool)
        b = np.zeros((4, 4), bool)
        self.assertNotEqual(packed_sha256(a), packed_sha256(b))


if __name__ == "__main__":
    unittest.main()
