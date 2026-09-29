import ast
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "outputs" / "PRAGMA_A-E-menos-1_diagnostico_caso_chica_Codex.ipynb"
BASE = ROOT / "outputs" / "PRAGMA_Fase_A_SAM2_v4_ligero.ipynb"
CLAUDE_AEM1 = ROOT / "outputs" / "claude_originals" / "PRAGMA_A-E-1_cierre_fase_A_celdas.md"
CLAUDE_PATCH = ROOT / "outputs" / "claude_originals" / "PRAGMA_Fase_A_v4_parche.md"
REPORT = ROOT / "outputs" / "PRAGMA_A-E-menos-1_Codex_verificacion.json"

EXPECTED = {
    "base": "757e9722aa98a4d9420fdca4f287ef36fe78d7b09e2b9e12b3be6896e76e814a",
    "claude_aem1": "7e832ff61d28077612b9c4cabc4274669b09884f06ab340653e4cc259ace4e91",
    "claude_patch": "d5c05f4c2c02026e8ef34baec11b606c28bc1d6f3ae71d643b028548845fe722",
    "image": "8f6e3b6f5013265a45c7e89121e3f0a18e3386951e2e75378b28da6d02ec529d",
}


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(name, condition, detail=""):
    result = {"name": name, "pass": bool(condition)}
    if detail:
        result["detail"] = detail
    checks.append(result)
    if not condition:
        raise AssertionError(f"{name}: {detail}")


checks = []
check("base_hash", sha256(BASE) == EXPECTED["base"], sha256(BASE))
check("claude_aem1_archived_byte_exact", sha256(CLAUDE_AEM1) == EXPECTED["claude_aem1"], sha256(CLAUDE_AEM1))
check("claude_patch_archived_byte_exact", sha256(CLAUDE_PATCH) == EXPECTED["claude_patch"], sha256(CLAUDE_PATCH))

nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
check("nbformat", nb.get("nbformat") == 4 and nb.get("nbformat_minor") == 5)
check("cell_count", len(nb["cells"]) == 23, str(len(nb["cells"])))
check("unique_cell_ids", len({c["id"] for c in nb["cells"]}) == len(nb["cells"]))

code_cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
markdown_cells = [c for c in nb["cells"] if c["cell_type"] == "markdown"]
check("code_cell_count", len(code_cells) == 10, str(len(code_cells)))
check("markdown_cell_count", len(markdown_cells) == 13, str(len(markdown_cells)))
check("clean_execution_counts", all(c.get("execution_count") is None for c in code_cells))
check("no_saved_outputs", all(c.get("outputs") == [] for c in code_cells))

syntax = []
for cell in code_cells:
    src = "".join(cell["source"])
    ast.parse(src, filename=cell["id"])
    syntax.append(cell["id"])
check("all_code_cells_parse", len(syntax) == len(code_cells), ", ".join(syntax))

all_text = "\n".join("".join(c["source"]) for c in nb["cells"])
all_code = "\n".join("".join(c["source"]) for c in code_cells)
for forbidden in ("<i>", "<la candidata elegida>", "BOX_CHICA = (x_min", "eval_js", "ClickSelector(", "np.argmax", "register_proposal("):
    check(f"forbidden_absent:{forbidden}", forbidden not in all_text)
