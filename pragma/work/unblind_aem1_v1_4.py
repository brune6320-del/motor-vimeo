"""Desciegue y análisis de la corrida A-E(−1) v1.4 `20260926T063238Z_67d41850` (protocolo v2 rev. 1, paso 7).

    python3 work/unblind_aem1_v1_4.py --zip <ZIP> --mapping <sealed_mapping.json local>

Necesita la foto (núcleos oscuros del moño). Antes de analizar comprueba los hashes del código
congelado en el prerregistro, del mapeo sellado, del compromiso de Claude, del eco del paquete y de la
adjudicación técnica ciega ya versionada. Escribe en ``auditoria/aem1v14_20260926T063238Z_67d41850/``:

- ``mapeo_desciegado.json``: el mapeo sellado;
- ``doble_llave_v14.json``: comparación de llaves, adjudicación y retest;
- ``aem1v14_analisis.json``: el análisis prerregistrado (``aem1_v14_audit.analyze``).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pragma_ae import aem1_v13 as v13  # noqa: E402
from pragma_ae import aem1_v14_audit as audit  # noqa: E402
from pragma_ae.imageio import load_rgb, locate_image  # noqa: E402

RUN = ROOT / "auditoria" / "aem1v14_20260926T063238Z_67d41850"
PREREG = ROOT / "aem1" / "PRERREGISTRO_A-E-menos-1_v1_4.json"
MAPPING_SHA256 = "1a68b79e3df2ab7e4fe8f75daef16ebe3c933d4bdcf4eb8fb582e3e47c3f1a66"
PACKAGE_SHA256 = "8f8df2730f64f5f94deb72c8f7af8b3653bc95bf0f5a3bb81e065b331ee4a17b"
COMMITTED_CLAUDE_SHA256 = "6febe5d6e37198af8fc4ceceb2e98ce1e5794fb1bd52a68e5ce9ad54f30c78d0"
ADJUDICATION = RUN / "adjudicacion_tecnica_ciega_v14.json"


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    args = parser.parse_args(argv)

    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    for path, digest in prereg["analysis_implementation_sha256"].items():
        if sha(ROOT / path) != digest:
            raise SystemExit(f"{path} cambió después del prerregistro: el análisis no sería el congelado")
    if sha(args.mapping) != MAPPING_SHA256:
        raise SystemExit("mapeo sellado distinto del registrado")
    first_path, second_path = RUN / "juicios_claude_crudos_v14.json", RUN / "segunda_llave_chatgpt_v14.json"
    if sha(first_path) != COMMITTED_CLAUDE_SHA256:
        raise SystemExit("los juicios de Claude no coinciden con el compromiso")
    first = json.loads(first_path.read_text(encoding="utf-8"))
    second = json.loads(second_path.read_text(encoding="utf-8"))
    if second["package_sha256"] != PACKAGE_SHA256:
        raise SystemExit("la segunda llave no juzgó el paquete registrado")
    blind = json.loads(ADJUDICATION.read_text(encoding="utf-8"))
    mapping = json.loads(args.mapping.read_text(encoding="utf-8"))
    cid = {label: row["candidate_id"] for label, row in mapping["mapping"].items()}

    # Adjudicación ciega, ya versionada, traducida a candidatas.
    adjudications = {}
    for label, row in blind["other_person_excluded"].items():
        adjudications[(cid[label], "other_person_excluded")] = {"value": row["value"], "kind": row["kind"],
                                                                "blind_label": label}
    for label, row in blind["body_and_edges_complete"].items():
        if row["value"] not in ("TRUE", "FALSE"):
            raise SystemExit(f"{label}: la adjudicación ciega no decidió; falta la tercera revisión")
        adjudications[(cid[label], "body_and_edges_complete")] = {"value": row["value"], "kind": row["kind"],
                                                                  "blind_label": label}

    dark = v13.dark_map(v13.gray_of(load_rgb(locate_image())))
    analysis = audit.analyze(args.zip, prereg, mapping, first, second, dark, adjudications)

    cells, agree, totals, disagreements = {}, {"criteria": 0, "aux": 0, "holes": 0}, {"criteria": 0, "aux": 0, "holes": 0}, []
    for label in sorted(first["candidates"]):
        a, b = first["candidates"][label], second["candidates"][label]
        row = {}
        for group in ("criteria", "aux"):
            for field, value in a[group].items():
                totals[group] += 1
                same = b[group][field] == value
                agree[group] += same
                row[field] = {"claude": value, "chatgpt": b[group][field], "agree": same}
                if not same:
                    disagreements.append({"label": label, "candidate_id": cid[label], "field": field,
                                          "claude": value, "chatgpt": b[group][field]})
        for number, value in a["holes"].items():
            totals["holes"] += 1
            agree["holes"] += b["holes"].get(number) == value
        cells[label] = row

    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / "mapeo_desciegado.json").write_bytes(args.mapping.read_bytes())
    double_key = {
        "schema": "pragma.aem1v14_double_key", "schema_version": "0.1.0",
        "first_key": {"file": first_path.name, "sha256": sha(first_path), "committed_in": "0a0e19c"},
        "second_key": {"file": second_path.name, "sha256": sha(second_path), "package_sha256_echoed": second["package_sha256"]},
        "blindness": ("TEMPORAL_DOBLE: ChatGPT recibió solo el paquete y su LEEME; Claude comprometió sus juicios por hash antes; "
                      "la adjudicación técnica se hizo y versionó por etiqueta ANTES del desciegue (751cbaa reglas, aa164e3 resultado)"),
        "agreement": {k: f"{agree[k]}/{totals[k]}" for k in agree},
        "cells": cells, "disagreements": disagreements,
        "technical_adjudication": {"file": ADJUDICATION.name, "sha256": sha(ADJUDICATION),
                                   "decisions": {f"{lab}.{field}": row["value"]
                                                 for field in ("other_person_excluded", "body_and_edges_complete")
                                                 for lab, row in blind[field].items()}},
        "mapping": {label: cid[label] for label in sorted(cid)},
    }
    (RUN / "doble_llave_v14.json").write_text(json.dumps(double_key, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    public = {
        "schema": "pragma.aem1v14_analysis_public", "schema_version": "0.1.0",
        "prereg_content_sha256": prereg["content_sha256"], "analysis_code_frozen": prereg["analysis_implementation_sha256"],
        **{k: analysis[k] for k in ("case_status", "aem1_closure", "passing", "best_attempt", "pending_adjudication",
                                    "adjudications", "reproduction", "consensus", "holes_consensus", "keys_reconciled",
                                    "per_seed", "hypotheses", "perturbation", "descriptive_preregistered", "sentinels",
                                    "sam2_rejectable", "project_status")},
    }
    public["adjudications"] = {k: {kk: vv for kk, vv in val.items() if kk != "evidence"} for k, val in public["adjudications"].items()}
    (RUN / "aem1v14_analisis.json").write_text(json.dumps(public, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("caso:", analysis["case_status"], "·", analysis["aem1_closure"], "· PASS:", analysis["passing"])
    print("mejor intento:", analysis["best_attempt"], "· reproducción:", analysis["reproduction"]["label"])
    print("hipótesis:", analysis["hypotheses"], "· pendientes:", analysis["pending_adjudication"])
    print("acuerdo:", double_key["agreement"])


if __name__ == "__main__":
    main()
