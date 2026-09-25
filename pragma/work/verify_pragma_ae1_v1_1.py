"""Verifica A-E(−1) v1.1: las 68 comprobaciones Codex + comprobaciones propias de v1.1.

1. Ejecuta el verificador Codex original (hash fijado) apuntándolo al cuaderno v1.1, sin
   modificar su lógica: si alguna de las 68 falla, v1.1 no pasa.
2. Añade comprobaciones que el verificador estático no podía hacer:
   - que solo cambiaron las celdas previstas y los 15 sentinelas no tocados siguen igual;
   - distancia mínima prompt↔holdout (un holdout pegado a un prompt no falsa nada);
   - que la función de hoja de contactos embebida es idéntica a la del kit;
   - con la foto disponible: comprobación anclada en píxeles de los puntos corregidos.
3. Ejecuta en CPU, con la foto real, las celdas que no requieren GPU (04, 06, 07) para
   demostrar que la celda de configuración modificada corre y produce sus evidencias.

Salida: ``outputs/PRAGMA_A-E-menos-1_v1_1_verificacion.json``. El experimento sigue NOT_RUN.
"""

import ast
import hashlib
import inspect
import json
import math
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pragma_ae.preflight import SPEC_PATTERN, sentinel_contact_sheet  # noqa: E402

CODEX_VERIFIER = ROOT / "work" / "verify_pragma_ae1_codex.py"
CODEX_VERIFIER_SHA256 = "e949c5aeb45450723a0718f92ef0b54afd7294f0d79156c15ee7e5cf21f1ba05"
V10 = ROOT / "outputs" / "PRAGMA_A-E-menos-1_diagnostico_caso_chica_Codex.ipynb"
V10_SHA256 = "5941be56b22fccc3efd4e299cc8ee6a12cb7c473d2977d4c0876e4e2ea73b706"
V11 = ROOT / "outputs" / "PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_1.ipynb"
REPORT = ROOT / "outputs" / "PRAGMA_A-E-menos-1_v1_1_verificacion.json"
HARNESS_DIR = ROOT / "local" / "aem1_v1_1_cpu_harness"

EXPECTED_CHANGED_CELLS = {"pragma-aem1-00", "pragma-aem1-01", "pragma-aem1-06m", "pragma-aem1-06", "pragma-aem1-11"}
CORRECTED = {"P-2": (2640, 430), "P-3": (2400, 810), "O2": (2700, 380)}
WALL_V10 = {"P-2": (2600, 400), "P-3": (2450, 700), "O2": (2680, 300)}
MIN_PROMPT_HOLDOUT_PX = 60  # 10 parches de radio 6: el holdout no puede quedar pegado a una orden


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


checks = []


def check(name, condition, detail=""):
    row = {"name": name, "pass": bool(condition)}
    if detail:
        row["detail"] = detail
    checks.append(row)
    if not condition:
        raise AssertionError(f"{name}: {detail}")


def run_codex_checks():
    source = CODEX_VERIFIER.read_text(encoding="utf-8")
    check("codex_verifier_hash", sha256(CODEX_VERIFIER) == CODEX_VERIFIER_SHA256, sha256(CODEX_VERIFIER))
    old_nb = 'NOTEBOOK = ROOT / "outputs" / "PRAGMA_A-E-menos-1_diagnostico_caso_chica_Codex.ipynb"'
    old_report = 'REPORT = ROOT / "outputs" / "PRAGMA_A-E-menos-1_Codex_verificacion.json"'
    assert source.count(old_nb) == 1 and source.count(old_report) == 1
    scratch = HARNESS_DIR / "codex_checks_on_v1_1.json"
    scratch.parent.mkdir(parents=True, exist_ok=True)
    source = source.replace(old_nb, f"NOTEBOOK = Path({str(V11)!r})").replace(old_report, f"REPORT = Path({str(scratch)!r})")
    namespace = {"__file__": str(CODEX_VERIFIER), "__name__": "codex_verifier_on_v1_1"}
    exec(compile(source, str(CODEX_VERIFIER), "exec"), namespace)
    codex = json.loads(scratch.read_text(encoding="utf-8"))
    check("codex_68_checks_on_v1_1", codex["checks_passed"] == 68 and all(c["pass"] for c in codex["checks"]),
          f"{codex['checks_passed']} checks")
    return codex


def specs_of(nb):
    code = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
    return {sid: {"xy": (int(x), int(y)), "group": g, "description": d}
            for sid, x, y, g, d in SPEC_PATTERN.findall(code) if not sid.startswith("S")}


