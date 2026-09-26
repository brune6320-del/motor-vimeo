"""Verificación del cuaderno A-E(−1) v1.4: estática, de punta a punta con SAM simulado y de la auditoría.

    python3 work/verify_pragma_aem1_v1_4.py        # necesita la foto (se localiza por SHA-256)

Qué demuestra:

- el cuaderno embebe el prerregistro v1.4 byte a byte y conserva las compuertas de congelado;
- ejecutado con la foto real y SAM **simulado**, hace exactamente las llamadas del plan (puntos,
  etiquetas, caja, ``multimask_output`` y semillas);
- no muestra resultados y usa solo nombres de v1.4;
- su ZIP pasa la integridad como ``SIMULATED_RUN_NOT_EVIDENCE``, y cualquier manipulación lo vuelve
  ``INVALID_BUNDLE``;
- el paquete ciego (6 láminas) y el análisis (adjudicación de O por medición, H-C3, H-G5,
  perturbación) funcionan sobre ese ZIP.

Qué NO demuestra: la calidad de SAM 2. Eso exige la GPU y la auditoría ciega.
"""

from __future__ import annotations

import hashlib
import json
import random
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "work"))

import harness_aem1 as harness  # noqa: E402
import verify_pragma_aem1_v1_3 as base  # noqa: E402
from pragma_ae import aem1_v13 as v13  # noqa: E402
from pragma_ae import aem1_v14 as w  # noqa: E402
from pragma_ae import aem1_v14_audit as audit  # noqa: E402
from pragma_ae.imageio import load_rgb, locate_image  # noqa: E402

NOTEBOOK = ROOT / "outputs" / "PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_4.ipynb"
PREREG = ROOT / "aem1" / "PRERREGISTRO_A-E-menos-1_v1_4.json"
PROTOCOL = ROOT / "auditoria" / "PROTOCOLO_AUDITORIA_AEM1_v2.md"
OUT_JSON = ROOT / "outputs" / "PRAGMA_A-E-menos-1_v1_4_verificacion.json"
WORKDIR = ROOT / "local" / "aem1_v1_4_harness"
CELLS = ["pragma-aem1v14-02", "pragma-aem1v14-03", "pragma-aem1v14-04", "pragma-aem1v14-05", "pragma-aem1v14-06"]

check = base.check
checks = base.checks


def static_checks(nb, prereg_bytes, prereg):
    # Las comprobaciones de v1.3 buscan sus celdas por id: se renombran a los de v1.4.
    renamed = {"cells": [{**c, "id": c["id"].replace("aem1v14", "aem1v13")} for c in nb["cells"]]}
    base.static_checks(renamed, prereg_bytes, prereg)
    sources = {c["id"]: "".join(c["source"]) for c in nb["cells"]}
    run_zip = sources["pragma-aem1v14-05"] + sources["pragma-aem1v14-06"]
    check("cuaderno: solo nombres de v1.4 en la ejecución y el ZIP",
          "aem1v13" not in run_zip and "AEM1v13" not in run_zip and "PRAGMA_AEM1v14_" in run_zip)
    check("cuaderno: PNG para BASE, referencia y H2; perturbaciones en npz",
          'PNG_BRANCHES = ("BASE", "+POS_HAIR+SLEEVE", "+POS_HAIR+SLEEVE+H2")' in sources["pragma-aem1v14-05"])
    check("cuaderno: pide L4 (la referencia debe salir bit a bit)", "L4" in sources["pragma-aem1v14-00b"])


