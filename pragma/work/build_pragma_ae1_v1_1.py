"""Construye A-E(−1) v1.1 a partir del cuaderno Codex v1.0, sin tocar el original.

Cambios (todos detectados por el preflight con la foto real, ver
``preflight/PREFLIGHT_A-E-menos-1_v1_0.md``):

1. P-3 estaba sobre la pared (luma media 205, igual que la pared de referencia):
   pasa al hombro posterior, tela oscura.
2. O2 estaba sobre la pared, ~20 px por encima del moño: pasa al interior del moño.
3. P-2 estaba justo en el borde pared/moño: pasa al interior del moño.
4. O3 y O4 caen en zonas de contacto de propietario dudoso: no se mueven, pero su
   descripción exige confirmar a quién pertenecen.
5. La celda de configuración genera y guarda una hoja de contactos por sentinela
   (misma función que ``pragma_ae.preflight.sentinel_contact_sheet``) y el ZIP la incluye.

``AEM1_CONFIG_CONFIRMADA`` sigue en ``False``: confirmar es una decisión humana.
"""

import hashlib
import inspect
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pragma_ae.preflight import sentinel_contact_sheet  # noqa: E402

SOURCE = ROOT / "outputs" / "PRAGMA_A-E-menos-1_diagnostico_caso_chica_Codex.ipynb"
OUT = ROOT / "outputs" / "PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_1.ipynb"
SOURCE_SHA256 = "5941be56b22fccc3efd4e299cc8ee6a12cb7c473d2977d4c0876e4e2ea73b706"

COORDINATE_CHANGES = [
    ('SentinelSpec("P-2", (2600, 400), "prompt_negative_other_person", "cabello/cabeza posterior"),',
     'SentinelSpec("P-2", (2640, 430), "prompt_negative_other_person", "cabello recogido posterior (v1.1: antes borde con pared)"),'),
    ('SentinelSpec("P-3", (2450, 700), "prompt_negative_other_person", "hombro posterior"),',
     'SentinelSpec("P-3", (2400, 810), "prompt_negative_other_person", "hombro posterior, tela oscura (v1.1: antes pared)"),'),
    ('SentinelSpec("O2", (2680, 300), "drop_other_person", "cabello posterior superior"),',
     'SentinelSpec("O2", (2700, 380), "drop_other_person", "cabello recogido posterior (v1.1: antes pared)"),'),
    ('SentinelSpec("O3", (2680, 520), "drop_other_person", "cabello posterior central"),',
     'SentinelSpec("O3", (2680, 520), "drop_other_person", "cabello en contacto: CONFIRMAR PROPIETARIO"),'),
    ('SentinelSpec("O4", (2335, 1035), "drop_other_person", "manga/torso posterior"),',
     'SentinelSpec("O4", (2335, 1035), "drop_other_person", "borde manga/hombro: CONFIRMAR PROPIETARIO"),'),
]

CONFIG_REVISION = [(
    '    "schema_version": CODEX_AEM1_SCHEMA_VERSION,\n    "image_sha256": IMAGE_SHA256,\n',
    '    "schema_version": CODEX_AEM1_SCHEMA_VERSION,\n'
    '    "config_revision": "1.1",\n'
    '    "config_revision_note": "P-2, P-3 y O2 reubicados tras preflight con la foto real; O3/O4 exigen confirmar propietario",\n'
    '    "image_sha256": IMAGE_SHA256,\n',
)]

CONTACT_SHEET_CALL = '''

# v1.1 · Hoja de contactos: cada sentinela a resolución nativa ×2, con su parche de evaluación.
# El overlay completo no basta: a esa escala dos puntos sobre la pared parecían estar sobre la persona.
CONFIG_CONTACT_SHEET_PATH = RUN_DIR / "aem1_config_contact_sheet.png"
AEM1_CONTACT_STATS = sentinel_contact_sheet(image, ALL_SPECS, CONFIG_CONTACT_SHEET_PATH, patch_radius=PATCH_RADIUS)
plt.figure(figsize=(22, 13)); plt.imshow(Image.open(CONFIG_CONTACT_SHEET_PATH)); plt.axis("off")
plt.title("CONFIRMA ID POR ID: cada cuadro debe caer sobre la región descrita"); plt.show()
'''

