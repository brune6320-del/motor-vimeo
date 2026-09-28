"""Verificación del cuaderno A‑E1 etapa 1: estática, de punta a punta con AMG simulado y del lector.

    python3 work/verify_pragma_ae1_stage1.py        # necesita la foto (se localiza por SHA‑256) y ae0/gt/

Qué demuestra:
- **El cuaderno:**
  - se detiene antes de instalar nada sin CUDA con capacidad ≥ 8 (bfloat16 nativo), como pidió ChatGPT 020;
  - embebe el protocolo byte a byte y conserva las compuertas de congelado de v1.3;
  - usa ``apply_postprocessing=False``;
  - no muestra resultados.
- **Ejecutado con la foto real, una L4 simulada y un AMG simulado:**
  - hace exactamente las 4 llamadas del plan, con sus kwargs, en bfloat16;
  - ``points_per_batch`` solo baja por OOM y se registra.
- **Su ZIP:**
  - pasa la integridad como ``SIMULATED_RUN_NOT_EVIDENCE``;
  - toda manipulación (una máscara, los kwargs, la regla de ``points_per_batch``, la capacidad CUDA) da
    ``INVALID_BUNDLE``, aunque el manifiesto se rehaga; un registro de GPU en float16 no es evidencia.
- **El lector R1–R4 sobre ese ZIP:**
  - se detiene en R1 si hay disparadores y faltan llaves;
  - dos ``MISS`` en el triaje no confirman nada: escalan a la revisión exhaustiva, que tiene todas las
    propuestas cuya caja corta la del objeto, sin tope y en varias láminas;
  - los paquetes ciegos no revelan la configuración, el score ni el ranking;
  - con las llaves, R2 (cotas por conjunto), R3 (diagnóstico) y R4 funcionan, y nunca dan PASS.

Qué NO demuestra: la calidad de SAM 2. Eso exige la GPU.
"""

from __future__ import annotations

import ast
import hashlib
import json
import shutil
import sys
import types
import zipfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "work"))

import build_pragma_aem1_v1_3 as v13  # noqa: E402
import harness_aem1 as harness  # noqa: E402
from pragma_ae import ae1_stage1 as s1  # noqa: E402
from pragma_ae.imageio import load_rgb, locate_image  # noqa: E402
from pragma_ae.masks import rle_encode  # noqa: E402

NOTEBOOK = ROOT / "outputs" / "PRAGMA_A-E1_etapa1_SAM2_AMG.ipynb"
PROTOCOL = ROOT / "ae1" / "AE1_STAGE1_READING_PROTOCOL.json"
INVENTORY = ROOT / "ae0" / "scene_inventory.json"
GT_DIR = ROOT / "ae0" / "gt"
OUT_JSON = ROOT / "outputs" / "PRAGMA_A-E1_etapa1_verificacion.json"
WORKDIR = ROOT / "local" / "ae1_stage1_harness"
CELLS = ["pragma-ae1s1-00g", "pragma-ae1s1-02", "pragma-ae1s1-03", "pragma-ae1s1-04", "pragma-ae1s1-05",
         "pragma-ae1s1-06"]
MISSED = ("ae0_012", "ae0_029")          # el AMG simulado nunca los propone enteros: dispara R1
FRAGMENTS = 4                            # … solo en trozos (FRAGMENTS × FRAGMENTS), que no los cubren
L4, T4 = ("SIMULATED L4", (8, 9)), ("SIMULATED T4", (7, 5))
H, W = 2248, 4000

checks = []


def check(name, ok, detail=""):
    checks.append({"check": name, "pass": bool(ok), "detail": detail})
    print(("PASS " if ok else "FAIL ") + name + (f" · {detail}" if detail else ""))


# ─── AMG simulado ─────────────────────────────────────────────────────────────────────────────