def run_v11_checks():
    check("v1_0_source_hash", sha256(V10) == V10_SHA256, sha256(V10))
    v10 = json.loads(V10.read_text(encoding="utf-8"))
    v11 = json.loads(V11.read_text(encoding="utf-8"))
    ids10 = [c["id"] for c in v10["cells"]]
    ids11 = [c["id"] for c in v11["cells"]]
    check("same_cell_order", ids10 == ids11)
    changed = {a["id"] for a, b in zip(v10["cells"], v11["cells"]) if a != b}
    check("only_expected_cells_changed", changed == EXPECTED_CHANGED_CELLS, ", ".join(sorted(changed)))

    s10, s11 = specs_of(v10), specs_of(v11)
    check("sentinel_ids_preserved", set(s10) == set(s11) and len(s11) == 18)
    for sid, xy in CORRECTED.items():
        check(f"corrected:{sid}", s11[sid]["xy"] == xy and s11[sid]["group"] == s10[sid]["group"], str(s11[sid]["xy"]))
    wall_left = [sid for sid, xy in WALL_V10.items() if any(s["xy"] == xy for s in s11.values())]
    check("wall_coordinates_absent", not wall_left, ", ".join(wall_left))
    untouched = [sid for sid in s10 if sid not in CORRECTED and s10[sid]["xy"] != s11[sid]["xy"]]
    check("other_15_coordinates_unchanged", not untouched, ", ".join(untouched))
    check("contact_ids_flagged", all("CONFIRMAR PROPIETARIO" in s11[s]["description"] for s in ("O3", "O4")))

    prompts = [(sid, s["xy"]) for sid, s in s11.items() if s["group"].startswith("prompt_")]
    holdouts = [(sid, s["xy"]) for sid, s in s11.items() if not s["group"].startswith("prompt_")]
    closest = min((math.dist(a, b), pa, hb) for pa, a in prompts for hb, b in holdouts)
    check("min_prompt_holdout_distance", closest[0] >= MIN_PROMPT_HOLDOUT_PX,
          f"{closest[0]:.0f}px ({closest[1]}↔{closest[2]}) ≥ {MIN_PROMPT_HOLDOUT_PX}px")

    code11 = {c["id"]: "".join(c["source"]) for c in v11["cells"]}
    check("box_unchanged", "BOX_CHICA_XYXY = (2100, 300, 3500, 2247)" in code11["pragma-aem1-06"])
    check("confirmation_default_false", "AEM1_CONFIG_CONFIRMADA = False # @param" in code11["pragma-aem1-06"])
    check("config_revision_recorded", '"config_revision": "1.1"' in code11["pragma-aem1-06"])
    tree = ast.parse(code11["pragma-aem1-06"])
    embedded = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "sentinel_contact_sheet"), None)
    kit = ast.parse(inspect.getsource(sentinel_contact_sheet)).body[0]
    check("contact_sheet_function_identical_to_kit",
          embedded is not None and ast.dump(embedded) == ast.dump(kit))
    check("contact_sheet_in_zip_whitelist",
          "CONFIG_OVERLAY_PATH, CONFIG_CONTACT_SHEET_PATH, *current_proposal_artifacts" in code11["pragma-aem1-11"])
    check("contact_stats_in_report", '"config_contact_sheet": AEM1_CONTACT_STATS' in code11["pragma-aem1-11"])
    return s11


def grounded_checks(s11):
    """Anclado en píxeles. Solo corre si la foto de aceptación está disponible."""
    try:
        from pragma_ae.imageio import load_rgb, locate_image
        path = locate_image()
    except (FileNotFoundError, ImportError) as exc:
        return {"status": "SKIPPED_NO_IMAGE", "detail": str(exc)}
    import numpy as np
    gray = load_rgb(path).astype(np.float32).mean(axis=2)

    def patch(xy, r=6):
        x, y = xy
        p = gray[y - r:y + r + 1, x - r:x + r + 1]
        return round(float(p.mean()), 1), round(float(p.std()), 1)

    wall_refs = {"wall_2400_550": patch((2400, 550)), "wall_2550_250": patch((2550, 250))}
    wall_mean = min(m for m, _ in wall_refs.values())
    old = {sid: patch(xy) for sid, xy in WALL_V10.items()}
    new = {sid: patch(xy) for sid, xy in CORRECTED.items()}
    rows = {
        # v1.0 P-3 y O2: estadísticamente indistinguibles de la pared lisa.
        "v1_0_P-3_wall_like": old["P-3"][0] >= wall_mean - 15 and old["P-3"][1] < 25,
        "v1_0_O2_wall_like": old["O2"][0] >= wall_mean - 15 and old["O2"][1] < 25,
        # v1.1: los tres puntos corregidos están sobre material oscuro (pelo/tela), lejos de la pared.
        "v1_1_corrected_not_wall": all(m < 150 for m, _ in new.values()),
    }
    return {"status": "PASS" if all(rows.values()) else "FAIL", "image_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "wall_reference": wall_refs, "v1_0_points": old, "v1_1_points": new, "rows": rows,
            "scope": "Solo descarta 'pared lisa'. No prueba a quién pertenece el píxel: eso lo confirma la persona."}


