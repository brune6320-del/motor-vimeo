"""Construye el cuaderno A-E(−1) v1.3 a partir del prerregistro (sin editar a mano ninguna celda).

    python3 work/build_pragma_aem1_v1_3.py

El cuaderno ejecuta exactamente ``call_plan`` del prerregistro embebido, verifica antes de generar
el commit de SAM 2, el checkpoint, la foto, el prerregistro y la luma de todos los prompts, y
empaqueta todas las máscaras en un ZIP. **No muestra máscaras, áreas, scores ni sentinelas**: la
auditoría es externa y ciega (protocolo v2 rev. 1).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "aem1" / "PRERREGISTRO_A-E-menos-1_v1_3.json"
OUT = ROOT / "outputs" / "PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_3.ipynb"


def md(cell_id, text):
    return {"cell_type": "markdown", "id": cell_id, "metadata": {}, "source": text.strip("\n").splitlines(True)}


def code(cell_id, text):
    return {"cell_type": "code", "id": cell_id, "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(True)}


INTRO = """
# PRAGMA · A‑E(−1) v1.3 — diagnóstico prerregistrado del caso chica · un clic

> **No tienes que decidir ni mirar nada.** Arrastra la foto `P1070614.JPG` al panel **Archivos**
> (icono de carpeta, a la izquierda) y pulsa **Entorno de ejecución → Ejecutar todas**. Al final se
> descarga un ZIP: **adjúntalo solo a Claude**.

Qué hace, sin intervención:

1. Instala SAM 2 **en el commit exacto** `2b90b9f5` y descarga SAM 2.1 Large. **Se detiene** si el
   commit o el checkpoint no son los congelados.
2. Encuentra la foto por su huella SHA‑256 y **se detiene** si la luma de cualquiera de los prompts
   se desvía más de 3,0 de lo registrado.
3. Ejecuta las **178 llamadas** del prerregistro: BASE, +POS_HAIR, +POS_SLEEVE, +POS_HAIR+SLEEVE,
   recíproco y perturbaciones.
4. Empaqueta las 210 máscaras con un manifiesto de hashes en
   `PRAGMA_AEM1v13_<run>_PENDING_EXTERNAL_AUDIT.zip`.

**Por qué no enseña resultados:** la auditoría es **ciega y a doble llave**. Si Colab mostrara las
máscaras, alguien podría ver o contar un resultado antes de que las dos IAs juzguen a ciegas. No
compartas capturas de este cuaderno con ChatGPT ni con nadie: el paquete ciego lo prepara Claude.

Prerregistro: `aem1/PRERREGISTRO_A-E-menos-1_v1_3.json` (SHA‑256 del archivo `{prereg_sha}`;
`content_sha256` `{content_sha}`). Auditoría: `auditoria/PROTOCOLO_AUDITORIA_AEM1_v2.md` (rev. 1).
"""

HOWTO = """
## 0. Antes de pulsar «Ejecutar todas»

1. **Entorno de ejecución → Cambiar tipo de entorno de ejecución → GPU** (L4 o A100; T4 también
   sirve, pero es más lenta). La corrida 1 usó L4.
2. Arrastra `P1070614.JPG` al panel **Archivos**. Si no lo haces, la celda 2 te pedirá la foto con
   un botón **Elegir archivos**. El nombre no importa: se reconoce por su huella.
3. **Entorno de ejecución → Ejecutar todas.** Tarda unos minutos: la mayor parte es instalar SAM 2
   y descargar 857 MiB. Al terminar, el navegador descarga el ZIP.