class FakeAMG:
    """Rectángulos deterministas dentro de las cajas del inventario; nunca propone ``MISSED``."""
    calls, build_kwargs, oom = [], [], set()
    boxes = []
    gpu = L4

    def __init__(self, model, **kwargs):
        self.kwargs = kwargs

    def generate(self, image):
        FakeAMG.calls.append(dict(self.kwargs))
        key = (self.kwargs["points_per_side"], self.kwargs["crop_n_layers"], self.kwargs["pred_iou_thresh"],
               self.kwargs["points_per_batch"])
        if key in FakeAMG.oom:
            FakeAMG.oom.discard(key)
            raise sys.modules["torch"].cuda.OutOfMemoryError("SIMULATED OOM")
        h, w = np.asarray(image).shape[:2]
        shrink = {32: 0.15, 64: 0.08}[self.kwargs["points_per_side"]] + 0.05 * self.kwargs["crop_n_layers"]
        anns = []
        for oid, (x1, y1, x2, y2) in FakeAMG.boxes:
            if oid in MISSED:                                # trozos iguales en las 4 configuraciones
                xs = np.linspace(x1, x2, FRAGMENTS + 1).astype(int)
                ys = np.linspace(y1, y2, FRAGMENTS + 1).astype(int)
                for i in range(FRAGMENTS):
                    for j in range(FRAGMENTS):
                        mask = np.zeros((h, w), bool)
                        mask[ys[j]:ys[j + 1], xs[i]:xs[i + 1]] = True
                        anns.append(self.ann(mask, xs[i], ys[j], xs[i + 1], ys[j + 1]))
                continue
            dx, dy = int((x2 - x1) * shrink / 2), int((y2 - y1) * shrink / 2)
            mask = np.zeros((h, w), bool)
            mask[y1 + dy:y2 - dy, x1 + dx:x2 - dx] = True
            anns.append(self.ann(mask, x1 + dx, y1 + dy, x2 - dx, y2 - dy))
        if self.kwargs["pred_iou_thresh"] < 0.8:            # SENSITIVE: además, fondo
            mask = np.zeros((h, w), bool)
            mask[0:300, 1500:2100] = True
            anns.append(self.ann(mask, 1500, 0, 2100, 300))
        return anns

    @staticmethod
    def ann(mask, x1, y1, x2, y2):
        return {"segmentation": rle_encode(mask), "area": int(mask.sum()), "bbox": [x1, y1, x2 - x1, y2 - y1],
                "predicted_iou": 0.9, "point_coords": [[float((x1 + x2) / 2), float((y1 + y2) / 2)]],
                "stability_score": 0.96, "crop_box": [0, 0, W, H]}


def stub_modules_ae1(download_log):
    modules = original_stub(download_log)
    if FakeAMG.gpu is not None:                              # GPU simulada: solo cambia lo que informa CUDA
        name, capability = FakeAMG.gpu
        modules["torch"].cuda.is_available = lambda: True
        modules["torch"].cuda.get_device_capability = lambda index=0: capability
        modules["torch"].cuda.get_device_name = lambda index=0: name
    build = types.ModuleType("sam2.build_sam")

    def build_sam2(cfg, checkpoint, device="cpu", apply_postprocessing=True):
        FakeAMG.build_kwargs.append({"cfg": cfg, "apply_postprocessing": apply_postprocessing})
        return harness.FakeModel()
    build.build_sam2 = build_sam2
    amg = types.ModuleType("sam2.automatic_mask_generator")
    amg.SAM2AutomaticMaskGenerator = FakeAMG
    modules.update({"sam2.build_sam": build, "sam2.automatic_mask_generator": amg})
    return modules


original_stub = harness.stub_modules


def run_notebook(workdir, image_path, headless, oom=(), gpu=L4):
    FakeAMG.calls, FakeAMG.build_kwargs, FakeAMG.oom, FakeAMG.gpu = [], [], set(oom), gpu
    harness.stub_modules = stub_modules_ae1
    try:
        return harness.run(NOTEBOOK, workdir, image_path=image_path, headless=headless, cells=CELLS)
    finally:
        harness.stub_modules = original_stub


# ─── comprobaciones ───────────────────────────────────────────────────────────────────────────

