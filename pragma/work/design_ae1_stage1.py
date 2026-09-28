"""Protocolo de lectura de A‑E1 etapa 1 (ChatGPT 019), generado y comprobable byte a byte.

    python3 work/design_ae1_stage1.py            # escribe ae1/AE1_STAGE1_READING_PROTOCOL.json
    python3 work/design_ae1_stage1.py --check    # comprueba que nada de lo ligado cambió

Liga por SHA‑256:
- el contrato A‑E1 congelado y el sweep prerregistrado;
- el inventario A‑E0 congelado;
- el lector ``pragma_ae/ae1_stage1.py``.
Fija el plan exacto de las 4 llamadas AMG y las reglas R1–R4. No toca el contrato, ni ``metrics.py``, ni
A‑E0, ni las configuraciones. El GO a la GPU es aparte: lo da ChatGPT después de revisar esto.
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
        "schema_version": "0.1.0",
        "status": "PREREGISTERED",
        "gpu_gate": "HOLD: la GPU espera un GO separado de ChatGPT tras revisar este protocolo, el cuaderno y su verificador (019)",
        "origin": "carta 019 (ORDEN 190) con las correcciones de ChatGPT 019 (ORDEN 191): R1 con revisión ciega por configuración, R2 con cotas a nivel de conjunto, R3 diagnóstico, R4 con una persona basta",
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
            "precision": "torch.autocast CUDA en bfloat16 si la capacidad es ≥ 8 (L4); float16 si es menor",
            "image": "RGB HWC uint8 tras exif_transpose, 2248×4000; la foto se reconoce por SHA-256",
            "device": "GPU CUDA; se recomienda L4, como en las corridas anteriores",
        },
        "call_plan": s1.call_plan(sweep),
        "operational": {
            "points_per_batch": "empieza en 64; solo baja por OOM (64 → 32 → 16), y cada intento queda registrado (regla del sweep)",
            "output": "uncompressed_rle por máscara, con su packed_sha256 (cabecera «HxW:» + np.packbits)",
            "no_results_in_colab": "el cuaderno solo imprime el progreso; no muestra máscaras, número de máscaras ni scores",
        },
        "run_validity": {
            "REAL_GPU_EVIDENCE": "integridad sin problemas, commit y checkpoint congelados, foto por hash, CUDA",
            "SIMULATED_RUN_NOT_EVIDENCE": "arnés con SAM simulado: prueba el cuaderno, nunca es resultado",
            "REAL_CPU_NOT_EVIDENCE": "sin CUDA: no se lee",
            "INVALID_BUNDLE": "manifiesto, kwargs, hashes de máscara o regla de points_per_batch rotos: no se lee",
        },
        "rules": {
            "R1": {
                "name": "BOX_SCREEN_FAILURE",
                "trigger": f"objeto Tier A cuya mejor IoU de caja (caja declarada del inventario frente a mask_bbox de cada propuesta) es < {s1.BOX_THRESHOLD} en las cuatro configuraciones",
                "candidates": f"las {s1.TOP_PER_CONFIG} mejores propuestas por IoU de caja POR CONFIGURACIÓN (≤ 12), deduplicadas por packed_sha256; empates por índice menor",
                "blinding": "sin configuración, score SAM ni ranking; orden aleatorio con semilla fija; mapeo sellado fuera del paquete",
                "sheet": "recorte del objeto con su caja en verde y cada candidata en magenta, con miniatura de la foto entera; etiquetas con nombre (ae0_044, ae0_045) tapadas siempre",
                "seed": s1.BLIND_SEED,
                "answers": list(s1.KEY_ANSWERS),
                "confirmed": "CONFIRMED_BOX_SCREEN_FAILURE solo si las dos llaves dicen MISS; cualquier desacuerdo o CANNOT_DETERMINE no para nada",
                "keys": "Claude compromete sus respuestas por SHA-256 antes de archivar las de ChatGPT; ChatGPT recibe solo el paquete ciego",
                "wording": "BOX_SCREEN_FAILURE: no demuestra que ninguna propuesta posible contenga el objeto",
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
            "2. disparadores de R1 (solo cajas); si los hay: paquete ciego → llave de Claude por hash → llave de ChatGPT",
            "3. solo con las dos llaves de R1: R2, R3 y R4 (ae1_stage1.analyze)",
            "4. informe con el techo de la etapa y la decisión de R4",
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