Si aparece un error en rojo, copia el texto y pégalo a Claude. No cambies nada del cuaderno.
"""

CELL_INSTALL = '''
# Celda 1 · SAM 2 en el commit congelado y checkpoint verificado (red; en el arnés local se omite)
import hashlib, os, subprocess, sys, urllib.request
from pathlib import Path

SAM2_PINNED_COMMIT = "2b90b9f5ceec907a1c18123530e92e794ad901a4"
CHECKPOINT_SHA256_PINNED = "2647878d5dfa5098f2f8649825738a9345572bae2d4350a2468587ece47dd318"
CHECKPOINT_BYTES_PINNED = 898083611
REPO_DIR = Path("/content/pragma_sam2_2b90b9f5")
WORK_DIR = Path("/content/pragma_run")
CHECKPOINT_DIR = WORK_DIR / "checkpoints"
CHECKPOINT = CHECKPOINT_DIR / "sam2.1_hiera_large.pt"
CHECKPOINT_URL = "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt"
MODEL_CFG = "configs/sam2.1/sam2.1_hiera_l.yaml"
WORK_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

def run_checked(args, **kwargs):
    print("$", " ".join(map(str, args)))
    return subprocess.run(args, check=True, text=True, **kwargs)

if not (REPO_DIR / ".git").exists():
    # Clon sin blobs y checkout del commit exacto (no «main», que puede moverse).
    run_checked(["git", "clone", "--filter=blob:none", "--no-checkout",
                 "https://github.com/facebookresearch/sam2.git", str(REPO_DIR)])
run_checked(["git", "-C", str(REPO_DIR), "checkout", "--quiet", SAM2_PINNED_COMMIT])
SAM2_COMMIT = subprocess.check_output(["git", "-C", str(REPO_DIR), "rev-parse", "HEAD"], text=True).strip()
if SAM2_COMMIT != SAM2_PINNED_COMMIT:
    raise RuntimeError(f"FAIL_FREEZE: SAM 2 está en {SAM2_COMMIT}, no en {SAM2_PINNED_COMMIT}. No se genera nada.")

install_env = os.environ.copy()
install_env["SAM2_BUILD_CUDA"] = "0"
run_checked([sys.executable, "-m", "pip", "install", "-q", "-e", "."], cwd=REPO_DIR, env=install_env)
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))
import importlib
importlib.invalidate_caches()
import sam2
print("SAM 2 importable:", Path(sam2.__file__).resolve())

def download(url, destination):
    temporary = destination.with_suffix(destination.suffix + ".part")
    def progress(blocks, block_size, total):
        if total > 0 and blocks % 128 == 0:
            print(f"Descarga: {min(100, blocks*block_size*100/total):5.1f}%", end="\\r")
    urllib.request.urlretrieve(url, temporary, reporthook=progress)
    temporary.replace(destination)
    print(f"\\nCheckpoint: {destination.stat().st_size / 2**20:.1f} MiB")

if not CHECKPOINT.exists() or CHECKPOINT.stat().st_size != CHECKPOINT_BYTES_PINNED:
    download(CHECKPOINT_URL, CHECKPOINT)
digest = hashlib.sha256()
with open(CHECKPOINT, "rb") as handle:
    for block in iter(lambda: handle.read(1 << 20), b""):
        digest.update(block)
if CHECKPOINT.stat().st_size != CHECKPOINT_BYTES_PINNED or digest.hexdigest() != CHECKPOINT_SHA256_PINNED:
    raise RuntimeError("FAIL_FREEZE: el checkpoint no es el congelado (bytes o SHA-256). No se genera nada.")
os.chdir(WORK_DIR)
print("Congelado verificado · SAM 2", SAM2_COMMIT, "· checkpoint", CHECKPOINT_SHA256_PINNED[:12], "…")
'''

CELL_ENV = '''
# Celda 2 · hardware, precisión y foto (se reconoce por SHA-256; el nombre puede variar)
EXPECTED_IMAGE_SHA256 = "8f6e3b6f5013265a45c7e89121e3f0a18e3386951e2e75378b28da6d02ec529d"
EXPECTED_IMAGE_BYTES = 4260352
import hashlib, io, json, os, platform, time, uuid, zipfile
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
import torch
from google.colab import files

PRAGMA_HEADLESS = os.environ.get("PRAGMA_HEADLESS") == "1"   # 1 = Colab CLI, sin navegador

def select_precision(cuda_available, capability=None):
    if not cuda_available:
        return {"device": "cpu", "dtype": "float32", "autocast": False}
    native_bf16 = int(capability[0]) >= 8
    return {"device": "cuda", "dtype": "bfloat16" if native_bf16 else "float16", "autocast": True}

CUDA_AVAILABLE = torch.cuda.is_available()
CUDA_CAPABILITY = torch.cuda.get_device_capability(0) if CUDA_AVAILABLE else None
PRECISION = select_precision(CUDA_AVAILABLE, CUDA_CAPABILITY)
DEVICE = PRECISION["device"]
TORCH_DTYPE = {"float16": torch.float16, "bfloat16": torch.bfloat16, "float32": torch.float32}[PRECISION["dtype"]]

def inference_precision():
    return torch.autocast(device_type="cuda", dtype=TORCH_DTYPE) if DEVICE == "cuda" else nullcontext()

def synchronize():
    if DEVICE == "cuda":
        torch.cuda.synchronize()

if DEVICE == "cuda":
    torch.cuda.reset_peak_memory_stats()
    DEVICE_NAME = torch.cuda.get_device_name(0)
else:
    DEVICE_NAME = "CPU"
    print("ADVERTENCIA: sin GPU. La corrida se registrará como REAL_CPU y no será comparable.")

RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
RUN_DIR = WORK_DIR / "runs_v13" / RUN_ID
RUN_DIR.mkdir(parents=True, exist_ok=False)

def sha256_file(path, chunk=1 << 20):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()

def find_acceptance_image(folders):
    for folder in map(Path, folders):
        if not folder.is_dir():
            continue
        for path in sorted(folder.iterdir()):
            if (path.is_file() and path.suffix.lower() in (".jpg", ".jpeg")
                    and path.stat().st_size == EXPECTED_IMAGE_BYTES and sha256_file(path) == EXPECTED_IMAGE_SHA256):
                return path
    return None

IMAGE_PATH = find_acceptance_image([Path("/content"), Path("/mnt/data"), WORK_DIR])
if IMAGE_PATH is not None:
    print(f"Foto encontrada por su huella SHA-256: {IMAGE_PATH}")
elif PRAGMA_HEADLESS:
    raise FileNotFoundError("Modo sin navegador: sube antes la foto a /content.")
else:
    print("Selecciona la foto P1070614.JPG. Se validará por SHA-256; el nombre puede variar.")
    uploaded = files.upload()
    exact = [(n, p) for n, p in uploaded.items() if hashlib.sha256(p).hexdigest() == EXPECTED_IMAGE_SHA256]
    if len(exact) != 1:
        raise ValueError("No se recibió exactamente la fotografía de aceptación.")
    IMAGE_PATH = RUN_DIR / "P1070614.JPG"
    IMAGE_PATH.write_bytes(exact[0][1])

IMAGE_SHA256 = sha256_file(IMAGE_PATH)
assert IMAGE_SHA256 == EXPECTED_IMAGE_SHA256, "La foto no coincide con la aceptación acordada."
image = np.asarray(ImageOps.exif_transpose(Image.open(IMAGE_PATH)).convert("RGB"))
assert image.shape[:2] == (2248, 4000), image.shape
ENVIRONMENT = {
    "python": platform.python_version(), "torch": torch.__version__, "device": DEVICE, "device_name": DEVICE_NAME,
    "cuda_capability": CUDA_CAPABILITY, "dtype": PRECISION["dtype"], "sam2_commit": SAM2_COMMIT,
    "checkpoint_bytes": CHECKPOINT.stat().st_size, "checkpoint_sha256": sha256_file(CHECKPOINT),
    "image_sha256": IMAGE_SHA256, "image_size": [image.shape[1], image.shape[0]], "run_id": RUN_ID,
}
print(json.dumps(ENVIRONMENT, indent=2, ensure_ascii=False))
'''

CELL_PREREG = '''
# Celda 3 · prerregistro embebido (no editar) y compuerta de luma de TODOS los prompts
PREREG_FILE_SHA256 = "{prereg_sha}"
PREREG_TEXT = {prereg_literal}
assert hashlib.sha256(PREREG_TEXT.encode("utf-8")).hexdigest() == PREREG_FILE_SHA256, "Prerregistro alterado"
PREREG = json.loads(PREREG_TEXT)
CALL_PLAN = PREREG["call_plan"]
assert PREREG["status"] == "PREREGISTERED" and len(CALL_PLAN) == PREREG["candidate_counts"]["calls"]

gray = image.astype(np.float32).mean(axis=2)   # misma luma que el preflight: media de canales, parche 13×13

def patch_luma(xy, radius=6):
    x, y = int(xy[0]), int(xy[1])
    return float(gray[max(0, y - radius):y + radius + 1, max(0, x - radius):x + radius + 1].mean())

expected_luma = {{}}
for entry in PREREG["base_config"]["prompts"]:
    expected_luma[tuple(entry["xy"])] = entry["patch_luma_mean"]
for group in PREREG["base_config"]["holdouts"].values():
    for entry in group:
        expected_luma[tuple(entry["xy"])] = entry["patch_luma_mean"]
for entry in PREREG["new_prompts"].values():
    expected_luma[tuple(entry["xy"])] = entry["patch_luma_mean"]
for target in PREREG["branches"]["PERTURB_POINT"]["targets"].values():
    for row in target["perturbations"]:
        expected_luma[tuple(row["xy"])] = row["patch_luma_mean"]
used = {{tuple(p) for call in CALL_PLAN for p in call["points"]}}
missing = sorted(used - set(expected_luma))
if missing:
    raise RuntimeError(f"FAIL_CONFIG: prompts sin luma registrada: {{missing[:5]}}")
deviations = {{xy: abs(patch_luma(xy) - value) for xy, value in expected_luma.items()}}
LUMA_CHECK = {{"points_checked": len(deviations), "max_abs_deviation": round(max(deviations.values()), 3), "tolerance": 3.0}}
if LUMA_CHECK["max_abs_deviation"] > 3.0:
    raise RuntimeError(f"FAIL_CONFIG: la luma se desvía {{LUMA_CHECK['max_abs_deviation']}} > 3,0. No se genera nada.")
print("Prerregistro verificado:", PREREG["content_sha256"][:12], "…", "·", len(CALL_PLAN), "llamadas ·",
      "luma de", LUMA_CHECK["points_checked"], "puntos dentro de 3,0")
'''

CELL_MODEL = '''
# Celda 4 · modelo y un único embedding de la foto (las mismas llamadas que v1.2)
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor

MASK_THRESHOLD = 0.0
t0 = time.perf_counter()
try:
    sam2_model = build_sam2(MODEL_CFG, str(CHECKPOINT), device=DEVICE)
    predictor = SAM2ImagePredictor(sam2_model)
    synchronize()
except torch.cuda.OutOfMemoryError as exc:
    raise RuntimeError("FAIL_ENVIRONMENT: Large no cabe; usa L4 o A100. No se degrada a Small.") from exc
MODEL_LOAD_S = time.perf_counter() - t0

@dataclass
class PromptSet:
    points: np.ndarray
    labels: np.ndarray
    def __post_init__(self):
        self.points = np.asarray(self.points, dtype=np.float32).reshape(-1, 2)
        self.labels = np.asarray(self.labels, dtype=np.int32).reshape(-1)

def generate(prompts=None, box=None, mask_input=None, multimask_output=True):
    synchronize(); start = time.perf_counter()
    with torch.inference_mode(), inference_precision():
        hr_logits, scores, low_res = predictor.predict(
            point_coords=prompts.points if prompts is not None else None,
            point_labels=prompts.labels if prompts is not None else None,
            box=box, mask_input=mask_input, multimask_output=multimask_output, return_logits=True)
    synchronize()
    return (np.asarray(hr_logits, dtype=np.float32) > MASK_THRESHOLD, np.asarray(scores, dtype=np.float32),
            np.asarray(low_res, dtype=np.float32), time.perf_counter() - start)

synchronize(); t0 = time.perf_counter()
with torch.inference_mode(), inference_precision():
    predictor.set_image(image)
synchronize()
EMBEDDING_S = time.perf_counter() - t0
print(f"Modelo listo en {MODEL_LOAD_S:.1f} s · embedding en {EMBEDDING_S:.2f} s")
'''

CELL_RUN = '''
# Celda 5 · las 178 llamadas del prerregistro, en orden. Solo se imprime el progreso.
PNG_BRANCHES = ("BASE", "+POS_HAIR", "+POS_SLEEVE", "+POS_HAIR+SLEEVE", "RECIPROCAL")
LOW_RES, EXECUTED, PNG_MASKS, PACKED, PACKED_SHA = {}, [], {}, {}, {}
t_run = time.perf_counter()
for number, call in enumerate(CALL_PLAN, 1):
    prompts = PromptSet(call["points"], call["labels"]) if call["points"] else None
    box = None if call["box"] is None else np.asarray(call["box"], np.float32)
    mask_input = None
    if call["mask_input_from"] is not None:
        source = call["mask_input_from"]
        mask_input = LOW_RES[source["call_id"]][source["index"]][None, :, :]
    masks, scores, low_res, seconds = generate(prompts, box, mask_input, call["multimask_output"])
    assert masks.shape == (len(call["candidates"]), 2248, 4000), masks.shape
    if call["multimask_output"]:
        LOW_RES[call["call_id"]] = low_res          # solo se reutilizan como semillas
    for cid, mask in zip(call["candidates"], masks):
        packed = np.packbits(mask)
        PACKED_SHA[cid] = hashlib.sha256(packed.tobytes()).hexdigest()
        if cid.split("|", 1)[0] in PNG_BRANCHES:
            PNG_MASKS[cid] = mask
        else:
            PACKED[cid] = packed
    EXECUTED.append({**{k: call[k] for k in ("call_id", "branch", "protocol", "points", "labels", "box",
                                               "mask_input_from", "multimask_output", "candidates")},
                     "scores_never_used": [round(float(s), 6) for s in scores], "inference_s": round(seconds, 4)})
    if number % 20 == 0 or number == len(CALL_PLAN):
        print(f"llamada {number}/{len(CALL_PLAN)}")
RUN_S = time.perf_counter() - t_run
assert len(PACKED_SHA) == PREREG["candidate_counts"]["total_masks"]
print(f"Hecho: {len(PACKED_SHA)} máscaras en {RUN_S:.1f} s. No se muestran: la auditoría es ciega.")
'''

CELL_ZIP = '''
# Celda 6 · manifiesto, ZIP y descarga
def write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
    return path

(RUN_DIR / "masks").mkdir(exist_ok=True)
for cid, mask in PNG_MASKS.items():
    Image.fromarray(mask.astype(np.uint8) * 255).save(RUN_DIR / "masks" / (cid.replace("|", "__") + ".png"))
np.savez_compressed(RUN_DIR / "aem1v13_perturbaciones.npz", __shape__=np.array([2248, 4000]),
                    **{cid.replace("|", "__"): packed for cid, packed in PACKED.items()})
write_json(RUN_DIR / "aem1v13_config.json", {
    "notebook_version": "1.3", "run_id": RUN_ID, "prereg_content_sha256": PREREG["content_sha256"],
    "prereg_file_sha256": PREREG_FILE_SHA256, "prereg": PREREG, "environment": ENVIRONMENT, "luma_check": LUMA_CHECK,
    "gates": {"sam2_commit": "verificado en la celda 1", "checkpoint": "verificado en la celda 1",
              "image_sha256": "verificado en la celda 2", "prereg": "verificado en la celda 3", "luma": LUMA_CHECK},
})
write_json(RUN_DIR / "aem1v13_calls.json", EXECUTED)
write_json(RUN_DIR / "aem1v13_report.json", {
    "run_id": RUN_ID, "status": "PENDING_EXTERNAL_AUDIT", "environment": ENVIRONMENT,
    "timings_s": {"model_load": round(MODEL_LOAD_S, 3), "embedding": round(EMBEDDING_S, 3), "calls": round(RUN_S, 3)},
    "gpu_peak_gib": round(torch.cuda.max_memory_allocated() / 2**30, 3) if DEVICE == "cuda" else None,
    "counts": {"calls": len(EXECUTED), "masks": len(PACKED_SHA), "png": len(PNG_MASKS), "npz": len(PACKED)},
    "note": "sin revisión en Colab: auditoría ciega externa según auditoria/PROTOCOLO_AUDITORIA_AEM1_v2.md (rev. 1)",
})
files_listed = sorted(p for p in RUN_DIR.rglob("*") if p.is_file() and p.name != "P1070614.JPG"
                      and p.name != "aem1v13_manifest.json")
manifest = {"run_id": RUN_ID, "files": {p.relative_to(RUN_DIR).as_posix(): {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
                                        for p in files_listed},
            "masks": dict(sorted(PACKED_SHA.items())), "mask_hash": "sha256(np.packbits(mask)) sin cabecera"}
write_json(RUN_DIR / "aem1v13_manifest.json", manifest)
ZIP_PATH = WORK_DIR / f"PRAGMA_AEM1v13_{RUN_ID}_PENDING_EXTERNAL_AUDIT.zip"
with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as archive:
    for p in files_listed + [RUN_DIR / "aem1v13_manifest.json"]:
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

1. Busca el ZIP `PRAGMA_AEM1v13_…_PENDING_EXTERNAL_AUDIT.zip` en tu carpeta de descargas.
2. **Adjúntalo a Claude** en la sesión de Claude Code. No se lo mandes a ChatGPT.
3. Claude verifica la integridad sin mirar resultados, prepara el paquete ciego y te lo da. Ese
   paquete es lo único que recibe ChatGPT, sin carta.
"""


def build() -> dict:
    prereg_bytes = PREREG.read_bytes()
    prereg_text = prereg_bytes.decode("utf-8")
    prereg = json.loads(prereg_text)
    if prereg["status"] != "PREREGISTERED":
        raise SystemExit("El prerregistro no está en PREREGISTERED: no se construye el cuaderno")
    prereg_sha = hashlib.sha256(prereg_bytes).hexdigest()
    cells = [
        md("pragma-aem1v13-00", INTRO.replace("{prereg_sha}", prereg_sha).replace("{content_sha}", prereg["content_sha256"])),
        md("pragma-aem1v13-00b", HOWTO),
        code("pragma-aem1v13-01", CELL_INSTALL),
        code("pragma-aem1v13-02", CELL_ENV),
        code("pragma-aem1v13-03", CELL_PREREG.format(prereg_sha=prereg_sha,
                                                     prereg_literal=json.dumps(prereg_text, ensure_ascii=False))),
        code("pragma-aem1v13-04", CELL_MODEL),
        code("pragma-aem1v13-05", CELL_RUN),
        code("pragma-aem1v13-06", CELL_ZIP),
        md("pragma-aem1v13-07", OUTRO),
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
