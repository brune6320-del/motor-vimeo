"""Compone las máscaras de referencia A‑E0 de las tres personas a partir de las dos llaves de polígonos.

    python3 work/ae0_compose_masks.py <adjudicaciones.json> [--write]

Pasos (DEC‑025; ``ae0/FORMATO_POLIGONOS_A-E0.md`` §3):
1. Rasteriza las dos llaves (``local/``, nunca en git) y verifica sus SHA‑256 contra el compromiso y la
   recepción.
2. Por persona, ``keydiff.compare_keys(A, B)`` y ``compose_reference`` con las adjudicaciones y la
   política ``MIDLINE``.
3. La zona incierta final añade la unión de los ``uncertain_rings`` de las dos llaves.
4. **Exclusividad entre personas** (propuesta de la carta 016): un píxel que queda en la estimación de
   dos personas pasa a ``uncertain`` en las dos y sale de la estimación de ambas.
5. Imprime un resumen público (áreas, fracciones, cotas de cada llave). Con ``--write`` guarda las
   máscaras en ``ae0/gt/`` (no versionado) y sus hashes.
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

from pragma_ae import EXPECTED_IMAGE_SIZE, keydiff  # noqa: E402
from pragma_ae.polygon import rasterize_person  # noqa: E402

KEY_A = ROOT / "local/ae0/poligonos_claude_A-E0.json"
KEY_B = ROOT / "local/ae0/llaves_poligonos/poligonos_chatgpt_A-E0.json"
COMMIT_A = ROOT / "ae0/COMPROMISO_POLIGONOS_CLAUDE_A-E0.json"
RECEIPT_B = ROOT / "ae0/RECEPCION_POLIGONOS_CHATGPT_A-E0.json"
PERSONS = ("ae0_001", "ae0_002", "ae0_003")
SHAPE = (EXPECTED_IMAGE_SIZE[1], EXPECTED_IMAGE_SIZE[0])


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exclusive_persons(refs: dict) -> dict:
    """Quita de la estimación de todas las personas los píxeles que reclaman dos o más, y los marca inciertos."""
    ids = list(refs)
    claimed = np.zeros(SHAPE if not ids else refs[ids[0]]["estimate"].shape, np.uint8)
    for oid in ids:
        claimed += refs[oid]["estimate"].astype(np.uint8)
    shared = claimed > 1
    out = {}
    for oid in ids:
        overlap = refs[oid]["estimate"] & shared
        out[oid] = {"estimate": refs[oid]["estimate"] & ~shared, "uncertain": refs[oid]["uncertain"] | overlap,
                    "shared_px": int(overlap.sum())}
    return out


def compose(adjudications: dict, key_a: Path = KEY_A, key_b: Path = KEY_B, check_custody: bool = True) -> dict:
    if check_custody:
        want_a = json.loads(COMMIT_A.read_text(encoding="utf-8"))["file_sha256"]
        want_b = json.loads(RECEIPT_B.read_text(encoding="utf-8"))["file_sha256"]
        if sha(key_a) != want_a or sha(key_b) != want_b:
            raise SystemExit("Custodia: el hash de alguna llave no coincide con su registro")
    A = json.loads(key_a.read_text(encoding="utf-8"))["persons"]
    B = json.loads(key_b.read_text(encoding="utf-8"))["persons"]
    refs, report = {}, {}
    for oid in PERSONS:
        ra, rb = rasterize_person(A[oid], SHAPE), rasterize_person(B[oid], SHAPE)
        diff = keydiff.compare_keys(ra["mask"], rb["mask"])
        verdicts = {cid: v[0] if isinstance(v, list) else v for cid, v in adjudications[oid].items()}
        ref = keydiff.compose_reference(diff, verdicts, "MIDLINE")
        rings = ra["uncertain"] | rb["uncertain"]
        refs[oid] = {"estimate": ref["reference_estimate_mask"], "uncertain": ref["uncertain_mask"] | rings,
                     "a": ra["mask"], "b": rb["mask"]}
        report[oid] = {"keydiff": diff["summary"], "rings_union_px": int(rings.sum())}
    final = exclusive_persons({k: {"estimate": v["estimate"], "uncertain": v["uncertain"]} for k, v in refs.items()})
    for oid in PERSONS:
        est, unc = final[oid]["estimate"], final[oid]["uncertain"]
        report[oid].update({
            "estimate_px": int(est.sum()), "certain_foreground_px": int((est & ~unc).sum()),
            "uncertain_area_px": int(unc.sum()), "uncertain_fraction_of_image": round(float(unc.sum()) / unc.size, 6),
            "uncertain_fraction_of_estimate": round(float((unc & est).sum()) / max(1, int(est.sum())), 4),
            "shared_between_persons_px": final[oid]["shared_px"],
            "key_A_vs_reference": keydiff.iou_with_uncertainty(refs[oid]["a"], est, unc),
            "key_B_vs_reference": keydiff.iou_with_uncertainty(refs[oid]["b"], est, unc),
        })
        refs[oid].update(final[oid])
    return {"report": report, "refs": refs}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("adjudications", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    adj = json.loads(args.adjudications.read_text(encoding="utf-8"))["adjudications"]
    out = compose(adj)
    report = out["report"]
    if args.write:
        from PIL import Image
        gt = ROOT / "ae0/gt"
        gt.mkdir(parents=True, exist_ok=True)
        for oid in PERSONS:
            for name, m in (("estimate", out["refs"][oid]["estimate"]), ("uncertain", out["refs"][oid]["uncertain"])):
                path = gt / f"{oid}_{name}.png"
                Image.fromarray(m.astype(np.uint8) * 255).save(path)
                report[oid][f"{name}_png_sha256"] = sha(path)
    print(json.dumps({"adjudications_file": args.adjudications.as_posix(), "adjudications_sha256": sha(args.adjudications),
                      "estimate_policy": "MIDLINE", "cross_person_rule": "EXCLUSIVITY", "persons": report},
                     indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
