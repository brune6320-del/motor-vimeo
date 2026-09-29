"""Verificación del cuaderno A-E(−1) v1.3: estática, de punta a punta con SAM simulado y de la auditoría.

    python3 work/verify_pragma_aem1_v1_3.py        # necesita la foto (se localiza por SHA-256)

Qué demuestra:

- el cuaderno embebe el prerregistro byte a byte y tiene las compuertas de congelado;
- ejecutado con la foto real y SAM **simulado**, hace exactamente las 178 llamadas del plan, con los
  mismos puntos, etiquetas, cajas, ``multimask_output`` y semillas (``mask_input``);
- no muestra resultados;
- su ZIP pasa la integridad como ``SIMULATED_RUN_NOT_EVIDENCE``, y cualquier manipulación lo vuelve
  ``INVALID_BUNDLE``;
- el paquete ciego y el análisis funcionan sobre ese ZIP.

Qué NO demuestra: la calidad de SAM 2. Eso exige la GPU y la auditoría ciega.
"""

from __future__ import annotations

import ast
import hashlib
import io
import json
import random
import shutil
import sys
import zipfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "work"))

import harness_aem1 as harness  # noqa: E402
from pragma_ae import aem1_v13_audit as audit  # noqa: E402
from pragma_ae.imageio import load_rgb, locate_image  # noqa: E402

NOTEBOOK = ROOT / "outputs" / "PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_3.ipynb"
PREREG = ROOT / "aem1" / "PRERREGISTRO_A-E-menos-1_v1_3.json"
BASE_REF = ROOT / "auditoria" / "aem1_20260925T062504Z_256dba9f" / "BASE_V2_REFERENCE.json"
PROTOCOL = ROOT / "auditoria" / "PROTOCOLO_AUDITORIA_AEM1_v2.md"
OUT_JSON = ROOT / "outputs" / "PRAGMA_A-E-menos-1_v1_3_verificacion.json"
WORKDIR = ROOT / "local" / "aem1_v1_3_harness"
CELLS = ["pragma-aem1v13-02", "pragma-aem1v13-03", "pragma-aem1v13-04", "pragma-aem1v13-05", "pragma-aem1v13-06"]

checks = []


def check(name, ok, detail=""):
    checks.append({"check": name, "pass": bool(ok), "detail": detail})
    print(("PASS " if ok else "FAIL ") + name + (f" · {detail}" if detail else ""))


class Recorder:
    calls = []

    @classmethod
    def install(cls):
        original = harness.FakePredictor.predict

        def predict(self, point_coords=None, point_labels=None, box=None, mask_input=None,
                    multimask_output=True, return_logits=False):
            out = original(self, point_coords=point_coords, point_labels=point_labels, box=box,
                           mask_input=mask_input, multimask_output=multimask_output, return_logits=return_logits)
            cls.calls.append({"point_coords": None if point_coords is None else np.array(point_coords),
                              "point_labels": None if point_labels is None else np.array(point_labels),
                              "box": None if box is None else np.array(box), "mask_input": mask_input,
                              "multimask_output": multimask_output, "return_logits": return_logits,
                              "low_res": out[2]})
            return out

        harness.FakePredictor.predict = predict
        return original


