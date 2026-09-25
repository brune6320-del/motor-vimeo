"""Lámina numerada A-E0: cada objeto del inventario con su número y su tier.

Es la herramienta de la pasada humana: se imprime o se abre a pantalla completa y
se contrasta con la foto, objeto por objeto. Como deriva de la foto, se genera
localmente (``local/``) y nunca se versiona en el repositorio público.
"""

from __future__ import annotations

TIER_COLORS = {"A": (255, 200, 0), "B": (0, 200, 255), "C": (255, 90, 200), "IGNORE": (150, 150, 150)}


def numbered_sheet(image, objects, out_path, max_side=2400, tiers=("A", "B", "C")):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont

    base = Image.fromarray(np.asarray(image).astype(np.uint8))
    scale = min(1.0, max_side / max(base.size))
    if scale < 1.0:
        base = base.resize((round(base.size[0] * scale), round(base.size[1] * scale)), Image.LANCZOS)
    base = base.convert("RGB")
    draw = ImageDraw.Draw(base)
    try:
        font = ImageFont.load_default(size=max(12, int(22 * scale / 0.6)))
    except TypeError:
        font = ImageFont.load_default()
    width = max(2, int(4 * scale / 0.6))
    shown = []
    # Primero C, luego B, luego A: las instancias principales quedan encima.
    order = {"C": 0, "IGNORE": 0, "B": 1, "A": 2}
    for obj in sorted(objects, key=lambda o: order.get(o["tier"], 0)):
        if obj["tier"] not in tiers:
            continue
        color = TIER_COLORS.get(obj["tier"], (255, 255, 255))
        x1, y1, x2, y2 = (v * scale for v in obj["bbox"])
        draw.rectangle([x1, y1, x2, y2], outline=color, width=width if obj["tier"] == "A" else max(1, width - 1))
        label = obj["id"].split("_")[-1].lstrip("0") or "0"
        left, top, right, bottom = draw.textbbox((x1 + 3, y1 + 2), label, font=font)
        draw.rectangle([left - 2, top - 2, right + 2, bottom + 2], fill=(0, 0, 0))
        draw.text((x1 + 3, y1 + 2), label, fill=color, font=font)
        shown.append(obj)
    base.save(out_path)
    return shown


def legend_markdown(objects) -> str:
    lines = ["| # | id | nombre | tier | concepto | oclusión | truncado | padre | por verificar |",
             "|---:|---|---|---|---|---|---|---|---|"]
    for obj in objects:
        number = obj["id"].split("_")[-1].lstrip("0") or "0"
        lines.append(
            f"| {number} | `{obj['id']}` | {obj['canonical_name']} | {obj['tier']} | {obj['concept_en']} | "
            f"{obj['occlusion']} | {obj['truncation']} | {obj['parent_id'] or '—'} | {', '.join(obj['review']) or '—'} |"
        )
    return "\n".join(lines) + "\n"
