"""Preflight de coordenadas: hoja de contactos por sentinela a resolución nativa.

El overlay de A-E(−1) v1.0 mostraba los 18 puntos sobre la foto entera: a esa escala
dos puntos que caían en la pared parecían estar sobre la persona posterior. La hoja
de contactos (operación tomada de la fotografía analógica: una tira por toma para
juzgar cada una a su tamaño) recorta cada punto a 1:1 ampliado, con su parche de
evaluación dibujado, para confirmar ID por ID.

``sentinel_contact_sheet`` es autocontenida a propósito: el constructor del cuaderno
v1.1 copia su código fuente tal cual en la celda de configuración, de modo que Colab
y el kit local ejecutan exactamente la misma función.
"""

from __future__ import annotations

import re


def sentinel_contact_sheet(image, specs, out_path, half=90, zoom=2, patch_radius=6, columns=6):
    """Hoja de contactos de sentinelas. Devuelve estadísticas locales por ID.

    ``specs``: objetos con ``sentinel_id``, ``xy``, ``group``, ``description`` o tuplas
    ``(sentinel_id, (x, y), group, description)``. Las estadísticas (media y desviación de
    luminancia en el parche evaluado) son registro, no veredicto: la confirmación es humana.
    """
    import unicodedata

    import numpy as np
    from PIL import Image, ImageDraw, ImageFont

    def ascii_text(value):  # la fuente por defecto de Pillow no garantiza tildes ni símbolos
        return unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")

    colors = {
        "prompt_positive": (40, 90, 255), "prompt_negative_other_person": (255, 40, 40),
        "keep_subject": (60, 230, 60), "drop_other_person": (255, 0, 255), "drop_background": (0, 220, 255),
    }
    try:
        font = ImageFont.load_default(size=15)
    except TypeError:  # Pillow antiguo sin tamaño
        font = ImageFont.load_default()
    rgb = np.asarray(image)
    gray = rgb.astype(np.float32).mean(axis=2) if rgb.ndim == 3 else rgb.astype(np.float32)
    height, width = gray.shape
    side = (2 * half + 1) * zoom
    header = 58
    tiles, stats = [], []
    for spec in specs:
        if isinstance(spec, tuple):
            sid, xy, group, description = spec
        else:
            sid, xy, group, description = spec.sentinel_id, spec.xy, spec.group, spec.description
        x, y = int(round(float(xy[0]))), int(round(float(xy[1])))
        x0, y0, x1, y1 = max(0, x - half), max(0, y - half), min(width, x + half + 1), min(height, y + half + 1)
        crop = Image.fromarray(np.ascontiguousarray(rgb[y0:y1, x0:x1]).astype(np.uint8))
        crop = crop.resize(((x1 - x0) * zoom, (y1 - y0) * zoom), Image.NEAREST)
        tile = Image.new("RGB", (side, side + header), (0, 0, 0))
        offset_x, offset_y = (x0 - (x - half)) * zoom, header + (y0 - (y - half)) * zoom
        tile.paste(crop, (offset_x, offset_y))
        draw = ImageDraw.Draw(tile)
        color = colors.get(group, (255, 255, 0))
        cx, cy = half * zoom + zoom // 2, header + half * zoom + zoom // 2
        r = (patch_radius + 0.5) * zoom
        draw.rectangle([cx - r, cy - r, cx + r, cy + r], outline=color, width=2)
        for a, b in (((cx - 3 * r, cy), (cx - 1.5 * r, cy)), ((cx + 1.5 * r, cy), (cx + 3 * r, cy)),
                     ((cx, cy - 3 * r), (cx, cy - 1.5 * r)), ((cx, cy + 1.5 * r), (cx, cy + 3 * r))):
            draw.line([a, b], fill=color, width=2)
        patch = gray[max(0, y - patch_radius):y + patch_radius + 1, max(0, x - patch_radius):x + patch_radius + 1]
        mean, std = float(patch.mean()), float(patch.std())
        draw.text((6, 4), ascii_text(f"{sid} - {group}"), fill=color, font=font)
        draw.text((6, 22), ascii_text(description)[:46], fill=(235, 235, 235), font=font)
        draw.text((6, 40), f"({x},{y})  luma media={mean:.0f} sd={std:.0f}", fill=(180, 180, 180), font=font)
        tiles.append(tile)
        stats.append({"sentinel_id": sid, "xy": [x, y], "group": group, "description": description,
                      "patch_luma_mean": round(mean, 1), "patch_luma_std": round(std, 1)})
    rows = (len(tiles) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * (side + 6), rows * (side + header + 6)), (25, 25, 25))
    for index, tile in enumerate(tiles):
        sheet.paste(tile, ((index % columns) * (side + 6), (index // columns) * (side + header + 6)))
    sheet.save(out_path)
    return stats


SPEC_PATTERN = re.compile(r'SentinelSpec\("([A-Z+\-0-9\']+)", \((\d+), (\d+)\), "([a-z_]+)", "([^"]*)"\)')
BOX_PATTERN = re.compile(r"BOX_CHICA_XYXY = \((\d+), (\d+), (\d+), (\d+)\)")


def specs_from_notebook(notebook: dict):
    """Extrae los sentinelas reales (no sintéticos) y la caja de un cuaderno A-E(−1)."""
    code = "\n".join("".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code")
    specs = [(sid, (int(x), int(y)), group, desc) for sid, x, y, group, desc in SPEC_PATTERN.findall(code)
             if not sid.startswith("S")]
    box = BOX_PATTERN.search(code)
    return specs, (tuple(int(v) for v in box.groups()) if box else None)
