"""Construye el cuaderno A‑E1 etapa 1 desde el protocolo de lectura, sin editar a mano ninguna celda.

    python3 work/build_pragma_ae1_stage1.py

El protocolo ya liga por hash el contrato A‑E1, el sweep y A‑E0. Del cuaderno v1.3 se reutilizan, tal
cual, dos celdas: la instalación (SAM 2 en el commit congelado y checkpoint por SHA‑256) y el entorno
(la foto se reconoce por su hash). Solo cambia la carpeta de corridas.

Las celdas nuevas son:
- el protocolo embebido byte a byte;
- el modelo sin postprocesado;
- las 4 llamadas AMG del plan, con ``points_per_batch`` que solo baja por OOM;
- el ZIP con manifiesto.

**No muestra máscaras, número de máscaras ni scores.**
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "work"))

import build_pragma_aem1_v1_3 as v13  # noqa: E402

PROTOCOL = ROOT / "ae1" / "AE1_STAGE1_READING_PROTOCOL.json"
OUT = ROOT / "outputs" / "PRAGMA_A-E1_etapa1_SAM2_AMG.ipynb"

INTRO = """
# PRAGMA · A‑E1 etapa 1 — SAM 2 automático (4 configuraciones) · un clic

> **No tienes que decidir ni mirar nada.** Arrastra la foto `P1070614.JPG` al panel **Archivos**
> (icono de carpeta, a la izquierda) y pulsa **Entorno de ejecución → Ejecutar todas**. Al final se
> descarga un ZIP: **adjúntalo solo a Claude**.

Qué hace, sin intervención:

1. Instala SAM 2 **en el commit exacto** `2b90b9f5` y descarga SAM 2.1 Large. **Se detiene** si el
   commit o el checkpoint no son los congelados.
2. Encuentra la foto por su huella SHA‑256.
3. Ejecuta las **4 configuraciones** del generador automático de máscaras prerregistradas
   (AMG‑0 a AMG‑3), en orden, con los parámetros exactos del protocolo.
4. Empaqueta todas las máscaras con un manifiesto de hashes en
   `PRAGMA_AE1S1_<run>_PENDING_ANALYSIS.zip`.

**Por qué no enseña resultados:** el análisis es externo y está fijado antes de la corrida. Parte de
él es una revisión ciega a doble llave. No compartas capturas de este cuaderno con ChatGPT ni con nadie.

Protocolo: `ae1/AE1_STAGE1_READING_PROTOCOL.json` (SHA‑256 del archivo `{protocol_sha}`;
`content_sha256` `{content_sha}`). Techo de esta etapa: `INCONCLUSIVE_GT_INCOMPLETE`, nunca un PASS.
"""

HOWTO = """
## 0. Antes de pulsar «Ejecutar todas»

1. **Entorno de ejecución → Cambiar tipo de entorno de ejecución → GPU → L4.** Usa **L4**, como en
   las corridas anteriores.
2. Arrastra `P1070614.JPG` al panel **Archivos**. Si no lo haces, la celda 2 te pedirá la foto con
   un botón **Elegir archivos**. El nombre no importa: se reconoce por su huella.
3. **Entorno de ejecución → Ejecutar todas.** Tarda unos minutos: instalar SAM 2, descargar 857 MiB y
   generar las máscaras de las 4 configuraciones. Al terminar, el navegador descarga el ZIP.