def reference_calls_identical(prereg):
    v13_plan = {c["call_id"]: c for c in json.loads((ROOT / "aem1" / "PRERREGISTRO_A-E-menos-1_v1_3.json").read_text())["call_plan"]}
    fields = ("points", "labels", "box", "mask_input_from", "multimask_output", "candidates")
    same = [c["call_id"] for c in prereg["call_plan"] if c["branch"] in ("BASE", w.REF_BRANCH)
            and all(c[f] == v13_plan[c["call_id"]][f] for f in fields)]
    check("plan: BASE|box y la referencia son llamada a llamada las de v1.3", len(same) == 4, f"{len(same)}/4")
    h2_calls = [c for c in prereg["call_plan"] if c["branch"] == w.H2_BRANCH]
    ok = all(c["point_ids"] == ["P+1", "H1", "S1", "H2", "P-1", "P-2", "P-3"] and c["labels"] == [1, 1, 1, 1, 0, 0, 0]
             and c["box"] == prereg["base_config"]["BOX"] and c["mask_input_from"]["call_id"] == "BASE|box" for c in h2_calls)
    twins = [next(r for r in prereg["call_plan"] if r["call_id"] == c["call_id"].replace(w.H2_BRANCH, w.REF_BRANCH, 1))
             for c in h2_calls]
    only_h2 = all([p for p, i in zip(c["points"], c["point_ids"]) if i != "H2"] == t["points"] for c, t in zip(h2_calls, twins))
    check("plan: la rama H2 solo añade H2 a la referencia (misma caja, semillas y resto de prompts)",
          len(h2_calls) == 3 and ok and only_h2)