def static_checks(nb, protocol_bytes, protocol):
    sources = {c["id"]: "".join(c["source"]) for c in nb["cells"]}
    check("cuaderno: celda 1 = instalación de v1.3 (commit y checkpoint congelados)", sources["pragma-ae1s1-01"].strip("\n") == v13.CELL_INSTALL.strip("\n"))
    check("cuaderno: celda 2 = entorno de v1.3 con carpeta runs_ae1s1",
          sources["pragma-ae1s1-02"].strip("\n") == v13.CELL_ENV.replace('"runs_v13"', '"runs_ae1s1"').strip("\n"))
    literal = json.dumps(protocol_bytes.decode("utf-8"), ensure_ascii=False)
    check("cuaderno: protocolo embebido byte a byte con su SHA-256",
          literal in sources["pragma-ae1s1-03"] and hashlib.sha256(protocol_bytes).hexdigest() in sources["pragma-ae1s1-03"])
    check("cuaderno: modelo con apply_postprocessing=False", "apply_postprocessing=False" in sources["pragma-ae1s1-04"])
    code_ids = [c["id"] for c in nb["cells"] if c["cell_type"] == "code"]
    check("cuaderno: la compuerta de GPU es la primera celda de código, antes de instalar, y exige capacidad ≥ 8",
          code_ids[:2] == ["pragma-ae1s1-00g", "pragma-ae1s1-01"] and "_capability[0] < 8" in sources["pragma-ae1s1-00g"]
          and 'PRECISION["dtype"] != "bfloat16"' in sources["pragma-ae1s1-04"], str(code_ids[:2]))
    run_zip = sources["pragma-ae1s1-05"] + sources["pragma-ae1s1-06"]
    forbidden = ("anns", "masks", "RESULTS", "MASK_HASHES", "EXECUTED", "predicted_iou", "stability_score", "n_masks", "area")
    shown = []
    for cell in ("pragma-ae1s1-04", "pragma-ae1s1-05", "pragma-ae1s1-06"):
        for node in ast.walk(ast.parse(sources[cell])):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "print":
                text = " ".join(ast.unparse(a) for a in node.args)
                shown += [f"{cell}: {t}" for t in forbidden if t in text]
    check("cuaderno: ningún print muestra máscaras, número de máscaras ni scores",
          not shown and 'print(f"configuración {number}/{len(CALL_PLAN)} hecha")' in sources["pragma-ae1s1-05"], str(shown))
    check("cuaderno: ZIP PRAGMA_AE1S1_…_PENDING_ANALYSIS y pide L4",
          "PRAGMA_AE1S1_" in run_zip and "PENDING_ANALYSIS" in run_zip and "L4" in sources["pragma-ae1s1-00b"])
    check("protocolo: 4 llamadas con los kwargs del sweep y techo INCONCLUSIVE_GT_INCOMPLETE",
          [c["call_id"] for c in protocol["call_plan"]] == ["AMG-0", "AMG-1", "AMG-2", "AMG-3"]
          and protocol["stage"]["ceiling"] == "INCONCLUSIVE_GT_INCOMPLETE")


def tamper(zip_path, mutate, name, rehash=True):
    """Cambia archivos del ZIP; con ``rehash`` rehace también el manifiesto (para probar las reglas semánticas)."""
    tmp = zip_path.with_name(f"tamper_{name}.zip")
    with zipfile.ZipFile(zip_path) as src:
        items = {n: src.read(n) for n in src.namelist()}
    for n in list(items):
        items[n] = mutate(n, items[n])
    if rehash:
        manifest = json.loads(items[s1.MANIFEST_JSON])
        for n in manifest["files"]:
            manifest["files"][n] = {"bytes": len(items[n]), "sha256": hashlib.sha256(items[n]).hexdigest()}
        items[s1.MANIFEST_JSON] = json.dumps(manifest).encode()
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
        for n, d in items.items():
            dst.writestr(n, d)
    return tmp


