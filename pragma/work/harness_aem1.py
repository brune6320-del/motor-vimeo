"""Arnés de punta a punta para cuadernos A-E(−1) con SAM, torch y google.colab SIMULADOS.

Ejecuta las celdas 03–11 del cuaderno real, en orden, con la foto de aceptación real. Solo se
sustituyen las dependencias que exigen GPU, red o navegador:

- ``torch``: CPU, sin CUDA (el cuaderno elige float32, como haría en CPU);
- ``sam2``: un predictor falso que devuelve máscaras geométricas deterministas con la misma forma
  (N×H×W logits, N scores, N×256×256 logits de baja resolución) que ``SAM2ImagePredictor.predict``;
- ``google.colab.files``: registra las descargas y falla si se intenta abrir un selector de archivos.

Lo que prueba: el flujo de control, los estados, el registro de propuestas, las evidencias, el
informe, el manifiesto y el ZIP. Lo que NO prueba: la calidad de SAM 2 (eso exige la GPU).
La celda 02 (instalación por red) no se ejecuta; sus variables se definen en el preludio.
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import sys
import types
from pathlib import Path

import numpy as np

CELL_ORDER = ["pragma-aem1-03", "pragma-aem1-04", "pragma-aem1-05", "pragma-aem1-06", "pragma-aem1-07",
              "pragma-aem1-08", "pragma-aem1-09", "pragma-aem1-10", "pragma-aem1-11"]


class UploadAttempted(AssertionError):
    """El cuaderno intentó abrir el selector de archivos del navegador."""


class FakeModel:
    def parameters(self):
        return [types.SimpleNamespace(numel=lambda: 1)]


class FakePredictor:
    """Máscaras deterministas: disco/elipse según prompt, menos discos alrededor de los negativos."""

    def __init__(self, model):
        self.shape = None

    def set_image(self, image):
        self.shape = np.asarray(image).shape[:2]

    def predict(self, point_coords=None, point_labels=None, box=None, mask_input=None,
                multimask_output=True, return_logits=False):
        assert self.shape is not None, "predict antes de set_image"
        h, w = self.shape
        yy, xx = np.ogrid[:h, :w]
        n = 3 if multimask_output else 1
        if mask_input is not None:
            assert np.asarray(mask_input).shape == (1, 256, 256), np.asarray(mask_input).shape
        masks = []
        for index in range(n):
            if box is not None:
                x1, y1, x2, y2 = np.asarray(box, np.float32).reshape(4)
                cx, cy, rx, ry = (x1 + x2) / 2, (y1 + y2) / 2, (x2 - x1) / 2 * (0.75 + 0.1 * index), (y2 - y1) / 2 * 0.9
                mask = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0
            else:
                points = np.asarray(point_coords, np.float32).reshape(-1, 2)
                labels = np.asarray(point_labels).reshape(-1)
                cx, cy = points[labels == 1][0]
                radius = (150, 480, 820)[index] if n == 3 else 700
                mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius ** 2
            if point_coords is not None:
                points = np.asarray(point_coords, np.float32).reshape(-1, 2)
                labels = np.asarray(point_labels).reshape(-1)
                for (px, py), label in zip(points, labels):
                    if label == 0:
                        mask &= (xx - px) ** 2 + (yy - py) ** 2 > 110 ** 2
            masks.append(mask)
        logits = np.where(np.stack(masks), 6.0, -6.0).astype(np.float32)
        low_res = logits[:, :: max(1, h // 256), :: max(1, w // 256)][:, :256, :256]
        low_res = np.pad(low_res, ((0, 0), (0, 256 - low_res.shape[1]), (0, 256 - low_res.shape[2])), constant_values=-6.0)
        scores = np.asarray([0.91, 0.55, 0.73][:n], np.float32)
        return logits, scores, low_res


def stub_modules(download_log: list):
    torch = types.ModuleType("torch")
    torch.__version__ = "SIMULATED"
    torch.float16, torch.bfloat16, torch.float32 = "float16", "bfloat16", "float32"
    torch.cuda = types.SimpleNamespace(
        is_available=lambda: False,
        get_device_capability=lambda index=0: (0, 0),
        get_device_name=lambda index=0: "SIMULATED",
        OutOfMemoryError=type("OutOfMemoryError", (RuntimeError,), {}),
        max_memory_allocated=lambda: 0,
        reset_peak_memory_stats=lambda: None,
        synchronize=lambda: None,
        empty_cache=lambda: None,
    )
    torch.inference_mode = contextlib.nullcontext
    torch.autocast = lambda **kwargs: contextlib.nullcontext()

    def upload():
        raise UploadAttempted("files.upload() llamado: el cuaderno pidió el selector del navegador")

    colab = types.ModuleType("google.colab")
    colab.files = types.SimpleNamespace(upload=upload, download=lambda path: download_log.append(str(path)))
    colab.output = types.SimpleNamespace()
    google = types.ModuleType("google")
    google.colab = colab

    sam2 = types.ModuleType("sam2")
    sam2.__file__ = "<SIMULATED sam2>"
    build = types.ModuleType("sam2.build_sam")
    build.build_sam2 = lambda cfg, checkpoint, device="cpu": FakeModel()
    predictor = types.ModuleType("sam2.sam2_image_predictor")
    predictor.SAM2ImagePredictor = FakePredictor
    return {"torch": torch, "google": google, "google.colab": colab, "sam2": sam2,
            "sam2.build_sam": build, "sam2.sam2_image_predictor": predictor}


def run(notebook_path, workdir, image_path=None, headless=False, cells=CELL_ORDER, image_name="foto_renombrada.jpg"):
    """Ejecuta las celdas indicadas. Devuelve (namespace, descargas, excepción o None)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    nb = json.loads(Path(notebook_path).read_text(encoding="utf-8"))
    sources = {c["id"]: "".join(c["source"]) for c in nb["cells"]}
    workdir = Path(workdir)
    if workdir.exists():
        shutil.rmtree(workdir)
    work = workdir / "pragma_run"
    (work / "checkpoints").mkdir(parents=True)
    checkpoint = work / "checkpoints" / "sam2.1_hiera_large.pt"
    checkpoint.write_bytes(b"SIMULATED CHECKPOINT - NOT SAM 2 WEIGHTS\n")
    if image_path is not None:
        shutil.copyfile(image_path, work / image_name)   # nombre distinto: prueba la búsqueda por hash

    downloads: list = []
    saved_modules = {name: sys.modules.get(name) for name in stub_modules([])}
    sys.modules.update(stub_modules(downloads))
    saved_env = os.environ.get("PRAGMA_HEADLESS")
    if headless:
        os.environ["PRAGMA_HEADLESS"] = "1"
    else:
        os.environ.pop("PRAGMA_HEADLESS", None)
    original_show = plt.show
    plt.show = lambda *args, **kwargs: plt.close("all")
    namespace = {
        "__name__": "aem1_e2e_harness", "os": os, "sys": sys, "Path": Path,
        "REPO_DIR": workdir / "sam2_repo", "WORK_DIR": work, "CHECKPOINT_DIR": work / "checkpoints",
        "CHECKPOINT": checkpoint, "CHECKPOINT_URL": "SIMULATED", "MODEL_CFG": "configs/sam2.1/sam2.1_hiera_l.yaml",
        "SAM2_COMMIT": "SIMULATED", "run_checked": lambda *args, **kwargs: None,
    }
    error = None
    try:
        for cell_id in cells:
            # dont_inherit: las celdas no deben heredar los `from __future__` de este módulo (como en Colab).
            exec(compile(sources[cell_id], cell_id, "exec", dont_inherit=True), namespace)
    except BaseException as exc:  # el llamador decide si el error era el esperado
        error = exc
    finally:
        plt.show = original_show
        plt.close("all")
        for name, module in saved_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
        if saved_env is None:
            os.environ.pop("PRAGMA_HEADLESS", None)
        else:
            os.environ["PRAGMA_HEADLESS"] = saved_env
    return namespace, downloads, error