check("exact_image_hash_present", EXPECTED["image"] in all_code)
check("dtype_dispatch_t4", 'select_precision(True, (7, 5))["dtype"] == "float16"' in all_code)
check("dtype_dispatch_ampere", 'select_precision(True, (8, 0))["dtype"] == "bfloat16"' in all_code)
check("dtype_dispatch_cpu", 'select_precision(False)["dtype"] == "float32"' in all_code)
check("no_model_downgrade", "sam2.1_hiera_large.pt" in all_code and "hiera_small" not in all_code)
check("manual_candidate_selection", "AEM1_SELECTED_CANDIDATE" in all_code and "ELIGE POR CONTENIDO" in all_code)
check("iterative_mask_input", "mask_input=AEM1_PROPOSALS" in all_code)
check("corrected_single_mask", all_code.count("multimask_output=False") >= 2)
check("four_protocols", all(name in all_code for name in ("point", "box", "point+corrections", "box+corrections")))
check("selector_module_executed", "class FixedProtocolSelector" in all_code and "pipeline.selector = AEM1_SELECTOR" in all_code)
check("selector_protocol_method_executed", "def select(self, image, subject, detections)" in all_code and "pipeline.selector.select(" in all_code)
check("phase_b_always_blocked", '"phase_b_blocked": True' in all_code and '"phase_b_blocked": False' not in all_code)
check("no_extension_or_phase_b_mutation", "pragma-extension.zip" not in all_code and "FastAPI" not in all_code)
check("whitelist_not_directory_glob", "current_proposal_artifacts" in all_code and ".glob(" not in all_code)
check("zip_roundtrip_hash_verification", "archive.read(name)" in all_code and "hashlib.sha256(payload).hexdigest()" in all_code)
check("pragma_resource_metrics", '"parameter_count"' in all_code and '"peak_gpu_gib_at_export"' in all_code)
check("aem1_namespace_distinct_from_ae1_inventory", "AEM1_" in all_code and "AE1_" not in all_code)
check("protocol_completion_gate", 'elif not AEM1_PROTOCOLS_COMPLETE:' in all_code and 'AEM1_CASE_STATUS = "PENDING_PROTOCOLS"' in all_code)
check("config_digest_bound", "config_digest=AEM1_CONFIG_DIGEST" in all_code and '"config_digest": AEM1_CONFIG_DIGEST' in all_code)
check("rerun_invalidation", all_code.count("invalidate_aem1_review(") >= 3)
check("selection_referential_integrity", "def validate_selection_binding" in all_code and "proposal_id no pertenece al registro actual" in all_code)
check("selected_evidence_hash_rechecked", "evidencia alterada:" in all_code and "SELECTION_BINDING_VALID" in all_code)
check("human_review_bound_to_selection", "AEM1_REVIEWED_SELECTION_ID" in all_code and "PENDING_REVIEW_BINDING" in all_code)
check("no_false_case_fail_status", "FAIL_CASE_UNDER_FIXED" not in all_text and "INCONCLUSIVE_SELECTED_OUTPUT_FAILED" in all_text)
check("closeup_evidence", "PRIMEROS PLANOS OBLIGATORIOS" in all_code and "closeups_path" in all_code)
check("preview_downsampled", "def preview_on_checker" in all_code and "max_side=1400" in all_code)
check("oom_embedding_and_prompt", all_code.count("FAIL_ENVIRONMENT: OOM") >= 2)
check("atomic_zip", "ZIP_TEMP_PATH.replace(ZIP_PATH)" in all_code)
check("artifact_path_guard", "path.resolve().parent == RUN_DIR.resolve()" in all_code)
check("manifest_bytes_verified", "archive.read(MANIFEST_PATH.name)" in all_code)

spec_matches = re.findall(
    r'SentinelSpec\("([A-Z+\-0-9]+)", \((\d+), (\d+)\), "([a-z_]+)"',
    all_code,
)
specs = [{"id": i, "xy": (int(x), int(y)), "group": g} for i, x, y, g in spec_matches]
real_specs = [s for s in specs if not s["id"].startswith("S")]
check("sentinel_spec_count", len(real_specs) == 18 and len(specs) == 21, f"real={len(real_specs)}, synthetic={len(specs)-len(real_specs)}")
check("sentinel_ids_unique", len({s["id"] for s in specs}) == len(specs))
check("real_sentinel_coordinates_unique", len({s["xy"] for s in real_specs}) == len(real_specs))
prompt_xy = {s["xy"] for s in real_specs if s["group"].startswith("prompt_")}
holdout_xy = {s["xy"] for s in real_specs if not s["group"].startswith("prompt_")}
check("prompt_holdout_disjoint", prompt_xy.isdisjoint(holdout_xy))
check("drop_categories_separate", {s["group"] for s in real_specs} >= {"drop_other_person", "drop_background"})
check("rounded_bounds_guard", "Coordenada fuera de imagen tras redondear" in all_code)