def main():
    photo_path = locate_image()
    protocol_bytes = PROTOCOL.read_bytes()
    protocol = json.loads(protocol_bytes)
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    FakeAMG.boxes = [(o["id"], o["bbox"]) for o in inventory["objects"] if o["tier"] in ("A", "B")]
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    static_checks(nb, protocol_bytes, protocol)

    for label, gpu in (("sin GPU", None), ("T4 (capacidad 7.5)", T4)):
        ns_g, _, error_g = run_notebook(WORKDIR / "gate", photo_path, headless=True, gpu=gpu)
        check(f"E2E {label}: FAIL_ENVIRONMENT en la celda 0, antes de crear la corrida",
              isinstance(error_g, RuntimeError) and str(error_g).startswith("FAIL_ENVIRONMENT") and "RUN_DIR" not in ns_g,
              str(error_g)[:90])
    ns, downloads, error = run_notebook(WORKDIR / "browser", photo_path, headless=False)
    check("E2E navegador: sin errores", error is None, repr(error)[:200] if error else "")
    plan = [c["generator_kwargs"] for c in protocol["call_plan"]]
    check("E2E: las 4 llamadas con exactamente los kwargs del plan, en orden", FakeAMG.calls == plan,
          f"{len(FakeAMG.calls)} llamadas")
    check("E2E: el modelo se construye una vez, sin postprocesado",
          FakeAMG.build_kwargs == [{"cfg": "configs/sam2.1/sam2.1_hiera_l.yaml", "apply_postprocessing": False}])
    zip_path = Path(ns.get("ZIP_PATH", "")) if error is None else None
    check("E2E navegador: una descarga, el ZIP", error is None and downloads == [str(zip_path)])
    env = ns.get("ENVIRONMENT", {})
    check("E2E: la L4 simulada corre en bfloat16 y registra cuda_capability",
          env.get("device") == "cuda" and env.get("dtype") == "bfloat16" and list(env.get("cuda_capability") or []) == [8, 9],
          f"{env.get('dtype')} · {env.get('cuda_capability')}")
    _, downloads_h, error_h = run_notebook(WORKDIR / "headless", photo_path, headless=True)
    check("E2E sin navegador: sin errores y sin descarga", error_h is None and not downloads_h)
    _, _, error_m = run_notebook(WORKDIR / "sin_foto", None, headless=True)
    check("E2E sin foto: error claro, sin selector", isinstance(error_m, FileNotFoundError), type(error_m).__name__)
    ns_o, _, error_o = run_notebook(WORKDIR / "oom", photo_path, headless=True, oom={(64, 0, 0.8, 64)})
    oom_calls = json.loads((Path(ns_o["RUN_DIR"]) / s1.CALLS_JSON).read_text()) if error_o is None else []
    dense = next((c for c in oom_calls if c["call_id"] == "AMG-1"), {})
    check("E2E con OOM simulado en AMG-1: baja a 32 y lo registra",
          error_o is None and dense.get("points_per_batch_attempts") == [64, 32]
          and dense.get("generator_kwargs", {}).get("points_per_batch") == 32, str(dense.get("points_per_batch_attempts")))
    if zip_path is None:
        return finish()

    result = s1.integrity(zip_path, protocol)
    check("integridad del ZIP simulado: SIMULATED_RUN_NOT_EVIDENCE sin problemas",
          result["status"] == "SIMULATED_RUN_NOT_EVIDENCE" and not result["problems"], str(result["problems"])[:200])
    allowed = {"status", "run_kind", "problems", "zip_sha256", "zip_bytes", "run_id", "protocol_content_sha256",
               "environment", "calls", "note"}
    check("integridad: no devuelve datos de resultado", set(result) == allowed, sorted(set(result) - allowed))
    oom_zip = Path(ns_o["ZIP_PATH"])
    check("integridad: el ZIP con OOM registrado sigue siendo válido",
          s1.integrity(oom_zip, protocol)["status"] == "SIMULATED_RUN_NOT_EVIDENCE")

    def flip_mask(n, d):
        if n != "masks/AMG-0.json":
            return d
        payload = json.loads(d)
        counts = payload["masks"][0]["rle"]["counts"]
        counts[1] += 1
        counts[2] -= 1
        return json.dumps(payload).encode()
    t = tamper(zip_path, flip_mask, "mask", rehash=False)
    check("manipular una máscara → INVALID_BUNDLE (manifiesto)", s1.integrity(t, protocol)["status"] == "INVALID_BUNDLE")
    t = tamper(zip_path, flip_mask, "mask_rehash")
    check("manipular una máscara y rehacer el manifiesto → INVALID_BUNDLE (hash de máscara)",
          s1.integrity(t, protocol)["status"] == "INVALID_BUNDLE")

    def edit_calls(field, value):
        def mutate(n, d):
            if n != s1.CALLS_JSON:
                return d
            calls = json.loads(d)
            if field == "attempts":
                calls[0]["points_per_batch_attempts"] = value
                calls[0]["generator_kwargs"]["points_per_batch"] = value[-1]
            else:
                calls[0]["generator_kwargs"][field] = value
            return json.dumps(calls).encode()
        return mutate
    t = tamper(zip_path, edit_calls("pred_iou_thresh", 0.75), "kwargs")
    check("cambiar un kwarg ejecutado → INVALID_BUNDLE", s1.integrity(t, protocol)["status"] == "INVALID_BUNDLE")
    t = tamper(zip_path, edit_calls("attempts", [64, 16]), "ppb")
    check("points_per_batch fuera de la regla (64 → 16) → INVALID_BUNDLE", s1.integrity(t, protocol)["status"] == "INVALID_BUNDLE")

    def edit_env(**changes):
        def mutate(n, d):
            if n != s1.CONFIG_JSON:
                return d
            config = json.loads(d)
            config["environment"].update(changes)
            config["environment"] = {k: v for k, v in config["environment"].items() if v != "DROP"}
            return json.dumps(config).encode()
        return mutate
    frozen = protocol["freeze"]
    real = {"torch": "2.8.0+cu126", "sam2_commit": frozen["SAM2_GIT_COMMIT"], "checkpoint_sha256": frozen["CHECKPOINT_SHA256"]}
    t = tamper(zip_path, edit_env(**real, device_name="Tesla T4", cuda_capability=[7, 5], dtype="float16"), "t4")
    check("registro FORJADO como real en una T4 (float16) → REAL_GPU_DIFFERENT_PRECISION_NOT_EVIDENCE",
          s1.integrity(t, protocol)["status"] == "REAL_GPU_DIFFERENT_PRECISION_NOT_EVIDENCE")
    t = tamper(zip_path, edit_env(cuda_capability="DROP"), "sin_capacidad")
    check("CUDA sin cuda_capability → INVALID_BUNDLE", s1.integrity(t, protocol)["status"] == "INVALID_BUNDLE")
    t = tamper(zip_path, edit_env(dtype="float16"), "dtype")
    check("dtype incoherente con la capacidad (8.9 en float16) → INVALID_BUNDLE",
          s1.integrity(t, protocol)["status"] == "INVALID_BUNDLE")
    for p in zip_path.parent.glob("tamper_*.zip"):
        p.unlink()

    store = WORKDIR / "store"
    pending = s1.analyze(zip_path, protocol, inventory, GT_DIR, store)
    check("lector: con disparadores de R1 y sin llaves, se detiene antes de R2",
          pending["stage1"] == "PENDING_R1_REVIEW" and sorted(pending["r1"]["triggered"]) == sorted(MISSED)
          and "per_config" not in pending, str(pending["r1"]["triggered"]))
    proposals = s1.load_proposals(zip_path, store)
    screen = s1.box_screen(inventory["objects"], {c: p.boxes for c, p in proposals.items()})
    photo = load_rgb(photo_path)
    blind_dir = WORKDIR / "ciego"
    shutil.rmtree(blind_dir, ignore_errors=True)
    summary = s1.blind_package(zip_path, photo, inventory["objects"], screen, proposals, blind_dir)
    mapping = json.loads((blind_dir / "sealed_mapping.json").read_text())
    with zipfile.ZipFile(blind_dir / summary["package"]) as package:
        names = sorted(package.namelist())
        leeme = package.read("LEEME.md").decode("utf-8")
        template = json.loads(package.read("plantilla_respuesta.json"))
    check("triaje ciego: una lámina por objeto disparado, LEEME y plantilla",
          names == sorted(["LEEME.md", "plantilla_respuesta.json"] + [f"{lab}.png" for lab in summary["labels"]]))
    leaks = [t for t in ("AMG", "BASE", "DENSE", "CROP", "SENSITIVE", "score", "ranking", "configuración", "ae0_")
             if t.lower() in leeme.lower() and t not in ("ranking", "score")] + \
            [t for t in ("AMG", "ae0_", "predicted_iou") if t in json.dumps(template)]
    check("triaje ciego: ni el LEEME ni la plantilla nombran configuración, score ni id", not leaks, str(leaks))
    sizes = [len(v["candidates"]) for v in mapping["objects"].values()]
    check("triaje ciego: ≤ 12 candidatas por objeto (3 por configuración), deduplicadas por hash, y el mapeo sellado se publica solo por hash",
          all(0 < n <= 12 for n in sizes) and all(len({c["packed_sha256"] for c in v["candidates"]}) == len(v["candidates"])
                                                   for v in mapping["objects"].values())
          and hashlib.sha256((blind_dir / "sealed_mapping.json").read_bytes()).hexdigest() == summary["sealed_mapping_sha256"],
          str(sizes))
    labels = summary["labels"]
    by_label = {lab: mapping["objects"][lab]["object_id"] for lab in labels}
    first, second = by_label[labels[0]], by_label[labels[1]]
    triage = ({first: "MISS", second: "MISS"}, {first: "MISS", second: "CANNOT_DETERMINE"})
    waiting = s1.analyze(zip_path, protocol, inventory, GT_DIR, store, r1_keys=triage)
    check("lector: MISS + MISS en el triaje NO confirma: escala a la revisión exhaustiva y se detiene antes de R2",
          waiting["stage1"] == "PENDING_R1_REVIEW" and waiting["r1"]["escalated"] == [first]
          and waiting["r1"]["state"] == {first: "PENDING_EXHAUSTIVE_REVIEW", second: "NOT_CONFIRMED"}
          and "per_config" not in waiting, str(waiting["r1"]["state"]))

    exhaustive = s1.exhaustive_package(zip_path, photo, inventory["objects"], screen, proposals, [first], blind_dir)
    x_mapping = json.loads((blind_dir / exhaustive["sealed_mapping"]).read_text())
    with zipfile.ZipFile(blind_dir / exhaustive["package"]) as package:
        x_names = sorted(package.namelist())
        x_leeme = package.read("LEEME.md").decode("utf-8")
        x_template = json.loads(package.read("plantilla_respuesta.json"))
        first_page = package.read(sorted(n for n in x_names if n.endswith(".png"))[0])
    entry = x_mapping["objects"][labels[0]]
    x1, y1, x2, y2 = next(o["bbox"] for o in inventory["objects"] if o["id"] == first)
    brute = set()                                        # comprobación independiente: caja de cada máscara con numpy
    for props in proposals.values():
        for mask, h in zip(props.masks, props.hashes):
            ys, xs = np.nonzero(np.asarray(mask))
            if xs.size and min(xs.max() + 1, x2) > max(xs.min(), x1) and min(ys.max() + 1, y2) > max(ys.min(), y1):
                brute.add(h)
    got = [c["packed_sha256"] for c in entry["candidates"]]
    triage_hashes = {c["packed_sha256"] for c in mapping["objects"][labels[0]]["candidates"]}
    check("revisión exhaustiva: TODAS las propuestas cuya caja corta la del objeto, deduplicadas, sin tope",
          set(got) == brute and len(got) == len(set(got)) and len(got) > s1.PAGE_SIZE
          and (triage_hashes & brute) <= set(got), f"{len(got)} candidatas únicas")
    pages = entry["pages"]
    check("revisión exhaustiva: varias láminas de ≤ 12, todas en el paquete, con LEEME y plantilla",
          len(pages) == -(-len(got) // s1.PAGE_SIZE) > 1
          and x_names == sorted(pages + ["LEEME.md", "plantilla_respuesta.json"])
          and all(sum(c["page"] == pg for c in entry["candidates"]) <= s1.PAGE_SIZE for pg in pages),
          f"{len(pages)} láminas")
    x_leaks = [t for t in ("AMG", "BASE", "DENSE", "CROP", "SENSITIVE", "ae0_") if t.lower() in x_leeme.lower()] + \
              [t for t in ("AMG", "ae0_", "predicted_iou", "score") if t in json.dumps(x_template)]
    check("revisión exhaustiva: ni el LEEME ni la plantilla nombran configuración, score ni id; pide reviewed_all_pages",
          not x_leaks and "reviewed_all_pages" in json.dumps(x_template) and "reviewed_all_pages" in x_leeme, str(x_leaks))
    (WORKDIR / "ejemplo_lamina_R1_exhaustiva_SIMULADA.png").write_bytes(first_page)   # solo para el paquete privado

    full = {"answer": "MISS", "reviewed_all_pages": True}
    done = s1.analyze(zip_path, protocol, inventory, GT_DIR, store, r1_keys=triage,
                      r1_exhaustive_keys=({first: full}, {first: full}))
    check("lector: MISS + MISS en la revisión exhaustiva (todas las láminas) confirma; R4 = FAIL_COMPONENT",
          done["r4"]["confirmed_box_screen_failures"] == [first] and done["stage1"] == "FAIL_COMPONENT",
          str(done["r4"]["confirmed_box_screen_failures"]))
    partial = s1.analyze(zip_path, protocol, inventory, GT_DIR, store, r1_keys=triage,
                         r1_exhaustive_keys=({first: full}, {first: {"answer": "MISS", "reviewed_all_pages": False}}))
    check("lector: un MISS sin haber visto todas las láminas cuenta como CANNOT_DETERMINE → NOT_CONFIRMED",
          partial["r1"]["state"][first] == "NOT_CONFIRMED" and not partial["r4"]["confirmed_box_screen_failures"])
    rows = [done["per_config"][c]["r2_persons"][p] for c in done["per_config"] for p in s1.PERSONS]
    fields = {"verdict", "best_estimate", "best_robust_min", "best_possible_max", "argmax_estimate", "argmax_min", "argmax_max",
              "proposals"}
    check("lector: R2 por persona y configuración con las tres cotas y sus argmax",
          len(rows) == 12 and all(set(r) == fields for r in rows), "valores sobre datos SIMULADOS: no se archivan")
    check("lector: R3 etiquetado FUSION_Q_ESTIMATE_BASED y veredicto del contrato INCONCLUSIVE_GT_INCOMPLETE",
          all(v["r3"]["label"] == "FUSION_Q_ESTIMATE_BASED" and v["gate"] == "INCONCLUSIVE_GT_INCOMPLETE"
              for v in done["per_config"].values()))
    covers = ({first: "COVERS_OBJECT", second: "COVERS_OBJECT"}, {first: "COVERS_OBJECT", second: "COVERS_OBJECT"})
    other = s1.analyze(zip_path, protocol, inventory, GT_DIR, store, r1_keys=covers)
    check("lector: sin fallos confirmados, la decisión es FAIL_COMPONENT solo por R2 robusto; nunca PASS",
          other["stage1"] in ("FAIL_COMPONENT", "INCONCLUSIVE_GT_INCOMPLETE") and "PASS" not in other["stage1"]
          and (other["stage1"] == "FAIL_COMPONENT") == bool(other["r4"]["persons_fail_all_configs"]),
          other["stage1"])
    shutil.rmtree(store, ignore_errors=True)
    return finish()


def finish():
    passed = sum(c["pass"] for c in checks)
    payload = {"notebook": NOTEBOOK.name, "notebook_sha256": hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest(),
               "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
               "result": f"{passed}/{len(checks)}", "status": "PASS" if passed == len(checks) else "FAIL",
               "scope": "estático + E2E con GPU y AMG SIMULADOS + lector sobre el ZIP simulado; no mide la calidad de SAM 2",
               "checks": checks}
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\n{passed}/{len(checks)} · escrito {OUT_JSON.relative_to(ROOT)}")
    raise SystemExit(0 if passed == len(checks) else 1)


if __name__ == "__main__":
    main()
