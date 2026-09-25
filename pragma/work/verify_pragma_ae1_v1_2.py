"""Verifica A-E(−1) v1.2 «un clic».

1. Las 68 comprobaciones Codex, sin modificar su lógica, sobre el cuaderno v1.2.
2. Comprobaciones propias de v1.2 (diff acotado frente a v1.1, coordenadas, confirmación ligada a
   evidencia, semillas exhaustivas, invariante multimask_output=False por AST, modo sin navegador).
3. Con la foto: la luminancia esperada embebida coincide con la recalculada por el kit.
4. Arnés de punta a punta con SAM simulado (celdas 03–11 con la foto real):
   a) navegador: 8 propuestas, PENDING_EXTERNAL_AUDIT, ZIP íntegro y una descarga;
   b) sin navegador: mismo resultado y ninguna descarga;
   c) sin foto y sin navegador: error claro, nunca el selector de archivos.

Salida: outputs/PRAGMA_A-E-menos-1_v1_2_verificacion.json (sin contenido derivado de la foto).
El experimento real sigue NOT_RUN: el arnés no evalúa la calidad de SAM 2.
"""

import ast
import hashlib
import inspect
import json
import math
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "work"))
import harness_aem1  # noqa: E402
from build_pragma_ae1_v1_2 import PREFLIGHT_EXPECTED_LUMA  # noqa: E402
from pragma_ae.preflight import SPEC_PATTERN, sentinel_contact_sheet  # noqa: E402

CODEX_VERIFIER = ROOT / "work" / "verify_pragma_ae1_codex.py"
CODEX_VERIFIER_SHA256 = "e949c5aeb45450723a0718f92ef0b54afd7294f0d79156c15ee7e5cf21f1ba05"
V11 = ROOT / "outputs" / "PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_1.ipynb"
V11_SHA256 = "ddf784956de6eb8555bb9eb1f30d7af1dcabba06121568a0d4bc62be60c500dc"
V12 = ROOT / "outputs" / "PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_2.ipynb"
REPORT = ROOT / "outputs" / "PRAGMA_A-E-menos-1_v1_2_verificacion.json"
LOCAL = ROOT / "local" / "aem1_v1_2_harness"

EXPECTED_CHANGED_CELLS = {
    "pragma-aem1-00", "pragma-aem1-01", "pragma-aem1-03", "pragma-aem1-06m", "pragma-aem1-06", "pragma-aem1-07",
    "pragma-aem1-09m", "pragma-aem1-09", "pragma-aem1-10m", "pragma-aem1-10", "pragma-aem1-11", "pragma-aem1-12",
}
MOVED = {"O3": ((2680, 520), (2735, 360)), "O4": ((2335, 1035), (2325, 965))}
EXPECTED_KEYS = {"point", "box"} | {f"{b}+corrections:s{s}" for b in ("point", "box") for s in range(3)}
MIN_PROMPT_HOLDOUT_PX = 60
MAX_ZIP_BYTES = 25 * 2**20   # para poder adjuntarlo en el chat con margen

checks = []


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check(name, condition, detail=""):
    row = {"name": name, "pass": bool(condition)}
    if detail:
        row["detail"] = str(detail)
    checks.append(row)
    if not condition:
        raise AssertionError(f"{name}: {detail}")


def codex_checks():
    source = CODEX_VERIFIER.read_text(encoding="utf-8")
    check("codex_verifier_hash", sha256(CODEX_VERIFIER) == CODEX_VERIFIER_SHA256)
    old_nb = 'NOTEBOOK = ROOT / "outputs" / "PRAGMA_A-E-menos-1_diagnostico_caso_chica_Codex.ipynb"'
    old_report = 'REPORT = ROOT / "outputs" / "PRAGMA_A-E-menos-1_Codex_verificacion.json"'
    scratch = LOCAL / "codex_checks_on_v1_2.json"
    scratch.parent.mkdir(parents=True, exist_ok=True)
    source = source.replace(old_nb, f"NOTEBOOK = Path({str(V12)!r})").replace(old_report, f"REPORT = Path({str(scratch)!r})")
    exec(compile(source, str(CODEX_VERIFIER), "exec"), {"__file__": str(CODEX_VERIFIER), "__name__": "codex_on_v1_2"})
    codex = json.loads(scratch.read_text(encoding="utf-8"))
    check("codex_68_checks_on_v1_2", codex["checks_passed"] == 68 and all(c["pass"] for c in codex["checks"]),
          f"{codex['checks_passed']} checks")
    return codex["checks_passed"]