def static_checks(nb, prereg_bytes, prereg):
    sources = {c["id"]: "".join(c["source"]) for c in nb["cells"]}
    code_cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
    check("cuaderno: todas las celdas de código compilan",
          all(ast.parse("".join(c["source"])) is not None for c in code_cells), f"{len(code_cells)} celdas")
    check("cuaderno: sin salidas ni contadores de ejecución",
          all(not c["outputs"] and c["execution_count"] is None for c in code_cells))
    cell3 = sources["pragma-aem1v13-03"]
    literal = next(node.value for node in ast.walk(ast.parse(cell3))
                   if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "PREREG_TEXT")
    embedded = literal.value.encode("utf-8")
    check("prerregistro embebido idéntico byte a byte al versionado", embedded == prereg_bytes,
          hashlib.sha256(embedded).hexdigest()[:16])
    install = sources["pragma-aem1v13-01"]
    check("celda 1: commit fijado y checkout exacto (no main)",
          prereg["sam2_freeze"]["SAM2_GIT_COMMIT"] in install and '"checkout", "--quiet", SAM2_PINNED_COMMIT' in install
          and "--depth" not in install)
    check("celda 1: se detiene si el commit o el checkpoint difieren",
          install.count("raise RuntimeError(") >= 2 and prereg["sam2_freeze"]["CHECKPOINT_SHA256"] in install
          and str(prereg["sam2_freeze"]["CHECKPOINT_BYTES"]) in install)
    # El texto del prerregistro embebido se excluye del escaneo: su lista «forbidden» nombra lo prohibido.
    code_text = "\n".join(line for c in code_cells for line in "".join(c["source"]).splitlines()
                          if not line.startswith("PREREG_TEXT = "))
    lowered = code_text.lower()
    forbidden = [t for t in ("matplotlib", "imshow", "display(", "fastapi", "localhost", "yolo", "birefnet", "argmax")
                 if t in lowered]
    check("cuaderno: no muestra máscaras ni usa lo prohibido", not forbidden, f"encontrado: {forbidden}" if forbidden else "")
    run_cell = sources["pragma-aem1v13-05"]
    loads = [n for n in ast.walk(ast.parse(run_cell)) if isinstance(n, ast.Name) and n.id == "scores" and isinstance(n.ctx, ast.Load)]
    check("cuaderno: el score nunca se usa (una sola lectura, para archivarlo)",
          len(loads) == 1 and '"scores_never_used": [round(float(s), 6) for s in scores]' in run_cell, f"lecturas: {len(loads)}")
    check("cuaderno: compuerta de luma sobre todos los prompts y holdouts",
          "LUMA_CHECK" in cell3 and '"max_abs_deviation"' in cell3 and "> 3.0" in cell3)


def expected_from_plan(plan):
    return [(np.asarray(c["points"], np.float32).reshape(-1, 2) if c["points"] else None,
             np.asarray(c["labels"], np.int32) if c["points"] else None,
             None if c["box"] is None else np.asarray(c["box"], np.float32), c) for c in plan]


def compare_calls(plan):
    calls = Recorder.calls
    check("E2E: número de llamadas = plan", len(calls) == len(plan), f"{len(calls)} / {len(plan)}")
    by_id = {}
    bad = []
    for recorded, (points, labels, box, call) in zip(calls, expected_from_plan(plan)):
        by_id[call["call_id"]] = recorded
        same = ((points is None and recorded["point_coords"] is None)
                or (recorded["point_coords"] is not None and recorded["point_coords"].dtype == np.float32
                    and np.array_equal(recorded["point_coords"], points)))
        same &= ((labels is None and recorded["point_labels"] is None)
                 or (recorded["point_labels"] is not None and np.array_equal(recorded["point_labels"], labels)))
        same &= (box is None and recorded["box"] is None) or (recorded["box"] is not None and np.array_equal(recorded["box"], box))
        same &= recorded["multimask_output"] == call["multimask_output"] and recorded["return_logits"] is True
        if call["mask_input_from"] is None:
            same &= recorded["mask_input"] is None
        else:
            source = by_id[call["mask_input_from"]["call_id"]]["low_res"][call["mask_input_from"]["index"]]
            same &= recorded["mask_input"] is not None and np.array_equal(recorded["mask_input"], source[None, :, :])
        if not same:
            bad.append(call["call_id"])
    check("E2E: cada llamada = la del plan (puntos, etiquetas, caja, multimask, semilla)", not bad,
          f"distintas: {bad[:3]}" if bad else f"{len(calls)} llamadas idénticas")