def main():
    photo_path = locate_image()
    prereg_bytes = PREREG.read_bytes()
    prereg = json.loads(prereg_bytes)
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    static_checks(nb, prereg_bytes, prereg)
    reference_calls_identical(prereg)

    original = base.Recorder.install()
    zip_path = None
    try:
        base.Recorder.calls = []
        ns, downloads, error = harness.run(NOTEBOOK, WORKDIR / "browser", image_path=photo_path, headless=False, cells=CELLS)
        check("E2E navegador: sin errores", error is None, repr(error)[:200] if error else "")
        base.compare_calls(prereg["call_plan"])
        zip_path = Path(ns.get("ZIP_PATH", "")) if error is None else None
        check("E2E navegador: una descarga, el ZIP", error is None and len(downloads) == 1 and downloads[0] == str(zip_path))
        base.Recorder.calls = []
        _, downloads_h, error_h = harness.run(NOTEBOOK, WORKDIR / "headless", image_path=photo_path, headless=True, cells=CELLS)
        check("E2E sin navegador: sin errores y sin descarga", error_h is None and not downloads_h)
        _, _, error_m = harness.run(NOTEBOOK, WORKDIR / "sin_foto", image_path=None, headless=True, cells=CELLS)
        check("E2E sin foto: error claro, sin selector", isinstance(error_m, FileNotFoundError), type(error_m).__name__)
    finally:
        harness.FakePredictor.predict = original
    if zip_path is None:
        return finish()

    result = audit.integrity(zip_path, prereg)
    check("integridad del ZIP simulado: SIMULATED_RUN_NOT_EVIDENCE sin problemas",
          result["status"] == "SIMULATED_RUN_NOT_EVIDENCE" and not result["problems"], str(result["problems"])[:200])
    allowed = {"status", "run_kind", "problems", "zip_sha256", "zip_bytes", "run_id", "prereg_content_sha256",
               "environment", "calls", "candidates", "note"}
    check("integridad: no devuelve datos de resultado", set(result) == allowed, sorted(set(result) - allowed))

    def tamper(mutate, name):
        tmp = zip_path.with_name(f"tamper_{name}.zip")
        with zipfile.ZipFile(zip_path) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
            for item in src.namelist():
                dst.writestr(item, mutate(item, src.read(item)))
        out = audit.integrity(tmp, prereg)
        tmp.unlink()
        return out
    flip = tamper(lambda n, d: d[:-1] + bytes([d[-1] ^ 1]) if n.endswith(".png") else d, "png")
    check("manipular una máscara → INVALID_BUNDLE", flip["status"] == "INVALID_BUNDLE", flip["problems"][:1])

    def edit_calls(n, d):
        if n != audit.CALLS:
            return d
        calls = json.loads(d)
        calls[5]["points"][3][0] += 1
        return json.dumps(calls).encode()
    drift = tamper(edit_calls, "calls")
    check("mover H2 un píxel en lo ejecutado → INVALID_BUNDLE", drift["status"] == "INVALID_BUNDLE", drift["problems"][:1])

    photo = load_rgb(photo_path)
    dark = v13.dark_map(v13.gray_of(photo))
    blind_dir = WORKDIR / "ciego"
    shutil.rmtree(blind_dir, ignore_errors=True)
    summary = audit.blind_package(zip_path, photo, blind_dir, prereg, PROTOCOL, rng=random.Random(11))
    with zipfile.ZipFile(blind_dir / summary["package"]) as package:
        names = sorted(package.namelist())
        leeme = package.read("LEEME.md").decode("utf-8")
    check("paquete ciego: 6 láminas N01–N06, LEEME y plantilla",
          summary["labels"] == [f"N{i:02d}" for i in range(1, 7)] and len(names) == 8 and "LEEME.md" in names)
    leaks = [t for t in ("H2", "+POS", "BASE", "box", "seed", "semilla", "score", "referencia", "perturb") if t in leeme]
    check("paquete ciego: el LEEME no nombra ramas, H2, semillas ni scores", not leaks, str(leaks))
    mapping = json.loads((blind_dir / "sealed_mapping.json").read_text())
    check("paquete ciego: mapeo sellado con hash publicado y las 6 candidatas previstas",
          hashlib.sha256((blind_dir / "sealed_mapping.json").read_bytes()).hexdigest() == summary["sealed_mapping_sha256"]
          and sorted(r["candidate_id"] for r in mapping["mapping"].values()) == sorted(audit.blind_ids()))

    def judgments(overrides=()):
        rows = {}
        for label in summary["labels"]:
            crit = {c: "TRUE" for c in audit.CRITERIA}
            crit["body_and_edges_complete"] = "FALSE"
            rows[label] = {"criteria": crit, "aux": {a: "TRUE" for a in audit.AUX},
                           "holes": {str(h["number"]): "D" for h in mapping["holes"][label]}}
        for label, field, value in overrides:
            rows[label]["criteria"][field] = value
        return {"candidates": rows}
    h2_labels = [lab for lab, r in mapping["mapping"].items() if r["candidate_id"].startswith(w.H2_BRANCH + "|")]
    first = judgments()
    second = judgments([(h2_labels[0], "background_excluded", "FALSE"), (h2_labels[1], "other_person_excluded", "FALSE")])
    pending = audit.analyze(zip_path, prereg, mapping, first, second, dark)
    check("análisis: G en disputa queda pendiente; O en disputa se adjudica por medición",
          pending["case_status"] == "PENDING_TECHNICAL_ADJUDICATION" and len(pending["pending_adjudication"]) == 1
          and any(v["kind"] == "medicion_prerregistrada" for v in pending["adjudications"].values()),
          str(pending["pending_adjudication"]))
    cid = mapping["mapping"][h2_labels[0]]["candidate_id"]
    done = audit.analyze(zip_path, prereg, mapping, first, second, dark,
                         {(cid, "background_excluded"): {"value": "FALSE", "kind": "medicion"}})
    check("análisis: con la adjudicación, veredicto, cierre de A-E(−1) e hipótesis H-C3 y H-G5 evaluadas",
          done["case_status"] == "INCONCLUSIVE_SELECTED_OUTPUT_FAILED" and done["aem1_closure"] == "AEM1_CLOSED_INCONCLUSIVE"
          and set(done["hypotheses"]) == {"H-C3", "H-G5"} and "PENDING_ADJUDICATION" not in done["hypotheses"].values(),
          "valores sobre datos SIMULADOS: no se archivan (no son resultados)")
    check("análisis: la referencia simulada no es bit a bit y se declara",
          done["reproduction"]["label"] == "NOT_BIT_EXACT")
    check("análisis: por semilla, cierre, agujeros nuevos, O y perturbación de H2",
          set(done["per_seed"]) == {"s0", "s1", "s2"} and len(done["perturbation"]["per_seed"]) == 3
          and all(r["n"] == prereg["candidate_counts"]["valid_point_perturbations"] for r in done["perturbation"]["per_seed"].values()))
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