def specs_of(nb):
    code = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
    return {sid: {"xy": (int(x), int(y)), "group": g, "description": d}
            for sid, x, y, g, d in SPEC_PATTERN.findall(code) if not sid.startswith("S")}


def static_checks():
    check("v1_1_source_hash", sha256(V11) == V11_SHA256)
    v11 = json.loads(V11.read_text(encoding="utf-8"))
    v12 = json.loads(V12.read_text(encoding="utf-8"))
    check("same_cell_order", [c["id"] for c in v11["cells"]] == [c["id"] for c in v12["cells"]])
    changed = {a["id"] for a, b in zip(v11["cells"], v12["cells"]) if a != b}
    check("only_expected_cells_changed", changed == EXPECTED_CHANGED_CELLS, sorted(changed ^ EXPECTED_CHANGED_CELLS))

    s11, s12 = specs_of(v11), specs_of(v12)
    check("sentinel_ids_preserved", set(s11) == set(s12) and len(s12) == 18)
    for sid, (old, new) in MOVED.items():
        check(f"moved:{sid}", s11[sid]["xy"] == old and s12[sid]["xy"] == new and s12[sid]["group"] == "drop_other_person")
    untouched = [sid for sid in s11 if sid not in MOVED and s11[sid]["xy"] != s12[sid]["xy"]]
    check("other_16_coordinates_unchanged", not untouched, untouched)
    check("no_pending_ownership_flags", not any("CONFIRMAR PROPIETARIO" in s["description"] for s in s12.values()))
    prompts = [(k, s["xy"]) for k, s in s12.items() if s["group"].startswith("prompt_")]
    holdouts = [(k, s["xy"]) for k, s in s12.items() if not s["group"].startswith("prompt_")]
    closest = min((math.dist(a, b), pa, hb) for pa, a in prompts for hb, b in holdouts)
    check("min_prompt_holdout_distance", closest[0] >= MIN_PROMPT_HOLDOUT_PX, f"{closest[0]:.0f}px {closest[1]}↔{closest[2]}")

    code = {c["id"]: "".join(c["source"]) for c in v12["cells"]}
    check("expected_luma_covers_all_sentinels", set(PREFLIGHT_EXPECTED_LUMA) == set(s12))
    check("confirmation_default_true_and_attributed",
          'AEM1_CONFIG_CONFIRMADA = True # @param' in code["pragma-aem1-06"] and "AEM1_CONFIG_CONFIRMED_BY" in code["pragma-aem1-06"])
    tree06 = ast.parse(code["pragma-aem1-06"])
    ready = [n for n in tree06.body if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "AEM1_CONFIG_READY" for t in n.targets)]
    check("ready_bound_to_preflight_match",
          len(ready) == 1 and "AEM1_PREFLIGHT_MATCH" in ast.unparse(ready[0].value) and "AEM1_CONFIG_CONFIRMADA" in ast.unparse(ready[0].value),
          ast.unparse(ready[0]) if ready else "sin asignación")
    embedded = next((n for n in tree06.body if isinstance(n, ast.FunctionDef) and n.name == "sentinel_contact_sheet"), None)
    check("contact_sheet_function_identical_to_kit",
          embedded is not None and ast.dump(embedded) == ast.dump(ast.parse(inspect.getsource(sentinel_contact_sheet)).body[0]))

    # Invariante semántico (más fuerte que contar cadenas): toda llamada con mask_input usa multimask_output=False.
    offenders = []
    for cell_id, source in code.items():
        if not source.strip() or cell_id.endswith("m") or cell_id in ("pragma-aem1-00", "pragma-aem1-01", "pragma-aem1-12"):
            continue
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "generate_aem1":
                kw = {k.arg: k.value for k in node.keywords}
                if "mask_input" in kw and not (isinstance(kw.get("multimask_output"), ast.Constant)
                                               and kw["multimask_output"].value is False):
                    offenders.append(f"{cell_id}:{node.lineno}")
    check("corrections_single_mask_ast", not offenders, offenders)
    check("exhaustive_seeds_default", 'AEM1_SEEDS_CONFIRMADAS = False # @param' in code["pragma-aem1-09"]
          and 'AEM1_SEED_MODE = "manual" if AEM1_SEEDS_CONFIRMADAS else "exhaustive"' in code["pragma-aem1-09"])
    check("external_audit_state", code["pragma-aem1-10"].count('"PENDING_EXTERNAL_AUDIT"') == 1
          and 'elif AEM1_SELECTION is None:\n    AEM1_CASE_STATUS = "PENDING_EXTERNAL_AUDIT"' in code["pragma-aem1-11"])
    check("headless_flag", 'PRAGMA_HEADLESS = os.environ.get("PRAGMA_HEADLESS") == "1"' in code["pragma-aem1-03"])
    check("photo_found_by_hash_any_name", "def find_acceptance_image" in code["pragma-aem1-03"] and ".iterdir()" in code["pragma-aem1-03"])