def tamper(zip_path, prereg, mutate, name):
    tmp = zip_path.with_name(f"tamper_{name}.zip")
    with zipfile.ZipFile(zip_path) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.namelist():
            data = src.read(item)
            dst.writestr(item, mutate(item, data))
    result = audit.integrity(tmp, prereg)
    tmp.unlink()
    return result


def main():
    photo_path = locate_image()
    prereg_bytes = PREREG.read_bytes()
    prereg = json.loads(prereg_bytes)
    base_reference = json.loads(BASE_REF.read_text(encoding="utf-8"))
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    static_checks(nb, prereg_bytes, prereg)

    # E2E con navegador simulado (descarga) y sin navegador (Colab CLI).
    original = Recorder.install()
    try:
        Recorder.calls = []
        ns, downloads, error = harness.run(NOTEBOOK, WORKDIR / "browser", image_path=photo_path, headless=False, cells=CELLS)
        check("E2E navegador: sin errores", error is None, repr(error)[:200] if error else "")
        compare_calls(prereg["call_plan"])
        zip_path = Path(ns.get("ZIP_PATH", "")) if error is None else None
        check("E2E navegador: una descarga, el ZIP", error is None and len(downloads) == 1 and downloads[0] == str(zip_path))
        Recorder.calls = []
        ns_h, downloads_h, error_h = harness.run(NOTEBOOK, WORKDIR / "headless", image_path=photo_path, headless=True, cells=CELLS)
        check("E2E sin navegador: sin errores y sin descarga", error_h is None and not downloads_h)
        ns_m, _, error_m = harness.run(NOTEBOOK, WORKDIR / "sin_foto", image_path=None, headless=True, cells=CELLS)
        check("E2E sin foto: error claro, sin selector", isinstance(error_m, FileNotFoundError), type(error_m).__name__)
    finally:
        harness.FakePredictor.predict = original
    if zip_path is None:
        return finish()

    # Auditoría, etapa 1: integridad sin resultados.
    result = audit.integrity(zip_path, prereg)
    check("integridad del ZIP simulado: SIMULATED_RUN_NOT_EVIDENCE sin problemas",
          result["status"] == "SIMULATED_RUN_NOT_EVIDENCE" and not result["problems"], str(result["problems"])[:200])
    allowed = {"status", "run_kind", "problems", "zip_sha256", "zip_bytes", "run_id", "prereg_content_sha256",
               "environment", "calls", "candidates", "note"}
    check("integridad: no devuelve datos de resultado (solo campos de integridad)",
          set(result) == allowed and isinstance(result["candidates"], int), sorted(set(result) - allowed))
    flip = tamper(zip_path, prereg, lambda n, d: d[:-1] + bytes([d[-1] ^ 1]) if n.endswith(".png") else d, "png")
    check("manipular una máscara → INVALID_BUNDLE", flip["status"] == "INVALID_BUNDLE", flip["problems"][:1])

    def edit_calls(n, d):
        if n != audit.CALLS:
            return d
        calls = json.loads(d)
        calls[5]["points"][0][0] += 1
        return json.dumps(calls).encode()
    drift = tamper(zip_path, prereg, edit_calls, "calls")
    check("desviarse del plan → INVALID_BUNDLE", drift["status"] == "INVALID_BUNDLE", drift["problems"][:1])

    # Etapa 2: paquete ciego.
    photo = load_rgb(photo_path)
    blind_dir = WORKDIR / "ciego"
    shutil.rmtree(blind_dir, ignore_errors=True)
    summary = audit.blind_package(zip_path, photo, blind_dir, prereg, base_reference, PROTOCOL, rng=random.Random(7))
    expected_n = 18 + summary["base_not_bit_exact"]
    with zipfile.ZipFile(blind_dir / summary["package"]) as package:
        names = sorted(package.namelist())
        leeme = package.read("LEEME.md").decode("utf-8")
        template = json.loads(package.read("plantilla_juicios.json"))
    check("paquete ciego: 18 +POS + BASE no idénticas; LEEME y plantilla",
          summary["n"] == expected_n and len(names) == expected_n + 2 and "LEEME.md" in names,
          f"{summary['n']} láminas (BASE no idénticas: {summary['base_not_bit_exact']})")
    leaks = [w for w in ("+POS", "BASE", "RECIPROCAL", "point", "box", "seed", "score") if w in leeme]
    check("paquete ciego: el LEEME no nombra ramas, protocolos ni scores", not leaks, str(leaks))
    check("paquete ciego: la plantilla pide agujeros D/L y preguntas auxiliares",
          all(set(row["aux"]) == set(audit.AUX) for row in template["candidates"].values()))
    mapping = json.loads((blind_dir / "sealed_mapping.json").read_text())
    check("paquete ciego: mapeo sellado con hash publicado",
          hashlib.sha256((blind_dir / "sealed_mapping.json").read_bytes()).hexdigest() == summary["sealed_mapping_sha256"])

    # Etapa 3: análisis con juicios sintéticos (dos llaves iguales salvo una celda, adjudicada).
    def judgments(flip_label=None):
        rows = {}
        for label in summary["labels"]:
            crit = {c: "FALSE" for c in audit.CRITERIA}
            crit["correct_subject"] = "TRUE"
            rows[label] = {"criteria": crit, "aux": {a: "FALSE" for a in audit.AUX},
                           "holes": {str(h["number"]): "D" for h in mapping["holes"][label]}}
        if flip_label:
            rows[flip_label]["criteria"]["background_excluded"] = "TRUE"
        return {"candidates": rows}
    first, second = judgments(), judgments(summary["labels"][0])
    pending = audit.analyze(zip_path, prereg, base_reference, mapping, first, second)
    check("análisis: una discrepancia sin adjudicar deja el caso pendiente",
          pending["case_status"] == "PENDING_TECHNICAL_ADJUDICATION" and len(pending["pending_adjudication"]) == 1)
    cid = mapping["mapping"][summary["labels"][0]]["candidate_id"]
    done = audit.analyze(zip_path, prereg, base_reference, mapping, first, second,
                         {(cid, "background_excluded"): {"value": "FALSE", "kind": "medicion"}})
    check("análisis: con la adjudicación, veredicto y 6 hipótesis evaluadas",
          done["case_status"] == "INCONCLUSIVE_SELECTED_OUTPUT_FAILED" and len(done["hypotheses"]) == 6
          and "PENDING_ADJUDICATION" not in done["hypotheses"].values(),
          f"{len(done['hypotheses'])} hipótesis evaluadas sobre datos SIMULADOS (sus valores no se archivan: no son resultados)")
    fam = done["perturbation"]["per_family"]
    check("análisis: estabilidad por familia (P+1, H1, S1, caja) y recíproco",
          {k.split("|")[1] for k in fam} == {"P+1", "H1", "S1", "TRANSLATE", "EXPAND", "CONTRACT"}
          and done["reciprocal"]["stability"]["label"] in ("STABLE", "UNSTABLE", "CONFLICT", "NOT_EVALUABLE"))
    owner = next(iter(done["ownership"].values()))
    check("análisis: propiedad con las tres razones", {"shared_over_min", "shared_over_target", "shared_over_reciprocal"} <= set(owner))
    return finish()


def finish():
    passed = sum(c["pass"] for c in checks)
    payload = {"notebook": NOTEBOOK.name, "notebook_sha256": hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest(),
               "prereg_sha256": hashlib.sha256(PREREG.read_bytes()).hexdigest(),
               "result": f"{passed}/{len(checks)}", "status": "PASS" if passed == len(checks) else "FAIL",
               "scope": "estático + E2E con SAM SIMULADO + auditoría sobre el ZIP simulado; no mide la calidad de SAM 2",
               "checks": checks}
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\n{passed}/{len(checks)} · escrito {OUT_JSON.relative_to(ROOT)}")
    raise SystemExit(0 if passed == len(checks) else 1)


if __name__ == "__main__":
    main()