# Demostración falsable: todos los puntos muestreados pueden estar limpios y aun existir una fuga no muestreada.
sampled_drop = {(10, 10), (20, 20), (30, 30)}
leak_pixels = {(70, 70), (71, 70), (72, 70)}
sentinel_clean = not bool(sampled_drop & leak_pixels)
global_leak_exists = bool(leak_pixels)
check("sentinels_do_not_prove_global_cleanliness", sentinel_clean and global_leak_exists)
check(
    "sentinel_requires_human_review",
    "def derive_aem1_case_status" in all_code
    and 'review["complete"]' in all_code
    and 'metrics["sentinel_screen_pass"]' in all_code,
)

def status(config_ready, protocols_complete, selection_present, review_complete, review_bound,
           visual_checks, sentinel_screen, notes):
    if not config_ready:
        return "PENDING_CONFIG"
    if not protocols_complete:
        return "PENDING_PROTOCOLS"
    if not selection_present or not review_complete:
        return "PENDING_REVIEW"
    if not review_bound:
        return "PENDING_REVIEW_BINDING"
    if not all(visual_checks) and not notes:
        return "PENDING_NOTES"
    if sentinel_screen and all(visual_checks):
        return "SEPARATION_DEMONSTRATED_UNDER_FIXED_AEM1_PROTOCOL"
    return "INCONCLUSIVE_SELECTED_OUTPUT_FAILED"


check("truth_config_gate", status(False, True, True, True, True, [True]*4, True, "") == "PENDING_CONFIG")
check("truth_protocol_gate", status(True, False, True, True, True, [True]*4, True, "") == "PENDING_PROTOCOLS")
check("truth_pending_without_review", status(True, True, True, False, False, [True]*4, True, "") == "PENDING_REVIEW")
check("truth_review_binding", status(True, True, True, True, False, [True]*4, True, "") == "PENDING_REVIEW_BINDING")
check("truth_notes_required", status(True, True, True, True, True, [True, False, True, True], True, "") == "PENDING_NOTES")
check("truth_human_false_is_inconclusive", status(True, True, True, True, True, [True, False, True, True], True, "borde roto") == "INCONCLUSIVE_SELECTED_OUTPUT_FAILED")
check("truth_sentinel_false_is_inconclusive", status(True, True, True, True, True, [True]*4, False, "") == "INCONCLUSIVE_SELECTED_OUTPUT_FAILED")
check("truth_demonstration_requires_all_gates", status(True, True, True, True, True, [True]*4, True, "") == "SEPARATION_DEMONSTRATED_UNDER_FIXED_AEM1_PROTOCOL")

# Ejecuta la función pura extraída del notebook para que la tabla anterior no sea una copia decorativa.
derive_node = None
for cell in code_cells:
    tree = ast.parse("".join(cell["source"]))
    derive_node = next((node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "derive_aem1_case_status"), derive_node)
check("notebook_status_function_found", derive_node is not None)
namespace = {}
exec(compile(ast.Module(body=[derive_node], type_ignores=[]), "derive_aem1_case_status", "exec"), namespace)
notebook_status = namespace["derive_aem1_case_status"]
check("notebook_status_matches_protocol_gate", notebook_status(True, False, True, True, True, [True]*4, True, "") == "PENDING_PROTOCOLS")
check("notebook_status_matches_review_binding", notebook_status(True, True, True, True, False, [True]*4, True, "") == "PENDING_REVIEW_BINDING")
check("notebook_status_never_false_case_fail", notebook_status(True, True, True, True, True, [False, True, True, True], True, "defecto") == "INCONCLUSIVE_SELECTED_OUTPUT_FAILED")

payload = {
    "artifact": NOTEBOOK.name,
    "artifact_bytes": NOTEBOOK.stat().st_size,
    "artifact_sha256": sha256(NOTEBOOK),
    "verification_status": "STATIC_VERIFICATION_PASS",
    "experiment_status": "NOT_RUN",
    "checks_passed": len(checks),
    "checks": checks,
    "source_hashes": EXPECTED,
    "limitations": [
        "Validación local estática y lógica; no ejecuta SAM 2 ni CUDA.",
        "La prueba real pendiente debe correrse en Google Colab con la fotografía de aceptación.",
        "Los sentinelas son muestras locales; no reemplazan máscaras ground-truth.",
    ],
}
REPORT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({k: payload[k] for k in ("verification_status", "experiment_status", "checks_passed", "artifact_sha256")}, indent=2))
