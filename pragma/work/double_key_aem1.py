"""Doble llave de la corrida A-E(−1) 20260925T062504Z_256dba9f: Claude (1ª) frente a ChatGPT (2ª).

Uso:
    python3 work/double_key_aem1.py                 # comparación de juicios (solo archivos del repo)
    python3 work/double_key_aem1.py --zip <ZIP>     # + las dos mediciones de adjudicación (máscaras reales)

Escribe ``auditoria/aem1_20260925T062504Z_256dba9f/doble_llave.json``. Los juicios crudos de ambas
llaves no se modifican: la adjudicación posterior al desciegue queda aparte y etiquetada como tal.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import sys
import zipfile
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pragma_ae.masks import enclosed_holes  # noqa: E402

RUN = ROOT / "auditoria" / "aem1_20260925T062504Z_256dba9f"
CRITERIA = ("correct_subject", "body_and_edges_complete", "other_person_excluded", "background_excluded")
SHORT = {"correct_subject": "S", "body_and_edges_complete": "B", "other_person_excluded": "O", "background_excluded": "G"}
HOLE_DEFECT_PX = 1000  # «yema de dedo» del protocolo v1 §4


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    path = RUN / name
    return path, json.loads(path.read_text(encoding="utf-8"))


def fails(criteria: dict) -> list:
    return [SHORT[c] for c in CRITERIA if criteria[c] != "TRUE"]


def cohen_kappa(a: list, b: list):
    """κ de Cohen para dos listas de etiquetas; None si no hay varianza (acuerdo esperado = 1)."""
    n = len(a)
    labels = sorted(set(a) | set(b))
    observed = sum(x == y for x, y in zip(a, b)) / n
    expected = sum((a.count(k) / n) * (b.count(k) / n) for k in labels)
    if math.isclose(expected, 1.0):
        return None
    return round((observed - expected) / (1 - expected), 3)


def compare(first: dict, second: dict) -> dict:
    labels = sorted(first["candidates"])
    cells, disagreements = {}, []
    for label in labels:
        row = {}
        for c in CRITERIA:
            a = first["candidates"][label]["criteria"][c]
            b = second["candidates"][label]["criteria"][c]
            row[SHORT[c]] = {"claude": a, "chatgpt": b, "agree": a == b}
            if a != b:
                disagreements.append({"label": label, "criterion": c, "claude": a, "chatgpt": b})
        cells[label] = row
    per_criterion = {}
    for c in CRITERIA:
        a = [first["candidates"][k]["criteria"][c] for k in labels]
        b = [second["candidates"][k]["criteria"][c] for k in labels]
        per_criterion[SHORT[c]] = {
            "agree": sum(x == y for x, y in zip(a, b)), "total": len(labels), "kappa": cohen_kappa(a, b),
        }
    total_agree = sum(v["agree"] for v in per_criterion.values())
    passes_first = {k: not fails(first["candidates"][k]["criteria"]) for k in labels}
    passes_second = {k: not fails(second["candidates"][k]["criteria"]) for k in labels}
    fail_sets = {k: {"claude": fails(first["candidates"][k]["criteria"]),
                     "chatgpt": fails(second["candidates"][k]["criteria"])} for k in labels}
    for d in disagreements:
        # Relevante solo si adoptar el valor de la otra llave en esa celda hiciera pasar a la candidata.
        relevant = False
        for own, other in ((first, second), (second, first)):
            criteria = dict(own["candidates"][d["label"]]["criteria"])
            criteria[d["criterion"]] = other["candidates"][d["label"]]["criteria"][d["criterion"]]
            relevant = relevant or not fails(criteria)
        d["verdict_relevant"] = relevant
    return {
        "cells": cells,
        "agreement": {"per_criterion": per_criterion, "cells_agree": total_agree, "cells_total": 4 * len(labels)},
        "fail_sets": fail_sets,
        "passing": {"claude": [k for k, v in passes_first.items() if v], "chatgpt": [k for k, v in passes_second.items() if v]},
        "verdict_agree": passes_first == passes_second,
        "disagreements": disagreements,
    }


def best_attempt(judgments: dict) -> dict:
    """Regla 3 del protocolo v1 §6: menos criterios FALSE (UNSURE cuenta como FALSE); empate → alfabética."""
    counts = {k: len(fails(v["criteria"])) for k, v in judgments["candidates"].items()}
    best = min(counts.values())
    tied = sorted(k for k, v in counts.items() if v == best)
    return {"label": tied[0], "false_count": best, "tied": tied}


def partition_odds(group_sizes: list) -> int:
    """Número de formas de repartir las etiquetas en grupos de esos tamaños (multinomial)."""
    total = math.factorial(sum(group_sizes))
    for size in group_sizes:
        total //= math.factorial(size)
    return total


def measure(zip_path: Path, mapping: dict) -> dict:
    """Las dos mediciones que deciden discrepancias medibles (posteriores al desciegue)."""
    import numpy as np
    from PIL import Image

    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()

        def mask_of(label):
            key, index = mapping[label]
            stem = key.replace("+", "_").replace(":", "_")
            pattern = re.compile(rf"^aem1_{re.escape(stem)}_[0-9a-f]{{8}}_c{index}_alpha\.png$")
            hits = [n for n in names if pattern.match(n)]
            if len(hits) != 1:
                raise SystemExit(f"No encuentro la máscara de {label} ({key}#{index}) en el ZIP")
            with Image.open(io.BytesIO(z.read(hits[0]))) as handle:
                return np.asarray(handle.convert("L")) > 127

        a, f, g = mask_of("A"), mask_of("F"), mask_of("G")
    g_area = int(g.sum())
    holes_f = enclosed_holes(f, HOLE_DEFECT_PX)
    return {
        "zip_sha256": sha(zip_path),
        "G_area_share": {
            "question": "¿La componente principal de G es la chica? (protocolo v1 §4, correct_subject)",
            "proxy": "A = box+corrections:s1#0, juzgada por ambas llaves sin persona posterior ni fondo: A ⊂ chica (salvo bordes ≤ 5 px)",
            "G_area_px": g_area,
            "G_inside_A_px": int((g & a).sum()),
            "share_inside_A": round(float((g & a).sum()) / g_area, 3),
            "G_inside_F_px": int((g & f).sum()),
            "share_inside_F": round(float((g & f).sum()) / g_area, 3),
            "reading": "cota inferior de la fracción de G sobre la chica = fracción dentro de A",
        },
        "F_enclosed_holes": {
            "question": "¿F tiene agujeros ≥ 1000 px? (protocolo v1 §4, body_and_edges_complete)",
            "min_area_px": HOLE_DEFECT_PX,
            "holes": [{"area_px": h["area"], "bbox_xyxy": list(h["bbox"])} for h in holes_f],
        },
    }


# Adjudicación de Claude tras desciegar, escrita con las razones. No reemplaza ningún juicio crudo.
ADJUDICATION = {
    ("C", "correct_subject"): ("TRUE", "definicion", "El texto congelado solo excluye a la persona posterior, al señor y el fondo; "
                               "una prenda de la chica no es nada de eso. Mi FALSE añadió una condición no escrita "
                               "(«la persona entera»). Tiene razón ChatGPT."),
    ("E", "correct_subject"): ("TRUE", "definicion", "Igual que C."),
    ("H", "correct_subject"): ("TRUE", "definicion", "Igual que C."),
    ("J", "correct_subject"): ("TRUE", "definicion", "Igual que C."),
    ("G", "correct_subject"): ("TRUE", "medicion", "Al menos el 61,9 % del área de G cae dentro de A, que ambas llaves juzgaron "
                               "sin persona posterior ni fondo: la componente principal es la chica. La fusión ya la "
                               "castiga other_person_excluded. Tiene razón ChatGPT."),
    ("F", "body_and_edges_complete"): ("FALSE", "medicion", "F tiene 2 agujeros cerrados ≥ 1000 px (2540 y 1885 px). Inspeccionados en "
                                       "local, los dos están sobre material continuo con el cuerpo incluido: el pelo de la "
                                       "chica entre la cara y el dedo índice, y el tirante blanco del overol. Son defectos, "
                                       "no huecos de fondo. Mi UNSURE pasa a FALSE y el TRUE de ChatGPT queda refutado."),
}
# Coincidencia de ambas llaves que el mismo texto no sostiene: el botón es de la chica.
SHARED_DEFINITION_GAP = {
    "labels": ["B", "D"],
    "criterion": "correct_subject",
    "both_keys": "FALSE",
    "literal_reading": "TRUE",
    "note": ("Con el texto literal, un botón del overol también es «de la chica». Las dos llaves aplicamos un umbral de "
             "extensión no escrito, con cortes distintos: yo en «persona entera» y ChatGPT entre «prenda» y «fragmento». "
             "El protocolo v2 separa la identidad (¿de quién es la mayoría del área?) de la extensión (body_and_edges_complete)."),
}


def adjudicate(first: dict, second: dict, measurements) -> dict:
    labels = sorted(first["candidates"])
    table, resolutions = {}, []
    for label in labels:
        row = {}
        for c in CRITERIA:
            a = first["candidates"][label]["criteria"][c]
            b = second["candidates"][label]["criteria"][c]
            if a == b:
                row[c] = a
                continue
            value, kind, reason = ADJUDICATION[(label, c)]
            if kind == "medicion" and measurements is None:
                value, reason = "PENDIENTE_MEDICION", "Requiere --zip con las máscaras reales."
            row[c] = value
            resolutions.append({"label": label, "criterion": c, "claude": a, "chatgpt": b,
                                "adjudicated": value, "kind": kind, "reason": reason})
        table[label] = {"criteria": row, "passes": all(v == "TRUE" for v in row.values())}
    if measurements is not None:
        share = measurements["G_area_share"]["share_inside_A"]
        holes = measurements["F_enclosed_holes"]["holes"]
        if not share > 0.5 or not holes:
            raise SystemExit("Las mediciones ya no sostienen la adjudicación escrita: revisar ADJUDICATION")
    concessions = sum(1 for r in resolutions if r["adjudicated"] == r["chatgpt"])
    return {
        "note": "Posterior al desciegue. No reemplaza los juicios crudos de ninguna llave.",
        "resolutions": resolutions,
        "concessions_to_chatgpt": concessions,
        "concessions_to_claude": sum(1 for r in resolutions if r["adjudicated"] == r["claude"]),
        "refuted_by_measurement": [
            {"cell": f"{r['label']}.{SHORT[r['criterion']]}",
             "refuted": [who for who in ("claude", "chatgpt") if r[who] not in (r["adjudicated"], "UNSURE")],
             "unsure_resolved": [who for who in ("claude", "chatgpt") if r[who] == "UNSURE"]}
            for r in resolutions if r["kind"] == "medicion"],
        "shared_definition_gap": SHARED_DEFINITION_GAP,
        "table": table,
        "passing": [k for k, v in table.items() if v["passes"]],
    }


def v13_id(key: str, index: int) -> str:
    """Nombre v1.3 de una candidata de la corrida 1: point#0 → BASE|point|0; box+corrections:s1#0 → BASE|box+corrections|s1."""
    if ":" in key:
        protocol, seed = key.split(":")
        return f"BASE|{protocol}|{seed}"
    return f"BASE|{key}|{index}"


