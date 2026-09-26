"""Contrato de análisis de A-E1 (ChatGPT 003): liga el sweep inspeccionado al código y umbrales que lo medirán.

Uso:
    python3 work/ae1_analysis_contract.py            # escribe ae1/CONTRATO_ANALISIS_A-E1.json
    python3 work/ae1_analysis_contract.py --check    # comprueba que el código y los umbrales no cambiaron

El sweep (`ae1/SWEEP_PRERREGISTRO_A-E1.json`) queda PREREGISTERED tal como lo inspeccionó ChatGPT y
no se toca. Este contrato añade lo que faltaba para el experimento completo: el SHA-256 de la
implementación de métricas y todos los umbrales. Se queda en DRAFT hasta que A-E0 se congele. Ese
mismo commit lo congela, y cualquier cambio posterior de las métricas exige una versión nueva.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pragma_ae.metrics import GateParams  # noqa: E402

SWEEP = ROOT / "ae1" / "SWEEP_PRERREGISTRO_A-E1.json"
SWEEP_SHA256_INSPECTED = "25a61aa98ec7db261d837ba4129474905f41bfedb28cc76e599ef920172d5a38"
OUT = ROOT / "ae1" / "CONTRATO_ANALISIS_A-E1.json"
IMPLEMENTATION = ["pragma_ae/metrics.py", "pragma_ae/masks.py", "pragma_ae/inventory.py"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    if sha(SWEEP) != SWEEP_SHA256_INSPECTED:
        raise SystemExit("El sweep no es el que ChatGPT inspeccionó: no se liga el contrato")
    params = {k: (list(v) if isinstance(v, tuple) else v) for k, v in dataclasses.asdict(GateParams()).items()}
    payload = {
        "schema": "pragma.ae1_analysis_contract",
        "schema_version": "0.1.0",
        "status": "DRAFT_FREEZES_WITH_A_E0",
        "sweep": {"file": SWEEP.relative_to(ROOT).as_posix(), "sha256": SWEEP_SHA256_INSPECTED,
                  "status": "PREREGISTERED", "cross_audit": "ChatGPT 003: las cuatro configuraciones, aceptadas sin cambios"},
        "full_experiment": "NOT_YET_FULLY_PREREGISTERED",
        "gates": {
            "A_E0_FROZEN": "REQUIRED: el inventario se congela por hash antes de mirar ninguna salida A-E1",
            "METRICS_CONTRACT_FROZEN": "REQUIRED: este archivo pasa a FROZEN en el mismo commit que A-E0",
            "SAM2_FREEZE": "el del sweep (commit, checkpoint, imagen)",
            "REFERENCE_TYPE_DECLARED": ("REQUIRED (DEC-024, ChatGPT 005): cada métrica registra contra qué referencia se "
                                        "calculó: AI_CONSENSUS_REFERENCE (producida y adjudicada solo por IA) o HUMAN_GT "
                                        "(ratificada píxel a píxel por personas), y la derivation de cada máscara"),
        },
        "reference_types": {
            "AI_CONSENSUS_REFERENCE": "ingeniería y comparación interna; nunca se presenta como exactitud frente a verdad humana",
            "HUMAN_GT": "solo si una muestra se anota o ratifica de forma independiente por personas",
            "report_by_derivation": "las métricas contra máscaras derivadas de prompts de SAM 2 se reportan aparte (circularidad)",
        },
        "metrics_implementation_sha256": {p: sha(ROOT / p) for p in IMPLEMENTATION},
        "entrypoint": "pragma_ae.metrics.evaluate(objects, gt_masks, proposals, GateParams())",
        "gate_params": params,
        "verdict_order": ["INCONCLUSIVE_GT_INCOMPLETE", "GATE_NOT_MET:…", "INCONCLUSIVE_FUSION_NOT_EVALUABLE", "GATE_MET"],
        "reported_not_gating": ["contact_leak (DEC-014-P)", "fusión según P (DEC-013-P, junto a Q)",
                                "tier_a_box_screen_failures", "duplicados", "fragmentación"],
        "rule": "si cambia un SHA-256 o un umbral de este contrato después de congelarlo, el análisis A-E1 es otra versión y se declara",
    }
    body = {k: v for k, v in payload.items()}
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
        print("contrato A-E1 reproducido byte a byte:", same)
        raise SystemExit(0 if same else 1)
    OUT.write_text(text, encoding="utf-8")
    print("escrito:", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