def grounded_checks():
    try:
        from pragma_ae.imageio import load_rgb, locate_image
        path = locate_image()
    except FileNotFoundError as exc:
        return {"status": "SKIPPED_NO_IMAGE", "detail": str(exc)}, None
    v12 = json.loads(V12.read_text(encoding="utf-8"))
    specs = [(sid, s["xy"], s["group"], s["description"]) for sid, s in specs_of(v12).items()]
    stats = sentinel_contact_sheet(load_rgb(path), specs, LOCAL / "contact_sheet_v1_2.png")
    measured = {s["sentinel_id"]: s["patch_luma_mean"] for s in stats}
    deviation = max(abs(measured[k] - PREFLIGHT_EXPECTED_LUMA[k]) for k in measured)
    rows = {
        "expected_luma_matches_kit": deviation == 0.0,
        "moved_O3_dark_hair": measured["O3"] < 110,
        "moved_O4_not_plain_wall": 150 < measured["O4"] < 205,
    }
    return {"status": "PASS" if all(rows.values()) else "FAIL", "max_deviation": deviation, "rows": rows,
            "measured": {k: measured[k] for k in ("O3", "O4")}}, path


def e2e(image_path):
    results = {}
    # a) navegador (valores por defecto, como «Ejecutar todas»)
    ns, downloads, error = harness_aem1.run(V12, LOCAL / "browser", image_path=image_path)
    check("e2e_browser_no_error", error is None, repr(error))
    zip_path = Path(ns["ZIP_PATH"])
    check("e2e_browser_status", ns["AEM1_CASE_STATUS"] == "PENDING_EXTERNAL_AUDIT", ns["AEM1_CASE_STATUS"])
    check("e2e_browser_keys", set(ns["AEM1_PROPOSALS"]) == EXPECTED_KEYS, sorted(ns["AEM1_PROPOSALS"]))
    check("e2e_config_ready_by_evidence", ns["AEM1_CONFIG_READY"] and ns["AEM1_PREFLIGHT_MATCH"],
          max(ns["AEM1_PREFLIGHT_DEVIATION"].values()))
    check("e2e_download_once", downloads == [str(zip_path)], f"{len(downloads)} descarga(s) del ZIP de la corrida")
    with zipfile.ZipFile(zip_path) as archive:
        report = json.loads(archive.read("aem1_report.json"))
        manifest = json.loads(archive.read("aem1_manifest.json"))
        names = set(archive.namelist())
    check("e2e_report_fields", report["review_mode"] == "external_ai_audit" and report["seed_mode"] == "exhaustive"
          and report["phase_b_blocked"] is True and report["project_status"] == "INCONCLUSIVE_A_E0_REQUIRED")
    check("e2e_zip_matches_manifest", names == {e["name"] for e in manifest["entries"]} | {"aem1_manifest.json"})
    alpha = sorted(n for n in names if n.endswith("_alpha.png"))
    check("e2e_all_candidate_alphas", len(alpha) == 12, len(alpha))   # 3 + 3 + 6×1
    check("e2e_zip_attachable", zip_path.stat().st_size <= MAX_ZIP_BYTES, zip_path.stat().st_size)
    results["browser"] = {"status": ns["AEM1_CASE_STATUS"], "proposals": len(ns["AEM1_PROPOSALS"]),
                          "zip_bytes": zip_path.stat().st_size, "zip_entries": len(names), "downloads": len(downloads)}

    # b) sin navegador (Colab CLI)
    ns, downloads, error = harness_aem1.run(V12, LOCAL / "headless", image_path=image_path, headless=True)
    check("e2e_headless_no_error", error is None, repr(error))
    check("e2e_headless_status", ns["AEM1_CASE_STATUS"] == "PENDING_EXTERNAL_AUDIT")
    check("e2e_headless_no_download", downloads == [], f"{len(downloads)} descarga(s)")
    results["headless"] = {"status": ns["AEM1_CASE_STATUS"], "proposals": len(ns["AEM1_PROPOSALS"]), "downloads": len(downloads)}

    # c) sin foto y sin navegador: debe fallar con un mensaje claro, jamás abrir el selector
    ns, downloads, error = harness_aem1.run(V12, LOCAL / "headless_no_photo", image_path=None, headless=True,
                                            cells=["pragma-aem1-03"])
    check("e2e_headless_missing_photo_clear_error", isinstance(error, FileNotFoundError) and "sin navegador" in str(error),
          repr(error))
    results["headless_no_photo"] = {"error": type(error).__name__}
    return results, zip_path


