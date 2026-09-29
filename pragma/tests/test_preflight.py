import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from pragma_ae.preflight import sentinel_contact_sheet, specs_from_notebook

ROOT = Path(__file__).resolve().parents[1]
V10 = ROOT / "outputs" / "PRAGMA_A-E-menos-1_diagnostico_caso_chica_Codex.ipynb"
V11 = ROOT / "outputs" / "PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_1.ipynb"


class Preflight(unittest.TestCase):
    def test_specs_extracted_from_both_versions(self):
        s10, box10 = specs_from_notebook(json.loads(V10.read_text(encoding="utf-8")))
        s11, box11 = specs_from_notebook(json.loads(V11.read_text(encoding="utf-8")))
        self.assertEqual(len(s10), 18)
        self.assertEqual(len(s11), 18)
        self.assertEqual(box10, (2100, 300, 3500, 2247))
        self.assertEqual(box10, box11)
        moved = {s[0]: (a[1], s[1]) for s, a in zip(s11, s10) if s[1] != a[1]}
        self.assertEqual(moved, {"P-2": ((2600, 400), (2640, 430)),
                                 "P-3": ((2450, 700), (2400, 810)),
                                 "O2": ((2680, 300), (2700, 380))})

    def test_contact_sheet_reports_patch_statistics(self):
        image = np.full((300, 400, 3), 200, np.uint8)
        image[100:200, 100:200] = 40                 # "tela oscura"
        specs = [("K1", (150, 150), "keep_subject", "interior oscuro"),
                 ("O2", (30, 30), "drop_other_person", "pared"),
                 ("B1", (399, 299), "drop_background", "esquina")]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sheet.png"
            stats = sentinel_contact_sheet(image, specs, out, half=20, zoom=2)
            self.assertTrue(out.is_file())
            with Image.open(out) as sheet:
                self.assertEqual(sheet.size[0], 6 * (41 * 2 + 6))
        by_id = {s["sentinel_id"]: s for s in stats}
        self.assertEqual(by_id["K1"]["patch_luma_mean"], 40.0)
        self.assertEqual(by_id["O2"]["patch_luma_mean"], 200.0)
        self.assertEqual(by_id["B1"]["xy"], [399, 299])  # recorte en el borde sin fallar


if __name__ == "__main__":
    unittest.main()