OVERLAY_ANCHOR = 'fig.tight_layout(); fig.savefig(CONFIG_OVERLAY_PATH, dpi=160, bbox_inches="tight"); plt.show(); plt.close(fig)\n'

EXPORT_CHANGES = [
    ("for path in [CONFIG_JSON_PATH, CONFIG_OVERLAY_PATH, *current_proposal_artifacts,",
     "for path in [CONFIG_JSON_PATH, CONFIG_OVERLAY_PATH, CONFIG_CONTACT_SHEET_PATH, *current_proposal_artifacts,"),
    ('    "configuration": AEM1_CONFIG,\n',
     '    "configuration": AEM1_CONFIG,\n    "config_contact_sheet": AEM1_CONTACT_STATS,\n'),
]

TITLE_NOTE = """
> **v1.1 (preflight con la foto real, sin GPU).** Tres coordenadas del v1.0 no caían donde
> decían: `P-3` y `O2` estaban sobre la pared y `P-2` en el borde pared/moño. Se reubicaron
> dentro de la persona posterior; `O3` y `O4` quedan marcados para confirmar propietario.
> Se añade una hoja de contactos por sentinela. El resto del cuaderno es idéntico al v1.0
> (`5941be…b706`). `AEM1_CONFIG_CONFIRMADA` sigue en `False`: confirmar es tuyo.
"""

SECTION5_NOTE = """

**v1.1:** además del overlay, la celda muestra una **hoja de contactos** con cada sentinela
ampliado a su resolución nativa y el parche real que se evalúa. Confirma ID por ID en la
hoja, no en el overlay. `O3` y `O4` están en zonas de contacto: si no puedes decidir a
quién pertenecen, deja `False` y devuelve la hoja."""


def replace_once(text, old, new, where):
    if text.count(old) != 1:
        raise RuntimeError(f"{where}: se esperaba exactamente 1 aparición de {old[:70]!r}, hay {text.count(old)}")
    return text.replace(old, new)


def set_source(cell, text):
    cell["source"] = text.splitlines(True)


def main():
    raw = SOURCE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise RuntimeError("El cuaderno v1.0 no coincide con el hash esperado; no se construye v1.1")
    nb = json.loads(raw.decode("utf-8"))
    cells = {cell["id"]: cell for cell in nb["cells"]}

    title = "".join(cells["pragma-aem1-00"]["source"])
    title = replace_once(title, "# PRAGMA · A‑E(−1) — diagnóstico controlado del caso chica\n",
                         "# PRAGMA · A‑E(−1) v1.1 — diagnóstico controlado del caso chica\n" + TITLE_NOTE, "00")
    set_source(cells["pragma-aem1-00"], title)

    howto = "".join(cells["pragma-aem1-01"]["source"])
    howto = replace_once(howto, "3. Confirma visualmente la caja y los puntos prellenados.",
                         "3. Confirma visualmente la caja y los puntos prellenados **en la hoja de contactos**, ID por ID.", "01")
    set_source(cells["pragma-aem1-01"], howto)

    section5 = "".join(cells["pragma-aem1-06m"]["source"]).rstrip("\n") + SECTION5_NOTE + "\n"
    set_source(cells["pragma-aem1-06m"], section5)

    config = "".join(cells["pragma-aem1-06"]["source"])
    for old, new in COORDINATE_CHANGES + CONFIG_REVISION:
        config = replace_once(config, old, new, "06")
    function_source = inspect.getsource(sentinel_contact_sheet)
    config = replace_once(config, OVERLAY_ANCHOR, OVERLAY_ANCHOR + "\n" + function_source + CONTACT_SHEET_CALL, "06")
    set_source(cells["pragma-aem1-06"], config)

    export = "".join(cells["pragma-aem1-11"]["source"])
    for old, new in EXPORT_CHANGES:
        export = replace_once(export, old, new, "11")
    set_source(cells["pragma-aem1-11"], export)

    # Misma serialización que el constructor Codex v1.0 (compacta, UTF-8).
    OUT.write_text(json.dumps(nb, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(json.dumps({"out": str(OUT.relative_to(ROOT)), "sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
                      "bytes": OUT.stat().st_size}, indent=2))


if __name__ == "__main__":
    main()
