"""Construye A-E(−1) v1.2 «un clic» a partir de v1.1, sin tocar v1.0 ni v1.1.

Objetivo de v1.2 (DEC-018-P): que la persona usuaria no tenga que fiscalizar nada en Colab.
Solo coloca la foto, pulsa «Ejecutar todas» y adjunta el ZIP; la verificación la hace el
auditor IA fuera de Colab, con evidencia y hashes, y ChatGPT puede contraauditar lo mismo.

Cambios respecto de v1.1:

1. O3 y O4 se reubican donde el propietario es inequívoco (moño y blusa floral de la persona
   posterior). La zona de contacto se audita con máscaras completas, no con dos puntos dudosos.
2. La configuración llega confirmada por el auditor IA y esa confirmación queda LIGADA a la
   evidencia: el cuaderno recalcula la luminancia de los 18 parches y la compara con la del
   preflight; si no coincide (foto o decodificación distinta), vuelve a PENDING_CONFIG.
3. Las correcciones se ejecutan para las TRES semillas de cada baseline (6 propuestas): ya no hay
   que elegir semillas. La elección manual sigue disponible marcando AEM1_SEEDS_CONFIRMADAS.
4. Sin selección en el cuaderno, el estado es PENDING_EXTERNAL_AUDIT y el ZIP se descarga igual.
5. La foto se busca por hash con cualquier nombre en /content (basta arrastrarla al panel
   Archivos, también en Brave) y existe un modo sin navegador (PRAGMA_HEADLESS=1) para Colab CLI.
6. Evidencias más livianas (dpi) para que el ZIP se pueda adjuntar en el chat.
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SOURCE = ROOT / "outputs" / "PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_1.ipynb"
OUT = ROOT / "outputs" / "PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_2.ipynb"
SOURCE_SHA256 = "ddf784956de6eb8555bb9eb1f30d7af1dcabba06121568a0d4bc62be60c500dc"

# Luminancia media del parche (radio 6) de cada sentinela v1.2 sobre la foto de aceptación,
# calculada con pragma_ae.preflight.sentinel_contact_sheet (la misma función embebida en la celda 06).
PREFLIGHT_EXPECTED_LUMA = {
    "P+1": 249.3, "P-1": 125.6, "P-2": 56.8, "P-3": 90.9,
    "K1": 245.8, "K2": 135.3, "K3": 101.4, "K4": 254.3, "K5": 101.7, "K6": 220.3, "K7": 252.9,
    "O1": 179.8, "O2": 78.7, "O3": 57.1, "O4": 185.1,
    "B1": 203.4, "B2": 182.9, "B3": 49.6,
}
CONFIRMED_BY = ("auditor IA · Claude Code · preflight v1.2: 18/18 puntos en su región "
                "(ver preflight/PREFLIGHT_A-E-menos-1_v1_2.md)")

TITLE_OLD = "# PRAGMA · A‑E(−1) v1.1 — diagnóstico controlado del caso chica\n"
TITLE_NEW = "# PRAGMA · A‑E(−1) v1.2 — diagnóstico controlado del caso chica · un clic\n"
TITLE_NOTE = """
> **v1.2 · no tienes que decidir nada aquí.** Coloca la foto, pulsa **Entorno de ejecución →
> Ejecutar todas** y adjunta el ZIP que se descarga al final en el chat. La configuración ya viene
> confirmada por el auditor IA y el cuaderno comprueba solo que la foto es la auditada; las
> correcciones se ejecutan para todas las semillas; la elección de la mejor máscara y la revisión
> visual se hacen fuera, con evidencia y hashes (estado `PENDING_EXTERNAL_AUDIT`).
"""

HOWTO_NEW = """## 0. Cómo usarlo (v1.2: sin decisiones)