def base_v2_reference(record: dict, table: dict, zip_path: Path) -> dict:
    """BASE_V2_REFERENCE (ChatGPT 003, objeción e): la corrida 1 normalizada a las definiciones del protocolo v2.

    No es una doble llave v2 heredada: es la adjudicación ya archivada más una sola normalización.
    En v2, ``correct_subject`` es la identidad por mayoría del área. Donde las dos llaves dijeron
    FALSE por extensión (B y D, un botón), se mide la fracción del área que cae dentro de A y se
    aplica la definición v2.
    """
    import numpy as np
    from PIL import Image

    adjudicated = record["adjudication_post_unblinding"]["table"]
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()

        def mask_of(key, index):
            stem = key.replace("+", "_").replace(":", "_")
            pattern = re.compile(rf"^aem1_{re.escape(stem)}_[0-9a-f]{{8}}_c{index}_alpha\.png$")
            (hit,) = [n for n in names if pattern.match(n)]
            with Image.open(io.BytesIO(z.read(hit))) as handle:
                return np.asarray(handle.convert("L")) > 127

        rows = {r["label"]: r for r in table["candidates"]}
        girl_proxy = mask_of(rows["A"]["key"], rows["A"]["candidate_index"])
        candidates, normalizations = {}, []
        for label in sorted(rows):
            row = rows[label]
            criteria = dict(adjudicated[label]["criteria"])
            if criteria["correct_subject"] != "TRUE":
                mask = mask_of(row["key"], row["candidate_index"])
                share = float((mask & girl_proxy).sum()) / max(int(mask.sum()), 1)
                v2 = "TRUE" if share > 0.5 else "FALSE"
                normalizations.append({"label": label, "criterion": "correct_subject", "v1_adjudicated": criteria["correct_subject"],
                                       "v2": v2, "share_inside_A": round(share, 4),
                                       "rule": "v2 §4: más de la mitad del área sobre la chica (A = cota inferior, juzgada sin persona posterior ni fondo)"})
                criteria["correct_subject"] = v2
            candidates[v13_id(row["key"], row["candidate_index"])] = {
                "run1_label": label, "packed_mask_sha256": row["packed_mask_sha256"], "criteria": criteria,
                "target_hair_included": "NO_JUZGADO_V1", "target_dark_sleeves_included": "NO_JUZGADO_V1",
                "passes": all(v == "TRUE" for v in criteria.values()),
            }
    out = {
        "schema": "pragma.aem1_base_v2_reference",
        "schema_version": "0.1.0",
        "kind": "REFERENCIA_NORMALIZADA_ADJUDICADA",
        "not": "no es una doble llave v2 heredada: los juicios se emitieron con el protocolo v1",
        "origin": "ChatGPT 003, objeción (e): BIT_EXACT_MASK ≠ BIT_EXACT_JUDGMENT_UNDER_NEW_PROTOCOL",
        "run_id": record["run_id"], "zip_sha256": record["zip_sha256"],
        "sources": {"doble_llave.json": sha(RUN / "doble_llave.json"), "aem1_tabla_desciegada.json": sha(RUN / "aem1_tabla_desciegada.json")},
        "use": ("si BASE v1.3 reproduce bit a bit una candidata de la corrida 1, esta tabla es su referencia para la "
                "comparación causal (+POS frente a BASE emparejada); lo que no se reproduzca vuelve al paquete ciego"),
        "normalizations": normalizations,
        "candidates": dict(sorted(candidates.items())),
        "passing": sorted(k for k, v in candidates.items() if v["passes"]),
    }
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--zip", type=Path, help="ZIP real de la corrida (para las mediciones)")
    parser.add_argument("--out", type=Path, default=RUN / "doble_llave.json")
    parser.add_argument("--base-reference", type=Path,
                        help="además escribe BASE_V2_REFERENCE.json (requiere --zip)")
    args = parser.parse_args(argv)

    first_path, first = load("juicios_crudos.json")
    second_path, second = load("segunda_llave_chatgpt.json")
    table_path, table = load("aem1_tabla_desciegada.json")
    verdict_path, verdict = load("aem1_audit_verdict.json")
    if first["protocol_sha256"] != second["protocol_sha256"]:
        raise SystemExit("Las dos llaves no citan el mismo protocolo")
    mapping = {row["label"]: (row["key"], row["candidate_index"]) for row in table["candidates"]}

    result = compare(first, second)
    # Estructura que ambas llaves describen con las mismas etiquetas (ver notas de cada llave):
    groups = {
        "fragmento_diminuto": ["B", "D"],
        "solo_prenda": ["C", "E", "H", "J"],
        "incluye_persona_posterior": sorted(k for k, v in result["fail_sets"].items()
                                            if "O" in v["claude"] and "O" in v["chatgpt"]),
        "resto": ["A", "L"],
    }
    sizes = [len(v) for v in groups.values()]
    out = {
        "schema": "pragma.aem1_double_key",
        "schema_version": "0.1.0",
        "run_id": verdict["run_id"],
        "zip_sha256": verdict["zip_sha256"],
        "protocol_sha256": first["protocol_sha256"],
        "first_key": {"by": "Claude Code", "file": first_path.relative_to(ROOT).as_posix(), "sha256": sha(first_path),
                      "blindness": "AUTO_CEGADO (mismo agente que escribió el código)"},
        "second_key": {"by": "ChatGPT", "file": second_path.relative_to(ROOT).as_posix(), "sha256": sha(second_path),
                       "source": second["source"], "source_sha256": second["source_sha256"],
                       "blindness": second["blindness"], "package_sha256": second["material_package_sha256_expected"],
                       "package_sha256_echoed": second["material_package_sha256_echoed_by_auditor"]},
        "unblinded_table_sha256": sha(table_path),
        "first_key_verdict_sha256": sha(verdict_path),
        **result,
        "best_attempt": {"claude": best_attempt(first), "chatgpt": best_attempt(second)},
        "shared_structure": {
            "groups": groups,
            "note": ("La carta 002 reveló CUÁNTAS candidatas había de cada tipo, no CUÁLES. Reproducir esta "
                     "partición por azar conociendo solo los recuentos tiene probabilidad 1/N."),
            "N": partition_odds(sizes),
        },
    }
    measurements = measure(args.zip, mapping) if args.zip else None
    if measurements is not None:
        out["measurements_post_unblinding"] = measurements
    out["adjudication_post_unblinding"] = adjudicate(first, second, measurements)
    out["status"] = {
        "double_key": "CONCORDANTE_EN_VEREDICTO" if result["verdict_agree"] else "DISCREPANTE",
        "case_status": verdict["case_status"],
        "case_status_level": ("ACEPTADO (doble llave; segunda llave parcialmente contaminada)"
                              if result["verdict_agree"] and not result["passing"]["claude"] else "PENDIENTE"),
        "selected_best_attempt": verdict["selected"],
        "project_status": verdict["project_status"],
        "phase_b_blocked": verdict["phase_b_blocked"],
        "sam2_rejectable": verdict["sam2_rejectable"],
        "limitations": [
            "La primera llave es un auto-cegado del agente que escribió el código.",
            "La segunda llave conocía, por la carta 002, el resultado agregado y los patrones por familia.",
            "La segunda llave no devolvió el SHA-256 del paquete que juzgó; la identidad se sostiene por la cadena de custodia.",
            "Las láminas de la segunda llave eran JPEG de las mismas láminas PNG de la primera.",
        ],
        "user_veto": "la persona usuaria puede vetar este veredicto en cualquier momento",
    }
    args.out.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.base_reference:
        if not args.zip:
            raise SystemExit("--base-reference requiere --zip")
        reference = base_v2_reference(out, table, args.zip)
        args.base_reference.write_text(json.dumps(reference, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("BASE_V2_REFERENCE:", reference["normalizations"], "· pasan:", reference["passing"])
    agreement = result["agreement"]
    print(f"celdas en acuerdo: {agreement['cells_agree']}/{agreement['cells_total']}")
    for k, v in agreement["per_criterion"].items():
        print(f"  {k}: {v['agree']}/{v['total']}  κ={v['kappa']}")
    print("veredicto concordante:", result["verdict_agree"], "· pasan:", result["passing"])
    print("discrepancias:", [(d["label"], SHORT[d["criterion"]], d["claude"], d["chatgpt"]) for d in result["disagreements"]])
    print("partición compartida: 1 /", out["shared_structure"]["N"])
    if args.zip:
        m = out["measurements_post_unblinding"]
        print("G dentro de A:", m["G_area_share"]["share_inside_A"], "· agujeros ≥1000 px en F:", m["F_enclosed_holes"]["holes"])
    print("escrito:", args.out)


if __name__ == "__main__":
    main()
