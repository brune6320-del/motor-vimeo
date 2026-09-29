"""Láminas de evidencia de la comparación de llaves A‑E0 (privadas: derivan de la foto; van a local/).

    python3 work/ae0_key_evidence.py <salida_dir> x1,y1,x2,y2[:nombre] ...

Dibuja sobre el recorte las cajas de las dos llaves: Claude en magenta (``C:nnn``) y ChatGPT en cian
(``G:nnn``), con el número de cada objeto. No decide nada: solo muestra la evidencia para adjudicar.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pragma_ae.imageio import load_rgb, locate_image  # noqa: E402

KEYS = (("C", ROOT / "ae0/llaves/llave_claude_A-E0.json", (255, 0, 255)),
        ("G", ROOT / "ae0/llaves/llave_chatgpt_A-E0.json", (0, 230, 255)))


def render(photo, crop, out, max_w=1600):
    x1, y1, x2, y2 = crop
    img = Image.fromarray(photo[y1:y2, x1:x2])
    s = min(1.0, max_w / img.width)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    for tag, path, col in KEYS:
        for o in json.loads(path.read_text(encoding="utf-8"))["objects"]:
            a, b, c, e = o["bbox"]
            if c <= x1 or a >= x2 or e <= y1 or b >= y2 or o["kind"] == "stuff":
                continue
            box = [(a - x1) * s, (b - y1) * s, (c - x1) * s - 1, (e - y1) * s - 1]
            d.rectangle(box, outline=col, width=2)
            d.text((box[0] + 3, box[1] + (3 if tag == "C" else 14)), f"{tag}:{o['id'][-3:]}", fill=col)
    img.save(out, quality=88)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    out_dir = Path(args[0]); out_dir.mkdir(parents=True, exist_ok=True)
    photo = np.asarray(load_rgb(locate_image()))
    for spec in args[1:]:
        coords, _, name = spec.partition(":")
        crop = tuple(int(v) for v in coords.split(","))
        render(photo, crop, out_dir / f"{name or coords.replace(',', '_')}.jpg")
        print(out_dir / f"{name or coords.replace(',', '_')}.jpg")


if __name__ == "__main__":
    main()
