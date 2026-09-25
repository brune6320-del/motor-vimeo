"""Localizar y abrir la foto de aceptación por contenido (el nombre puede variar)."""

from __future__ import annotations

from pathlib import Path

from . import EXPECTED_IMAGE_SHA256, EXPECTED_IMAGE_SIZE
from .inventory import sha256_file

PRAGMA_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES = (
    PRAGMA_ROOT / "inputs" / "P1070614.JPG",
    Path.home() / "Desktop" / "P1070614.JPG",
    Path("/content/P1070614.JPG"),
    Path("/mnt/data/P1070614.JPG"),
)


def locate_image(explicit=None) -> Path:
    candidates = [Path(explicit)] if explicit else []
    candidates += list(DEFAULT_CANDIDATES)
    candidates += sorted((PRAGMA_ROOT / "inputs").glob("*.[jJ][pP][gG]"))
    seen = set()
    for path in candidates:
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        if sha256_file(path) == EXPECTED_IMAGE_SHA256:
            return path
    if explicit:
        raise FileNotFoundError(f"{explicit} no es la foto de aceptación (SHA-256 distinto)")
    raise FileNotFoundError("No se encontró la foto de aceptación; colócala en pragma/inputs/ (ver inputs/README.md)")


def load_rgb(path):
    """Devuelve la foto como array RGB uint8 tras aplicar EXIF, verificando tamaño."""
    import numpy as np
    from PIL import Image, ImageOps

    with Image.open(path) as handle:
        image = ImageOps.exif_transpose(handle).convert("RGB")
    array = np.asarray(image)
    if (array.shape[1], array.shape[0]) != EXPECTED_IMAGE_SIZE:
        raise ValueError(f"tamaño {array.shape[1]}×{array.shape[0]} ≠ {EXPECTED_IMAGE_SIZE}")
    return array