1. **Entorno de ejecución → Cambiar tipo de entorno de ejecución →** GPU **L4** o **A100** (T4 también sirve).
2. Abre el panel **Archivos** (icono de carpeta, a la izquierda) y **arrastra `P1070614.JPG`** dentro. El nombre da igual: se reconoce por su huella SHA‑256. Si no lo haces, la sección 2 te pedirá elegir el archivo.
3. **Entorno de ejecución → Ejecutar todas.** Tarda unos minutos (la primera vez descarga el modelo, ~900 MB).
4. Al final se descarga solo `PRAGMA_AEM1_…_PENDING_EXTERNAL_AUDIT.zip`. Si la descarga no arranca, búscalo en el panel **Archivos** → `pragma_run/runs/…` → clic derecho → **Descargar**.
5. **Adjunta ese ZIP en el chat.** El auditor IA verifica hashes, revisa todas las candidatas a resolución completa y registra el veredicto.

No marques ni cambies ningún formulario: los valores por defecto son los correctos. Los formularios de las secciones 8 y 9 solo sirven si alguna vez quieres revisar a mano.
"""

COORDINATE_CHANGES = [
    ('SentinelSpec("O3", (2680, 520), "drop_other_person", "cabello en contacto: CONFIRMAR PROPIETARIO"),',
     'SentinelSpec("O3", (2735, 360), "drop_other_person", "cabello recogido posterior, arriba (v1.2: antes zona de contacto)"),'),
    ('SentinelSpec("O4", (2335, 1035), "drop_other_person", "borde manga/hombro: CONFIRMAR PROPIETARIO"),',
     'SentinelSpec("O4", (2325, 965), "drop_other_person", "blusa floral posterior, interior (v1.2: antes borde)"),'),
]

CONFIRMATION_OLD = 'AEM1_CONFIG_CONFIRMADA = False # @param {type:"boolean"}\n'
CONFIRMATION_NEW = (
    'AEM1_CONFIG_CONFIRMADA = True # @param {type:"boolean"}\n'
    "# v1.2 · Confirmación del auditor IA, ligada a evidencia: más abajo se recalcula la luminancia de\n"
    "# cada parche y debe coincidir con la del preflight. Si no coincide, la configuración NO queda lista.\n"
    f"AEM1_CONFIG_CONFIRMED_BY = {CONFIRMED_BY!r}\n"
    f"AEM1_PREFLIGHT_EXPECTED_LUMA = {json.dumps(PREFLIGHT_EXPECTED_LUMA)}\n"
    "AEM1_PREFLIGHT_TOLERANCE = 3.0\n"
)

REVISION_OLD = ('    "config_revision": "1.1",\n'
                '    "config_revision_note": "P-2, P-3 y O2 reubicados tras preflight con la foto real; O3/O4 exigen confirmar propietario",\n')
REVISION_NEW = ('    "config_revision": "1.2",\n'
                '    "config_revision_note": "v1.1 + O3/O4 reubicados en zonas de propietario inequívoco; confirmación del auditor IA ligada a la luminancia del preflight",\n'
                '    "confirmed_by": AEM1_CONFIG_CONFIRMED_BY,\n'
                '    "preflight_expected_luma": AEM1_PREFLIGHT_EXPECTED_LUMA,\n'
                '    "preflight_tolerance": AEM1_PREFLIGHT_TOLERANCE,\n')

READY_OLD = '''AEM1_CONFIG_READY = bool(AEM1_CONFIG_CONFIRMADA)
if AEM1_CONFIG_READY:
    print("CONFIGURACIÓN CONFIRMADA. Continúa con los baselines.")
else:
    print("PENDIENTE: revisa el overlay y la tabla. Si algo cae mal, no edites a ciegas: guarda captura y devuélvela a Codex.")
    print("Si todo coincide, marca AEM1_CONFIG_CONFIRMADA=True y reejecuta esta celda.")
'''
READY_NEW = '''AEM1_PREFLIGHT_DEVIATION = {
    s["sentinel_id"]: round(abs(s["patch_luma_mean"] - AEM1_PREFLIGHT_EXPECTED_LUMA[s["sentinel_id"]]), 2)
    for s in AEM1_CONTACT_STATS
}
AEM1_PREFLIGHT_MATCH = (set(AEM1_PREFLIGHT_DEVIATION) == set(AEM1_PREFLIGHT_EXPECTED_LUMA)
                        and max(AEM1_PREFLIGHT_DEVIATION.values()) <= AEM1_PREFLIGHT_TOLERANCE)
AEM1_CONFIG_READY = bool(AEM1_CONFIG_CONFIRMADA) and AEM1_PREFLIGHT_MATCH
print("Desviación máxima frente al preflight:", max(AEM1_PREFLIGHT_DEVIATION.values()), "(tolerancia", AEM1_PREFLIGHT_TOLERANCE, ")")
if AEM1_CONFIG_READY:
    print("CONFIGURACIÓN CONFIRMADA por", AEM1_CONFIG_CONFIRMED_BY)
    print("Los píxeles evaluados son los mismos que se auditaron. Continúa: no hay nada que marcar.")
elif not AEM1_PREFLIGHT_MATCH:
    print("PENDIENTE: la foto decodificada no coincide con la evidencia del preflight:", AEM1_PREFLIGHT_DEVIATION)
    print("No sigas: adjunta esta salida en el chat para revisarla.")
else:
    print("PENDIENTE: la confirmación está desmarcada. Si no sabes por qué, vuelve a marcarla o adjunta esta salida en el chat.")
'''

PHOTO_OLD = '''# Buscar una copia ya cargada; si no existe, pedirla una sola vez.
image_candidates = [
    Path("/mnt/data/P1070614.JPG"),
    Path("/content/P1070614.JPG"),
    WORK_DIR / "P1070614.JPG",
]
IMAGE_PATH = next(
    (p for p in image_candidates if p.exists() and sha256_file(p) == EXPECTED_IMAGE_SHA256),
    None,
)
if IMAGE_PATH is None:
'''
PHOTO_NEW = '''# v1.2 · Buscar la foto por contenido y con cualquier nombre antes de pedirla: basta con arrastrarla
# al panel Archivos (/content) antes de «Ejecutar todas». PRAGMA_HEADLESS=1 = Colab CLI, sin navegador.
import os
PRAGMA_HEADLESS = os.environ.get("PRAGMA_HEADLESS") == "1"
EXPECTED_IMAGE_BYTES = 4260352

def find_acceptance_image(folders):
    for folder in map(Path, folders):
        if not folder.is_dir():
            continue
        for path in sorted(folder.iterdir()):
            if (path.is_file() and path.suffix.lower() in (".jpg", ".jpeg")
                    and path.stat().st_size == EXPECTED_IMAGE_BYTES
                    and sha256_file(path) == EXPECTED_IMAGE_SHA256):
                return path
    return None

IMAGE_PATH = find_acceptance_image([Path("/content"), Path("/mnt/data"), WORK_DIR])
if IMAGE_PATH is not None:
    print(f"Foto encontrada por su huella SHA-256: {IMAGE_PATH}")
elif PRAGMA_HEADLESS:
    raise FileNotFoundError("Modo sin navegador: sube antes la foto a /content (por ejemplo con colab upload).")
else:
'''

GENERATE_CHANGES = [
    ("def generate_aem1(protocol, prompts=None, box=None, mask_input=None, multimask_output=True,\n"
     "                 parent_proposal_id=None, seed_candidate_index=None):",
     "def generate_aem1(protocol, prompts=None, box=None, mask_input=None, multimask_output=True,\n"
     "                 parent_proposal_id=None, seed_candidate_index=None, key=None):\n"
     "    key = key or protocol  # v1.2: varias semillas del mismo protocolo conviven como claves distintas"),
    ("        proposal_id=f\"aem1_{protocol.replace('+','_')}_{uuid.uuid4().hex[:8]}\",",
     "        proposal_id=f\"aem1_{key.replace('+','_').replace(':','_')}_{uuid.uuid4().hex[:8]}\","),
    ("    AEM1_PROPOSALS[protocol] = proposal\n"
     "    print(f\"{protocol}: {len(proposal.masks)} candidata(s) · inferencia {proposal.inference_s:.4f} s\")",
     "    AEM1_PROPOSALS[key] = proposal\n"
     "    print(f\"{key}: {len(proposal.masks)} candidata(s) · inferencia {proposal.inference_s:.4f} s\")"),
    ('fig.savefig(gallery_path, dpi=165, bbox_inches="tight")',
     'fig.savefig(gallery_path, dpi=90, bbox_inches="tight")'),
]

OVERLAY_DPI = [('fig.savefig(CONFIG_OVERLAY_PATH, dpi=160, bbox_inches="tight")',
                'fig.savefig(CONFIG_OVERLAY_PATH, dpi=90, bbox_inches="tight")')]

CORRECTIONS_MD = """## 8. Correcciones iterativas reales (v1.2: todas las semillas)