Si aparece un error en rojo, copia el texto y pégalo a Claude. No cambies nada del cuaderno.
"""

CELL_PROTOCOL = '''
# Celda 3 · protocolo de lectura embebido (no editar): plan de las 4 llamadas y congelados
PROTOCOL_FILE_SHA256 = "@@PROTOCOL_SHA@@"
PROTOCOL_TEXT = @@PROTOCOL_LITERAL@@
assert hashlib.sha256(PROTOCOL_TEXT.encode("utf-8")).hexdigest() == PROTOCOL_FILE_SHA256, "Protocolo alterado"
PROTOCOL = json.loads(PROTOCOL_TEXT)
assert PROTOCOL["status"] == "PREREGISTERED", "El protocolo no está prerregistrado"
CALL_PLAN = PROTOCOL["call_plan"]
assert [c["call_id"] for c in CALL_PLAN] == ["AMG-0", "AMG-1", "AMG-2", "AMG-3"]
FREEZE = PROTOCOL["freeze"]
assert FREEZE["SAM2_GIT_COMMIT"] == "2b90b9f5ceec907a1c18123530e92e794ad901a4"
assert FREEZE["CHECKPOINT_SHA256"] == "2647878d5dfa5098f2f8649825738a9345572bae2d4350a2468587ece47dd318"
assert FREEZE["IMAGE_SHA256"] == EXPECTED_IMAGE_SHA256
print("Protocolo verificado:", PROTOCOL["content_sha256"][:12], "…", "·", len(CALL_PLAN), "configuraciones")
'''

CELL_MODEL = '''
# Celda 4 · modelo sin postprocesado, como el ejemplo oficial de AMG en el commit congelado
from sam2.build_sam import build_sam2
from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator

t0 = time.perf_counter()
try:
    sam2_model = build_sam2(MODEL_CFG, str(CHECKPOINT), device=DEVICE, apply_postprocessing=False)
    synchronize()
except torch.cuda.OutOfMemoryError as exc:
    raise RuntimeError("FAIL_ENVIRONMENT: Large no cabe; usa L4 o A100. No se degrada a Small.") from exc
MODEL_LOAD_S = time.perf_counter() - t0
print(f"Modelo listo en {MODEL_LOAD_S:.1f} s")
'''

CELL_RUN = '''
# Celda 5 · las 4 configuraciones del protocolo, en orden. Solo se imprime el progreso.
def rle_to_mask(rle):
    h, w = (int(v) for v in rle["size"])
    counts = np.asarray(rle["counts"], dtype=np.int64)
    values = np.zeros(counts.size, dtype=bool)
    values[1::2] = True
    flat = np.repeat(values, counts)
    assert flat.size == h * w, "RLE incoherente"
    return flat.reshape(w, h).T

def packed_sha256(mask):
    header = f"{mask.shape[0]}x{mask.shape[1]}:".encode()
    return hashlib.sha256(header + np.packbits(mask).tobytes()).hexdigest()

EXECUTED, RESULTS, MASK_HASHES = [], {}, {}
t_run = time.perf_counter()
for number, call in enumerate(CALL_PLAN, 1):
    attempts, anns = [], None
    for ppb in call["points_per_batch_fallback"]:      # solo baja por OOM (regla del sweep)
        attempts.append(ppb)
        generator = SAM2AutomaticMaskGenerator(sam2_model, **dict(call["generator_kwargs"], points_per_batch=ppb))
        try:
            synchronize(); start = time.perf_counter()
            with torch.inference_mode(), inference_precision():
                anns = generator.generate(image)
            synchronize(); seconds = time.perf_counter() - start
            break
        except torch.cuda.OutOfMemoryError:
            del generator
            if DEVICE == "cuda":
                torch.cuda.empty_cache()
            print(f"{call['call_id']}: sin memoria con points_per_batch={ppb}; se registra y se baja")
    if anns is None:
        raise RuntimeError(f"FAIL_ENVIRONMENT: {call['call_id']} no cabe ni con points_per_batch=16")
    masks = []
    for ann in anns:
        mask = rle_to_mask(ann["segmentation"])
        assert mask.shape == (2248, 4000), mask.shape
        masks.append({"rle": ann["segmentation"], "packed_sha256": packed_sha256(mask), "area": int(ann["area"]),
                      "bbox_xywh": [float(v) for v in ann["bbox"]], "predicted_iou": float(ann["predicted_iou"]),
                      "stability_score": float(ann["stability_score"]), "point_coords": ann["point_coords"],
                      "crop_box_xywh": [float(v) for v in ann["crop_box"]]})
    RESULTS[call["call_id"]] = masks
    MASK_HASHES[call["call_id"]] = [m["packed_sha256"] for m in masks]
    EXECUTED.append({"call_id": call["call_id"], "config_id": call["config_id"],
                     "generator_kwargs": dict(call["generator_kwargs"], points_per_batch=attempts[-1]),
                     "points_per_batch_attempts": attempts, "seconds": round(seconds, 3), "n_masks": len(masks)})
    print(f"configuración {number}/{len(CALL_PLAN)} hecha")
RUN_S = time.perf_counter() - t_run
print(f"Hecho en {RUN_S:.1f} s. No se muestran resultados: el análisis es externo y prerregistrado.")
'''

CELL_ZIP = '''
# Celda 6 · manifiesto, ZIP y descarga
def write_json(path, payload, compact=False):
    text = json.dumps(payload, separators=(",", ":")) if compact else json.dumps(payload, indent=2, ensure_ascii=False)
    path.write_text(text + "\\n", encoding="utf-8")
    return path

(RUN_DIR / "masks").mkdir(exist_ok=True)
for call_id, masks in RESULTS.items():
    write_json(RUN_DIR / "masks" / f"{call_id}.json", {"call_id": call_id, "size": [2248, 4000], "masks": masks}, compact=True)
write_json(RUN_DIR / "ae1s1_config.json", {
    "notebook_version": "ae1s1-1.0", "run_id": RUN_ID, "protocol_file_sha256": PROTOCOL_FILE_SHA256,
    "protocol_content_sha256": PROTOCOL["content_sha256"], "environment": ENVIRONMENT,
    "gates": {"sam2_commit": "verificado en la celda 1", "checkpoint": "verificado en la celda 1",
              "image_sha256": "verificado en la celda 2", "protocol": "verificado en la celda 3"},
})
write_json(RUN_DIR / "ae1s1_calls.json", EXECUTED)
write_json(RUN_DIR / "ae1s1_report.json", {
    "run_id": RUN_ID, "status": "PENDING_ANALYSIS", "environment": ENVIRONMENT,
    "timings_s": {"model_load": round(MODEL_LOAD_S, 3), "run": round(RUN_S, 3)},
    "gpu_peak_gib": round(torch.cuda.max_memory_allocated() / 2**30, 3) if DEVICE == "cuda" else None,
    "note": "sin revisión en Colab: análisis externo según ae1/AE1_STAGE1_READING_PROTOCOL.json",
})
files_listed = sorted(p for p in RUN_DIR.rglob("*") if p.is_file() and p.suffix.lower() not in (".jpg", ".jpeg")
                      and p.name != "ae1s1_manifest.json")
manifest = {"run_id": RUN_ID, "files": {p.relative_to(RUN_DIR).as_posix(): {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
                                        for p in files_listed},
            "masks": MASK_HASHES, "mask_hash": "sha256(«HxW:» + np.packbits(mask)), como pragma_ae.masks.packed_sha256"}
write_json(RUN_DIR / "ae1s1_manifest.json", manifest)
ZIP_PATH = WORK_DIR / f"PRAGMA_AE1S1_{RUN_ID}_PENDING_ANALYSIS.zip"
with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as archive:
    for p in files_listed + [RUN_DIR / "ae1s1_manifest.json"]:
        archive.write(p, p.relative_to(RUN_DIR).as_posix())
with zipfile.ZipFile(ZIP_PATH) as archive:
    assert archive.testzip() is None
ZIP_SHA256 = sha256_file(ZIP_PATH)
print(f"ZIP: {ZIP_PATH.name} · {ZIP_PATH.stat().st_size / 2**20:.1f} MiB · SHA-256 {ZIP_SHA256}")
if not PRAGMA_HEADLESS:
    files.download(str(ZIP_PATH))
print("Adjunta este ZIP solo a Claude. No compartas capturas de esta corrida.")
'''

OUTRO = """
## 7. Qué hacer ahora