def audit_checks(zip_path, image_path):
    """La auditoría IA debe leer exactamente el ZIP que exporta el cuaderno y no dejarse engañar por el arnés."""
    from pragma_ae.aem1_audit import CRITERIA, audit_zip, write_verdict
    from pragma_ae.imageio import load_rgb
    auto = audit_zip(zip_path, photo=load_rgb(image_path), out_dir=LOCAL / "audit_browser")
    check("audit_integrity_on_notebook_zip", auto["integrity"]["pass"], auto["integrity"]["problems"])
    check("audit_detects_simulated_run", auto["run_kind"] == "SIMULATED", auto["run_kind"])
    check("audit_reads_all_candidates", len(auto["candidates"]) == 12, len(auto["candidates"]))
    check("audit_sentinels_match_notebook", all(c["sentinels_match_report"] for c in auto["candidates"]))
    check("audit_renders_closeups", len(auto["evidence_files"]) == 13, len(auto["evidence_files"]))
    verdict = write_verdict(auto, auto["inspection_order"][0], {k: True for k in CRITERIA}, "", "verificador v1.2", ["arnés"])
    check("audit_simulated_never_evidence", verdict["case_status"] == "SIMULATED_RUN_NOT_EVIDENCE", verdict["case_status"])
    return {"status": "PASS", "run_kind": auto["run_kind"], "candidates": len(auto["candidates"]),
            "integrity": auto["integrity"]["pass"], "verdict_on_simulated": verdict["case_status"]}


def main():
    codex = codex_checks()
    static_checks()
    grounded, image_path = grounded_checks()
    if grounded["status"] == "FAIL":
        raise AssertionError(f"grounded: {grounded}")
    harness = {"status": "SKIPPED_NO_IMAGE"}
    audit = {"status": "SKIPPED_NO_IMAGE"}
    if image_path is not None:
        results, zip_path = e2e(image_path)
        harness = {"status": "PASS", "results": results, "sample_zip_for_audit_tests": str(zip_path.relative_to(ROOT)),
                   "scope": "SAM, torch y google.colab simulados; prueba flujo, estados y empaquetado, no calidad de segmentación"}
        audit = audit_checks(zip_path, image_path)
    payload = {
        "artifact": V12.name,
        "artifact_bytes": V12.stat().st_size,
        "artifact_sha256": sha256(V12),
        "source_artifact_sha256": V11_SHA256,
        "verification_status": "STATIC_AND_SIMULATED_E2E_PASS" if harness["status"] == "PASS" else "STATIC_VERIFICATION_PASS",
        "experiment_status": "NOT_RUN",
        "codex_checks_passed": codex,
        "v1_2_checks_passed": len(checks),
        "checks": checks,
        "grounded_checks": grounded,
        "e2e_simulated_sam": harness,
        "audit_tool_on_notebook_zip": audit,
        "limitations": [
            "SAM 2 no se ejecutó: las máscaras del arnés son geométricas y simuladas.",
            "La confirmación de la configuración es del auditor IA; queda ligada a la luminancia de los 18 parches.",
        ],
    }
    REPORT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("verification_status", "experiment_status", "codex_checks_passed",
                                               "v1_2_checks_passed", "artifact_sha256")}
                     | {"grounded": grounded["status"], "e2e": harness["status"]}, indent=2))


if __name__ == "__main__":
    main()