def cpu_harness():
    """Ejecuta en CPU las celdas sin GPU (04, 06, 07) del v1.1 con la foto real."""
    try:
        from pragma_ae.imageio import locate_image
        path = locate_image()
    except FileNotFoundError as exc:
        return {"status": "SKIPPED_NO_IMAGE", "detail": str(exc)}
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from PIL import Image, ImageOps

    nb = json.loads(V11.read_text(encoding="utf-8"))
    cells = {c["id"]: "".join(c["source"]) for c in nb["cells"]}
    run_dir = HARNESS_DIR / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    # Preludio: sustituye solo lo que la celda 03 hace sin torch (hash, carga, RUN_DIR).
    import dataclasses
    import datetime as dt
    import typing
    import time
    import uuid
    namespace = {
        "__name__": "aem1_cpu_harness", "np": np, "plt": plt, "Image": Image, "ImageOps": ImageOps,
        "hashlib": hashlib, "json": json, "time": time, "uuid": uuid, "Path": Path,
        "dataclass": dataclasses.dataclass, "field": dataclasses.field,
        "Optional": typing.Optional, "Protocol": typing.Protocol,
        "datetime": dt.datetime, "timezone": dt.timezone,
        "RUN_DIR": run_dir, "IMAGE_SHA256": sha256(path),
        # La celda 05 (modelo) no corre aquí: la 06 solo asigna su selector a este sustituto.
        "pipeline": types.SimpleNamespace(selector=None, detections=[]),
    }
    with Image.open(path) as handle:
        namespace["image_pil"] = ImageOps.exif_transpose(handle).convert("RGB")
    namespace["image"] = np.asarray(namespace["image_pil"])
    plt.show = lambda *a, **k: None
    executed = []
    for cell_id in ("pragma-aem1-04", "pragma-aem1-06", "pragma-aem1-07"):
        exec(compile(cells[cell_id], cell_id, "exec"), namespace)
        executed.append(cell_id)
    assert type(namespace["pipeline"].selector).__name__ == "FixedProtocolSelector"
    produced = {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in sorted(run_dir.iterdir())}
    stats = {s["sentinel_id"]: [s["patch_luma_mean"], s["patch_luma_std"]] for s in namespace["AEM1_CONTACT_STATS"]}
    return {
        "status": "PASS",
        "executed_cells": executed,
        "not_executed": ["pragma-aem1-02", "pragma-aem1-03", "pragma-aem1-05", "pragma-aem1-08",
                         "pragma-aem1-09", "pragma-aem1-10", "pragma-aem1-11"],
        "config_digest": namespace["AEM1_CONFIG_DIGEST"],
        "config_ready": namespace["AEM1_CONFIG_READY"],
        "produced_local_files": produced,
        "contact_sheet_luma": stats,
        "note": "Evidencias derivadas de la foto: quedan en local/, no se versionan.",
    }


def main():
    codex = run_codex_checks()
    s11 = run_v11_checks()
    grounded = grounded_checks(s11)
    harness = cpu_harness()
    if grounded["status"] == "FAIL":
        raise AssertionError(f"grounded_checks: {grounded['rows']}")
    payload = {
        "artifact": V11.name,
        "artifact_bytes": V11.stat().st_size,
        "artifact_sha256": sha256(V11),
        "source_artifact_sha256": V10_SHA256,
        "verification_status": "STATIC_VERIFICATION_PASS",
        "experiment_status": "NOT_RUN",
        "codex_checks_passed": codex["checks_passed"],
        "v1_1_checks_passed": len(checks),
        "checks": checks,
        "grounded_checks": grounded,
        "cpu_harness": harness,
        "limitations": [
            "No ejecuta SAM 2 ni CUDA: los protocolos siguen NOT_RUN.",
            "Las comprobaciones en píxeles solo descartan 'pared lisa'; la pertenencia de cada punto la confirma una persona.",
            "AEM1_CONFIG_CONFIRMADA permanece False por diseño.",
        ],
    }
    REPORT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("verification_status", "experiment_status", "codex_checks_passed",
                                               "v1_1_checks_passed", "artifact_sha256")}
                     | {"grounded": grounded["status"], "cpu_harness": harness["status"]}, indent=2))


if __name__ == "__main__":
    main()