1. Busca el ZIP `PRAGMA_AE1S1_…_PENDING_ANALYSIS.zip` en tu carpeta de descargas.
2. **Adjúntalo a Claude** en la sesión de Claude Code. No se lo mandes a ChatGPT.
3. Claude comprueba la integridad sin mirar resultados. Si alguna caja dispara el cribado, prepara
   el paquete ciego: es lo único que recibe ChatGPT, sin carta.
"""


def build() -> dict:
    protocol_bytes = PROTOCOL.read_bytes()
    protocol_text = protocol_bytes.decode("utf-8")
    protocol = json.loads(protocol_text)
    if protocol["status"] != "PREREGISTERED":
        raise SystemExit("El protocolo no está en PREREGISTERED: no se construye el cuaderno")
    protocol_sha = hashlib.sha256(protocol_bytes).hexdigest()
    env = v13.CELL_ENV
    if 'WORK_DIR / "runs_v13"' not in env:
        raise SystemExit("la celda de entorno de v1.3 cambió: revisar el constructor")
    env = env.replace('WORK_DIR / "runs_v13"', 'WORK_DIR / "runs_ae1s1"')
    cells = [
        v13.md("pragma-ae1s1-00", INTRO.replace("{protocol_sha}", protocol_sha).replace("{content_sha}", protocol["content_sha256"])),
        v13.md("pragma-ae1s1-00b", HOWTO),
        v13.code("pragma-ae1s1-01", v13.CELL_INSTALL),
        v13.code("pragma-ae1s1-02", env),
        v13.code("pragma-ae1s1-03", CELL_PROTOCOL.replace("@@PROTOCOL_SHA@@", protocol_sha)
                 .replace("@@PROTOCOL_LITERAL@@", json.dumps(protocol_text, ensure_ascii=False))),
        v13.code("pragma-ae1s1-04", CELL_MODEL),
        v13.code("pragma-ae1s1-05", CELL_RUN),
        v13.code("pragma-ae1s1-06", CELL_ZIP),
        v13.md("pragma-ae1s1-07", OUTRO),
    ]
    return {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"name": OUT.name, "provenance": []},
                                         "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                         "language_info": {"name": "python", "version": "3.x"}},
            "nbformat": 4, "nbformat_minor": 5}


def main():
    notebook = build()
    OUT.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("escrito:", OUT.relative_to(ROOT), "·", hashlib.sha256(OUT.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
