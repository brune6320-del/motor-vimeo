"""Protocolo de lectura de A‑E1 etapa 1 (ChatGPT 019 y 020), generado y comprobable byte a byte.

    python3 work/design_ae1_stage1.py            # escribe ae1/AE1_STAGE1_READING_PROTOCOL.json
    python3 work/design_ae1_stage1.py --check    # comprueba que nada de lo ligado cambió

Liga por SHA‑256:
- el contrato A‑E1 congelado y el sweep prerregistrado;
- el inventario A‑E0 congelado;
- el lector ``pragma_ae/ae1_stage1.py``.
Fija el plan exacto de las 4 llamadas AMG, la compuerta de precisión y las reglas R1–R4. No toca el
contrato, ni ``metrics.py``, ni A‑E0, ni las configuraciones. El GO a la GPU es aparte: lo da ChatGPT
después de revisar esto.

v0.2.0 (ChatGPT 020, ORDEN 201): el triaje de R1 ya no confirma nada por sí solo (revisión exhaustiva) y
solo es evidencia una corrida CUDA en bfloat16 con capacidad ≥ 8. Sustituye a la v0.1.0.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pragma_ae import ae1_stage1 as s1  # noqa: E402

CONTRACT = ROOT / "ae1" / "CONTRATO_ANALISIS_A-E1.json"
SWEEP = ROOT / "ae1" / "SWEEP_PRERREGISTRO_A-E1.json"
INVENTORY = ROOT / "ae0" / "scene_inventory.json"
READER = ROOT / "pragma_ae" / "ae1_stage1.py"
OUT = ROOT / "ae1" / "AE1_STAGE1_READING_PROTOCOL.json"
AMG_EXAMPLE_SHA256 = "a503375b91ea76d463af8b12955e60270abede74937a2eda613eb3330ad56501"
AMG_SOURCE_SHA256 = "66df266dbe14412305ae3398f0ec1bb21b303a93216b102d767e6c4ee5d4c3d7"
BUILD_SAM_SHA256 = "856d64d71e44407401297b551884fb4cd1aba8082de0ff5fc60fac3dd42f094d"
SUPERSEDES = {"schema_version": "0.1.0",
              "file_sha256": "810818759e402c4df870de80ea03211c1737935722c96e51d516a1cde535dc98",
              "content_sha256": "d40cc5c4a3f3256421a40b28611611b68023bf515ae5e52bb2f6d836e928b57b",
              "reviewed_in": "dialogo/020_chatgpt_a_claude.md (ORDEN 201): R1_TOP3_AS_EARLY_STOP = REJECTED, GPU_BF16_GATE = REQUIRED"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    sweep = json.loads(SWEEP.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    if contract["status"] != "FROZEN" or inventory["status"] != "FROZEN":
        raise SystemExit("el contrato A-E1 y A-E0 tienen que estar congelados")
    if contract["sweep"]["sha256"] != sha(SWEEP) or contract["a_e0_reference"]["inventory"]["file_sha256"] != sha(INVENTORY):
        raise SystemExit("el sweep o el inventario no son los que liga el contrato")
    tier_a = [o["id"] for o in inventory["objects"] if o["tier"] == "A"]
    with_mask = [o["id"] for o in inventory["objects"] if o["tier"] == "A" and o["gt_mask"]]
    payload = {
        "schema": "pragma.ae1_stage1_reading_protocol",
        "schema_version": "0.2.0",
        "status": "PREREGISTERED",
        "gpu_gate": "HOLD: la GPU espera el GO de ChatGPT tras revisar esta versión, el cuaderno y su verificador (ChatGPT 020)",
        "origin": "carta 019 (ORDEN 190) con las correcciones de ChatGPT 019 (ORDEN 191: R1 ciega por configuración, R2 con cotas a nivel de conjunto, R3 diagnóstico, R4 con una persona basta) y de ChatGPT 020 (ORDEN 201: triaje → revisión exhaustiva, compuerta bfloat16)",
        "supersedes": SUPERSEDES,
        "binds": {
            "contract": {"file": CONTRACT.relative_to(ROOT).as_posix(), "sha256": sha(CONTRACT),
                         "content_sha256": contract["content_sha256"]},
            "sweep": {"file": SWEEP.relative_to(ROOT).as_posix(), "sha256": sha(SWEEP)},
            "a_e0": {"file": INVENTORY.relative_to(ROOT).as_posix(), "sha256": sha(INVENTORY),
                     "content_sha256": inventory["freeze"]["content_sha256"],
                     "reference_type": inventory["freeze"]["reference_type"]},
            "reader": {"file": READER.relative_to(ROOT).as_posix(), "sha256": sha(READER)},
            "metrics_implementation_sha256": contract["metrics_implementation_sha256"],
        },
        "stage": {"name": "ETAPA_1", "tier_a": len(tier_a), "tier_a_with_mask": with_mask,
                  "ceiling": "INCONCLUSIVE_GT_INCOMPLETE",
                  "never": "PASS_PROPOSALS: ningún informe de esta etapa la convierte en PASS, aunque los resultados sean buenos",
                  "role": "cribado de falsación / parada temprana, no validación completa"},
        "freeze": {k: sweep["freeze"][k] for k in ("SAM2_GIT_COMMIT", "MODEL_CONFIG", "CHECKPOINT_FILENAME",
                                                    "CHECKPOINT_SHA256", "IMAGE_SHA256", "IMAGE_H_x_W")},
        "model": {
            "build": "build_sam2(MODEL_CFG, CHECKPOINT, device=DEVICE, apply_postprocessing=False)",
            "generator": "SAM2AutomaticMaskGenerator(model, **generator_kwargs).generate(image)",
            "why_no_postprocessing": "es lo que hace el ejemplo oficial de AMG en el commit congelado",
            "sources_at_commit": {"notebooks/automatic_mask_generator_example.ipynb": AMG_EXAMPLE_SHA256,
                                  "sam2/automatic_mask_generator.py": AMG_SOURCE_SHA256,
                                  "sam2/build_sam.py": BUILD_SAM_SHA256},
            "precision": f"torch.autocast CUDA en bfloat16; exige capacidad CUDA ≥ {s1.MIN_BF16_CAPABILITY} (L4, A100, H100). La celda 0 se detiene antes de instalar si no la hay (FAIL_ENVIRONMENT) y la celda 4 lo vuelve a exigir antes de cargar el modelo",
            "image": "RGB HWC uint8 tras exif_transpose, 2248×4000; la foto se reconoce por SHA-256",
            "device": "GPU CUDA con bfloat16 nativo; se usa L4, como en las corridas anteriores (no se exige el nombre de la GPU)",
        },
        "call_plan": s1.call_plan(sweep),
        "operational": {
            "points_per_batch": "empieza en 64; solo baja por OOM (64 → 32 → 16), y cada intento queda registrado (regla del sweep)",
            "output": "uncompressed_rle por máscara, con su packed_sha256 (cabecera «HxW:» + np.packbits)",
            "no_results_in_colab": "el cuaderno solo imprime el progreso; no muestra máscaras, número de máscaras ni scores",
        },
        "run_validity": {
            "REAL_GPU_EVIDENCE": f"integridad sin problemas, commit y checkpoint congelados, foto por hash, y device = cuda, dtype = bfloat16 y cuda_capability[0] ≥ {s1.MIN_BF16_CAPABILITY}",
            "REAL_GPU_DIFFERENT_PRECISION_NOT_EVIDENCE": "CUDA sin bfloat16 (capacidad < 8, float16; p. ej. T4): no se lee",
            "SIMULATED_RUN_NOT_EVIDENCE": "arnés con SAM simulado: prueba el cuaderno, nunca es resultado",
            "REAL_CPU_NOT_EVIDENCE": "sin CUDA: no se lee",
            "INVALID_BUNDLE": "manifiesto, kwargs, hashes de máscara o regla de points_per_batch rotos, o cuda_capability ausente o incoherente con el dtype (la regla del cuaderno: capacidad ≥ 8 → bfloat16, < 8 → float16): no se lee",
        },
        "rules": {
            "R1": {
                "name": "BOX_SCREEN_FAILURE",
                "trigger": f"objeto Tier A cuya mejor IoU de caja (caja declarada del inventario frente a mask_bbox de cada propuesta) es < {s1.BOX_THRESHOLD} en las cuatro configuraciones",
                "phases": {
                    "R1_TRIAGE": {
                        "candidates": f"las {s1.TOP_PER_CONFIG} mejores propuestas por IoU de caja POR CONFIGURACIÓN (≤ 12), deduplicadas por packed_sha256; empates por índice menor",
                        "outcome": "si una llave dice COVERS_OBJECT o CANNOT_DETERMINE: NOT_CONFIRMED. Si las dos dicen MISS: ESCALATE_TO_EXHAUSTIVE, que todavía NO es un fallo",
                        "package": "PRAGMA_AE1S1_revision_ciega_R1.zip, una lámina Rnn.png por objeto; mapeo sellado sealed_mapping.json",
                    },
                    "R1_EXHAUSTIVE_BLIND_REVIEW": {
                        "when": "solo para los objetos que el triaje escala, y después de archivar las dos llaves del triaje",
                        "candidates": "TODAS las propuestas únicas de las cuatro configuraciones cuya mask_bbox tiene intersección de área no vacía con la caja congelada del objeto (cajas semiabiertas, la convención de box_iou); deduplicadas por packed_sha256; sin tope",
                        "pages": f"láminas Rnn_pPP.png de hasta {s1.PAGE_SIZE} candidatas, tantas como hagan falta; cada una repite el objeto",
                        "outcome": "CONFIRMED_BOX_SCREEN_FAILURE solo si las dos llaves revisan todas las láminas (reviewed_all_pages = true) y dicen MISS. Una candidata encontrada por cualquiera → NOT_CONFIRMED. CANNOT_DETERMINE, o un MISS sin reviewed_all_pages = true → NOT_CONFIRMED",
                        "package": "PRAGMA_AE1S1_revision_ciega_R1_exhaustiva.zip; mapeo sellado sealed_mapping_exhaustivo.json; mismas etiquetas de objeto Rnn que el triaje",
                    },
                },
                "blinding": "sin configuración, score SAM ni ranking; orden aleatorio con semilla fija (un generador nuevo para cada paquete); mapeo sellado fuera del paquete",
                "sheet": "recorte del objeto con su caja en verde y cada candidata en magenta, con miniatura de la foto entera; etiquetas con nombre (ae0_044, ae0_045) tapadas siempre",
                "seed": s1.BLIND_SEED,
                "answers": list(s1.KEY_ANSWERS),
                "keys": "en cada fase, Claude compromete sus respuestas por SHA-256 antes de archivar las de ChatGPT; ChatGPT recibe solo el paquete ciego",
                "wording": "BOX_SCREEN_FAILURE: el triaje no demuestra nada por sí solo; confirmado, significa que ninguna propuesta de este sweep contiene el objeto según las dos llaves",
            },
            "R2": {
                "per_proposal": "iou_estimate, iou_min, iou_max: los de keydiff.iou_with_uncertainty (redondeo a 6 decimales), con U = uncertain_path de la persona y F = gt_mask ∖ U",
                "per_person_config": "best_estimate = max iou_estimate (oráculo descriptivo); best_robust_min = max iou_min; best_possible_max = max iou_max; y los tres argmax (índice menor en empates)",
                "threshold": s1.STAGE_THRESHOLD,
                "verdict": {"PASS": "best_robust_min ≥ 0,70", "FAIL": "best_possible_max < 0,70",
                            "DEPENDS_ON_UNCERTAINTY": "en otro caso"},
            },
            "R3": {"label": "FUSION_Q_ESTIMATE_BASED",
                   "params": "los del contrato: regla Q, τ = 0,10, erosión 5 px, banda de contacto 24 px, umbral 0,20",
                   "status": "diagnóstico: la fusión se mide contra la estimación binaria y no tiene cotas; nunca es early-stop por sí sola"},
            "R4": {"FAIL_COMPONENT": "≥ 1 CONFIRMED_BOX_SCREEN_FAILURE, o ≥ 1 persona con R2 = FAIL en las cuatro configuraciones",
                   "otherwise": "INCONCLUSIVE_GT_INCOMPLETE → etapa 2 (máscaras de los 35 Tier A restantes, por doble llave)",
                   "never_fail": "un DEPENDS_ON_UNCERTAINTY nunca produce FAIL; un FAIL en menos de cuatro configuraciones tampoco"},
        },
        "order": [
            "1. integridad del ZIP sin mirar resultados (ae1_stage1.integrity)",
            "2. disparadores de R1 (solo cajas); si los hay: triaje ciego → llave de Claude por hash → llave de ChatGPT",
            "3. si el triaje escala algún objeto: revisión exhaustiva ciega → llave de Claude por hash → llave de ChatGPT",
            "4. solo con R1 resuelto para todos los objetos disparados: R2, R3 y R4 (ae1_stage1.analyze)",
            "5. informe con el techo de la etapa y la decisión de R4",
        ],
        "privacy": "las máscaras de SAM 2 derivan de la foto: van a local/, y a git solo hashes y cifras",
    }
    body = dict(payload)
    payload["content_sha256"] = hashlib.sha256(
        json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    return payload


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    text = json.dumps(build(), indent=2, ensure_ascii=False) + "\n"
    if args.check:
        same = OUT.read_text(encoding="utf-8") == text
        print("protocolo A-E1 etapa 1 reproducido byte a byte:", same)
        raise SystemExit(0 if same else 1)
    OUT.write_text(text, encoding="utf-8")
    print("escrito:", OUT.relative_to(ROOT), "·", hashlib.sha256(OUT.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
