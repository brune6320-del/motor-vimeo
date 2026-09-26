"""Adjudicación técnica A CIEGAS de la corrida v1.4 (protocolo v2 rev. 1 §5.2), antes del desciegue.

    python3 work/adjudicate_aem1_v1_4.py --zip <ZIP local> --mapping <sealed_mapping.json local>

El mapeo sellado se usa **solo** para leer la máscara de cada etiqueta. Nada de lo que imprime o
escribe este script nombra una rama, una semilla ni un candidato: todo va por etiqueta (N01…N06).

Reglas, fijadas y versionadas ANTES de medir (commit previo a su ejecución):

1. ``other_person_excluded`` (N01, N05). Regla prerregistrada en v1.4 (``adjudication_rules``):
   FALSE si hay píxeles de máscara en el núcleo oscuro del moño o islas separadas en el núcleo
   hombro/blusa (``pragma_ae.aem1_v14.measure_o``); si no, TRUE. Ninguna llave citó material
   posterior fuera de los núcleos: Claude citó (≈ 2618, 401), dentro del núcleo del moño.

2. ``body_and_edges_complete`` (N04). §5.2 pide evidencia objetiva primero. La evidencia usa lo
   que las DOS llaves ya acordaron en este mismo paquete:
   - ``acordado_D`` = unión de los agujeros cerrados ≥ 1000 px que las dos llaves marcaron ``D``
     («falta material de la chica») en las otras cinco láminas;
   - ``perdida`` = píxeles de ``acordado_D`` que N04 deja fuera de su máscara;
   - se reporta también qué parte de esa pérdida está abierta al exterior (no es agujero cerrado).
   Decisión: ``perdida`` ≥ 1000 px → FALSE (N04 deja fuera ≥ 1000 px que las dos llaves
   reconocen como material de la chica). ``perdida`` < 1000 px → la medición no decide y el caso va
   a la tercera revisión ciega (Codex), sin cambiar nada más.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pragma_ae import aem1_v13 as v13  # noqa: E402
from pragma_ae import aem1_v13_audit as a13  # noqa: E402
from pragma_ae import aem1_v14 as w  # noqa: E402
from pragma_ae import aem1_v14_audit as audit  # noqa: E402
from pragma_ae.imageio import load_rgb, locate_image  # noqa: E402
from pragma_ae.masks import components  # noqa: E402

RUN = ROOT / "auditoria" / "aem1v14_20260926T063238Z_67d41850"
MAPPING_SHA256 = "1a68b79e3df2ab7e4fe8f75daef16ebe3c933d4bdcf4eb8fb582e3e47c3f1a66"
PACKAGE_SHA256 = "8f8df2730f64f5f94deb72c8f7af8b3653bc95bf0f5a3bb81e065b331ee4a17b"
COMMITTED_CLAUDE_SHA256 = "6febe5d6e37198af8fc4ceceb2e98ce1e5794fb1bd52a68e5ce9ad54f30c78d0"
B_LOSS_MIN_PX = 1000
O_LABELS = ("N01", "N05")
B_LABEL = "N04"


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def open_part(lost: np.ndarray, mask: np.ndarray) -> int:
    """Píxeles perdidos que NO están dentro de un agujero cerrado de la máscara (faltante abierto)."""
    enclosed = np.zeros_like(lost)
    for hole in a13.holes_with_masks(mask, 1):
        enclosed |= hole["mask"]
    return int((lost & ~enclosed).sum())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    args = parser.parse_args(argv)
    if sha(args.mapping) != MAPPING_SHA256:
        raise SystemExit("mapeo sellado distinto del registrado")
    first_path, second_path = RUN / "juicios_claude_crudos_v14.json", RUN / "segunda_llave_chatgpt_v14.json"
    if sha(first_path) != COMMITTED_CLAUDE_SHA256:
        raise SystemExit("los juicios de Claude no coinciden con el compromiso")
    first = json.loads(first_path.read_text(encoding="utf-8"))["candidates"]
    second_doc = json.loads(second_path.read_text(encoding="utf-8"))
    if second_doc["package_sha256"] != PACKAGE_SHA256:
        raise SystemExit("la segunda llave no juzgó el paquete registrado")
    second = second_doc["candidates"]

    mapping = json.loads(args.mapping.read_text(encoding="utf-8"))
    labels = sorted(mapping["mapping"])
    blobs = a13._read(args.zip)
    loaded = audit.load_masks(blobs, [mapping["mapping"][lab]["candidate_id"] for lab in labels])
    masks = {lab: loaded[mapping["mapping"][lab]["candidate_id"]] for lab in labels}   # solo por etiqueta
    del loaded
    dark = v13.dark_map(v13.gray_of(load_rgb(locate_image())))

    # 1. O por la regla prerregistrada.
    o_result = {}
    for lab in O_LABELS:
        m = w.measure_o(masks[lab], dark)
        x1, y1, x2, y2 = w.BUN_CORE
        bun = masks[lab][y1:y2, x1:x2] & dark[y1:y2, x1:x2]
        islands = [{"area_px": c["area"], "bbox": [c["bbox"][0] + x1, c["bbox"][1] + y1, c["bbox"][2] + x1, c["bbox"][3] + y1]}
                   for c in components(bun)] if bun.any() else []
        o_result[lab] = {"value": m["o_by_measurement"], "kind": "medicion_prerregistrada",
                         "keys": {"claude": first[lab]["criteria"]["other_person_excluded"],
                                  "chatgpt": second[lab]["criteria"]["other_person_excluded"]},
                         "evidence": {**m, "bun_core_islands": islands}}

    # 2. B de N04 con el material que las dos llaves acordaron como D en las otras láminas.
    agreed = np.zeros_like(masks[B_LABEL])
    sources = []
    for lab in labels:
        if lab == B_LABEL:
            continue
        for hole in a13.holes_with_masks(masks[lab]):
            n = str(hole["number"])
            if first[lab]["holes"].get(n) == "D" and second[lab]["holes"].get(n) == "D":
                agreed |= hole["mask"]
                sources.append({"label": lab, "hole": hole["number"], "area_px": hole["area"], "bbox": list(hole["bbox"])})
    lost = agreed & ~masks[B_LABEL]
    loss = int(lost.sum())
    ys, xs = np.nonzero(lost)
    b_value = "FALSE" if loss >= B_LOSS_MIN_PX else "THIRD_REVIEW_REQUIRED"
    b_result = {"value": b_value, "kind": "medicion_consenso_D" if b_value == "FALSE" else "tercera_revision",
                "keys": {"claude": first[B_LABEL]["criteria"]["body_and_edges_complete"],
                         "chatgpt": second[B_LABEL]["criteria"]["body_and_edges_complete"]},
                "evidence": {"agreed_D_px": int(agreed.sum()), "agreed_D_sources": sources,
                             "lost_px": loss, "lost_open_px": open_part(lost, masks[B_LABEL]),
                             "lost_bbox": [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1] if loss else None,
                             "threshold_px": B_LOSS_MIN_PX}}

    out = {"schema": "pragma.aem1v14_blind_adjudication", "schema_version": "0.1.0",
           "blind": "sí: por etiqueta; el mapeo solo se usó para leer máscaras y no se imprime ni se escribe",
           "rules": __doc__.split("Reglas,", 1)[1].strip(),
           "script_sha256": sha(Path(__file__)), "mapping_sha256": MAPPING_SHA256, "package_sha256": PACKAGE_SHA256,
           "other_person_excluded": o_result, "body_and_edges_complete": {B_LABEL: b_result}}
    (RUN / "adjudicacion_tecnica_ciega_v14.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n",
                                                            encoding="utf-8")
    for lab, r in o_result.items():
        print(f"{lab} · O = {r['value']} · núcleo del moño {r['evidence']['bun_core_px']} px, "
              f"islas hombro {r['evidence']['shoulder_separate_px']} px")
    print(f"{B_LABEL} · B = {b_value} · material D acordado {int(agreed.sum())} px · perdido {loss} px "
          f"(abierto {b_result['evidence']['lost_open_px']} px)")


if __name__ == "__main__":
    main()