Cada corrección reutiliza los logits 256×256 de una semilla mediante `mask_input` y usa `multimask_output=False`, como permite la API oficial para prompts múltiples menos ambiguos. **En v1.2 no hay que elegir semillas:** por defecto se corrigen las tres candidatas de `point` y las tres de `box` (6 propuestas más), y la mejor se elige por contenido en la auditoría externa. Si alguna vez quieres el modo manual, pon los dos índices y marca `AEM1_SEEDS_CONFIRMADAS`.
"""

CORRECTIONS_CODE = '''AEM1_POINT_SEED_INDEX = -1 # @param {type:"integer"}
AEM1_BOX_SEED_INDEX = -1 # @param {type:"integer"}
AEM1_SEEDS_CONFIRMADAS = False # @param {type:"boolean"}

# v1.2 · Sin tocar nada: modo exhaustivo (las tres semillas de cada baseline). Nadie elige a ciegas.
# Invariante: cada corrección usa multimask_output=False sobre los logits de su semilla.
AEM1_PROTOCOLS_COMPLETE = False
AEM1_SEED_MODE = "manual" if AEM1_SEEDS_CONFIRMADAS else "exhaustive"
if not AEM1_CONFIG_READY or not {"point", "box"}.issubset(AEM1_PROPOSALS):
    print("PENDIENTE: ejecuta primero los baselines.")
else:
    if AEM1_SEED_MODE == "manual":
        seed_plan = {"point": [AEM1_POINT_SEED_INDEX], "box": [AEM1_BOX_SEED_INDEX]}
    else:
        seed_plan = {base: list(range(len(AEM1_PROPOSALS[base].masks))) for base in ("point", "box")}
    invalid_seeds = [(base, seed) for base, seeds in seed_plan.items() for seed in seeds
                     if seed not in range(len(AEM1_PROPOSALS[base].masks))]
    if invalid_seeds:
        print("PENDIENTE: cada semilla debe ser 0, 1 o 2. Valores inválidos:", invalid_seeds)
    else:
        invalidate_aem1_review("Se regeneraron las correcciones; la revisión final debe rehacerse.")
        for stale_key in [k for k in AEM1_PROPOSALS if "+corrections" in k]:
            AEM1_PROPOSALS.pop(stale_key)
        expected_keys = {"point", "box"}
        for base in ("point", "box"):
            bundle = pipeline.selector.select(image, f"{base}+corrections", pipeline.detections)
            for seed in seed_plan[base]:
                key = bundle.protocol if AEM1_SEED_MODE == "manual" else f"{bundle.protocol}:s{seed}"
                generate_aem1(
                    bundle.protocol,
                    prompts=bundle.prompts,
                    box=bundle.box_xyxy,
                    mask_input=AEM1_PROPOSALS[base].low_res_logits[seed][None, :, :],
                    multimask_output=False,
                    parent_proposal_id=AEM1_PROPOSALS[base].proposal_id,
                    seed_candidate_index=seed,
                    key=key,
                )
                expected_keys.add(key)
        AEM1_PROTOCOLS_COMPLETE = set(AEM1_PROPOSALS) == expected_keys
        assert AEM1_PROTOCOLS_COMPLETE
        print(f"PROTOCOLO FIJO COMPLETO ({AEM1_SEED_MODE}): {len(AEM1_PROPOSALS)} propuestas registradas.")
'''

REVIEW_CHANGES = [
    ('AEM1_SELECTED_PROTOCOL = "none" # @param ["none", "point", "box", "point+corrections", "box+corrections"]',
     'AEM1_SELECTED_PROTOCOL = "none" # @param ["none", "point", "box", "point+corrections:s0", "point+corrections:s1", "point+corrections:s2", "box+corrections:s0", "box+corrections:s1", "box+corrections:s2", "point+corrections", "box+corrections"]'),
    ('elif AEM1_SELECTED_PROTOCOL == "none":\n    print("PENDIENTE: selecciona un protocolo y una candidata tras mirar las galerías.")',
     'elif AEM1_SELECTED_PROTOCOL == "none":\n'
     '    AEM1_CASE_STATUS = "PENDING_EXTERNAL_AUDIT"\n'
     '    print("REVISIÓN DELEGADA AL AUDITOR IA: no tienes que elegir ni marcar nada.")\n'
     '    print("La sección 10 empaqueta todas las candidatas; adjunta el ZIP en el chat.")'),
    ('Devuelve el ZIP a Codex para agotar la revisión.', 'Adjunta el ZIP en el chat para agotar la revisión.'),
]

REVIEW_MD = """## 9. Revisión (v1.2: la hace el auditor IA fuera de Colab)

Con los valores por defecto (`AEM1_SELECTED_PROTOCOL = "none"`) esta celda **no pide nada**: deja el caso en `PENDING_EXTERNAL_AUDIT` y la sección 10 empaqueta todas las candidatas con sus hashes. El auditor IA elige por contenido, revisa a resolución completa y registra el veredicto con evidencia.

Revisión manual opcional (solo si quieres hacerla tú): elige protocolo y candidata, ejecuta, copia el `selection_id`, marca los criterios que sean verdad y vuelve a ejecutar. Si algún criterio es falso, las notas son obligatorias.
"""

EXPORT_CHANGES = [
    ('elif not SELECTION_BINDING_VALID:\n    AEM1_CASE_STATUS = "PENDING_STALE_SELECTION"\n',
     'elif not SELECTION_BINDING_VALID:\n    AEM1_CASE_STATUS = "PENDING_STALE_SELECTION"\n'
     'elif AEM1_SELECTION is None:\n    AEM1_CASE_STATUS = "PENDING_EXTERNAL_AUDIT"\n'),
    ('    "protocols_complete": bool(AEM1_PROTOCOLS_COMPLETE),\n',
     '    "protocols_complete": bool(AEM1_PROTOCOLS_COMPLETE),\n'
     '    "seed_mode": AEM1_SEED_MODE,\n'
     '    "review_mode": "external_ai_audit" if AEM1_SELECTION is None else "in_notebook_human",\n'
     '    "preflight_match": {"match": bool(AEM1_PREFLIGHT_MATCH), "deviation": AEM1_PREFLIGHT_DEVIATION},\n'),
    ('        "meaning": "Una salida fallida no agota las demás candidatas; Codex debe revisar el bundle antes de atribuir FAIL al caso.",\n',
     '        "meaning": "Una salida fallida no agota las demás candidatas; el auditor revisa todas las del bundle antes de atribuir FAIL al caso.",\n'),
    ('''if AEM1_DOWNLOAD_ZIP and not AEM1_CASE_STATUS.startswith("PENDING"):
    files.download(str(ZIP_PATH))
elif AEM1_DOWNLOAD_ZIP:
    print("ZIP PENDING guardado, pero no se descarga automáticamente hasta completar la revisión y las notas.")''',
     '''AEM1_ZIP_READY_TO_SHARE = (not AEM1_CASE_STATUS.startswith("PENDING")) or AEM1_CASE_STATUS == "PENDING_EXTERNAL_AUDIT"
if globals().get("PRAGMA_HEADLESS", False):
    print("Modo sin navegador: descarga el ZIP con colab download:", ZIP_PATH)
elif AEM1_DOWNLOAD_ZIP and AEM1_ZIP_READY_TO_SHARE:
    try:
        files.download(str(ZIP_PATH))
        print("Descarga iniciada. Adjunta este ZIP en el chat:", ZIP_PATH.name)
    except Exception as exc:  # la descarga depende del navegador; el ZIP ya quedó escrito y verificado
        print("La descarga automática falló:", exc)
        print("Descárgalo desde el panel Archivos:", ZIP_PATH)
elif AEM1_DOWNLOAD_ZIP:
    print("ZIP PENDING guardado, pero no se descarga automáticamente hasta completar la revisión y las notas.")'''),
]

INTERPRETATION_ADD = """
- `PENDING_EXTERNAL_AUDIT` (v1.2, el normal): el cuaderno terminó bien y el ZIP contiene todas las candidatas. Falta la auditoría externa (IA, con evidencia y hashes), que decide entre `SEPARATION_DEMONSTRATED_UNDER_FIXED_AEM1_PROTOCOL` e `INCONCLUSIVE_SELECTED_OUTPUT_FAILED`. No es un fallo.
"""


def replace_once(text, old, new, where):
    if text.count(old) != 1:
        raise RuntimeError(f"{where}: se esperaba exactamente 1 aparición de {old[:70]!r}, hay {text.count(old)}")
    return text.replace(old, new)


def set_source(cell, text):
    cell["source"] = text.splitlines(True)


def main():
    raw = SOURCE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise RuntimeError("El cuaderno v1.1 no coincide con el hash esperado; no se construye v1.2")
    nb = json.loads(raw.decode("utf-8"))
    cells = {cell["id"]: cell for cell in nb["cells"]}
    text = {cid: "".join(cell["source"]) for cid, cell in cells.items()}

    title = replace_once(text["pragma-aem1-00"], TITLE_OLD, TITLE_NEW, "00")
    first_note = title.index("\n> **v1.1")
    title = title[:first_note] + TITLE_NOTE + title[first_note:]
    set_source(cells["pragma-aem1-00"], title)
    set_source(cells["pragma-aem1-01"], HOWTO_NEW)

    photo = replace_once(text["pragma-aem1-03"], PHOTO_OLD, PHOTO_NEW, "03")
    set_source(cells["pragma-aem1-03"], photo)

    config = text["pragma-aem1-06"]
    for old, new in COORDINATE_CHANGES + [(CONFIRMATION_OLD, CONFIRMATION_NEW), (REVISION_OLD, REVISION_NEW),
                                          (READY_OLD, READY_NEW)] + OVERLAY_DPI:
        config = replace_once(config, old, new, "06")
    set_source(cells["pragma-aem1-06"], config)

    section5 = text["pragma-aem1-06m"].rstrip("\n") + (
        "\n\n**v1.2:** la configuración llega confirmada por el auditor IA (18/18 puntos en su región) y la celda "
        "comprueba sola que la foto es la auditada, comparando la luminancia de cada parche con la del preflight. "
        "No hay nada que marcar.\n")
    set_source(cells["pragma-aem1-06m"], section5)

    generate = text["pragma-aem1-07"]
    for old, new in GENERATE_CHANGES:
        generate = replace_once(generate, old, new, "07")
    set_source(cells["pragma-aem1-07"], generate)

    set_source(cells["pragma-aem1-09m"], CORRECTIONS_MD)
    set_source(cells["pragma-aem1-09"], CORRECTIONS_CODE)

    set_source(cells["pragma-aem1-10m"], REVIEW_MD)
    review = text["pragma-aem1-10"]
    for old, new in REVIEW_CHANGES:
        review = replace_once(review, old, new, "10")
    set_source(cells["pragma-aem1-10"], review)

    export = text["pragma-aem1-11"]
    for old, new in EXPORT_CHANGES:
        export = replace_once(export, old, new, "11")
    set_source(cells["pragma-aem1-11"], export)

    interpretation = replace_once(
        text["pragma-aem1-12"],
        "\nEn todos los casos, el siguiente paso correcto",
        INTERPRETATION_ADD + "\nEn todos los casos, el siguiente paso correcto",
        "12",
    )
    set_source(cells["pragma-aem1-12"], interpretation)

    # Misma serialización que los constructores v1.0 y v1.1 (compacta, UTF-8).
    OUT.write_text(json.dumps(nb, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(json.dumps({"out": str(OUT.relative_to(ROOT)), "sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
                      "bytes": OUT.stat().st_size}, indent=2))


if __name__ == "__main__":
    main()
