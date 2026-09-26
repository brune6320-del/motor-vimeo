"""Validación retrospectiva de ``pragma_ae.keydiff`` con las máscaras reales de v1.4 (EXPLORATORIO).

    python3 work/keydiff_retro_aem1_v1_4.py --zip <ZIP local v1.4> --mapping <sealed_mapping.json local>

Se hace **después** del desciegue y del cierre por doble llave: no cambia ningún veredicto. Pregunta
qué habría señalado la comprobación geométrica (DEC‑025) si dos de estas máscaras fueran dos llaves:

- ¿aparece la pérdida lateral de N04 como componente ``OPEN``, que un detector de agujeros no ve?
- ¿aparece la isla de 3 px de N01 en el núcleo del moño como ``ISLAND``, aunque sea diminuta?
- ¿qué queda en ``thin`` (desacuerdo de trazo) y qué no?

Al repositorio solo van cifras y cajas (``keydiff_retrospectivo_v14.json``). Las láminas se escriben
en ``local/share/`` (derivan de la foto; DEC‑017).
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

from pragma_ae import aem1_v13_audit as a13  # noqa: E402
from pragma_ae import aem1_v14 as w  # noqa: E402
from pragma_ae import aem1_v14_audit as audit  # noqa: E402
from pragma_ae import keydiff  # noqa: E402
from pragma_ae.imageio import load_rgb, locate_image  # noqa: E402

RUN = ROOT / "auditoria" / "aem1v14_20260926T063238Z_67d41850"
MAPPING_SHA256 = "1a68b79e3df2ab7e4fe8f75daef16ebe3c933d4bdcf4eb8fb582e3e47c3f1a66"
LATERAL_X_MAX = 2900
PAIRS = [("N01", "N04"), ("N02", "N04"), ("N03", "N04"), ("N05", "N04"), ("N06", "N04"), ("N01", "N05")]
SHEETS = [("N01", "N04"), ("N06", "N04"), ("N01", "N05")]


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def overlap_box(bbox, box) -> bool:
    return not (bbox[2] <= box[0] or box[2] <= bbox[0] or bbox[3] <= box[1] or box[3] <= bbox[1])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--sheets", type=Path, default=ROOT / "local" / "share" / "keydiff_v14")
    args = parser.parse_args(argv)
    if sha(args.mapping) != MAPPING_SHA256:
        raise SystemExit("mapeo sellado distinto del registrado")
    mapping = json.loads(args.mapping.read_text(encoding="utf-8"))["mapping"]
    labels = sorted(mapping)
    loaded = audit.load_masks(a13._read(args.zip), [mapping[lab]["candidate_id"] for lab in labels])
    masks = {lab: loaded[mapping[lab]["candidate_id"]] for lab in labels}
    first = json.loads((RUN / "juicios_claude_crudos_v14.json").read_text(encoding="utf-8"))["candidates"]
    second = json.loads((RUN / "segunda_llave_chatgpt_v14.json").read_text(encoding="utf-8"))["candidates"]

    lateral = np.zeros_like(masks["N04"])
    for lab in labels:
        for hole in a13.holes_with_masks(masks[lab]):
            n = str(hole["number"])
            if first[lab]["holes"].get(n) == "D" and second[lab]["holes"].get(n) == "D" and hole["bbox"][2] <= LATERAL_X_MAX:
                lateral |= hole["mask"]

    photo = load_rgb(locate_image())
    args.sheets.mkdir(parents=True, exist_ok=True)
    pairs = {}
    for key_a, key_b in PAIRS:
        diff = keydiff.compare_keys(masks[key_a], masks[key_b])
        rows = []
        for c in diff["components"]:
            crop, region = diff["masks"]["components"][c["id"]]
            local_lateral = lateral[crop[1]:crop[3], crop[0]:crop[2]]
            rows.append({**{k: v for k, v in c.items() if k != "semantic_adjudication"},
                         "px_in_lateral_D_region": int((region & local_lateral).sum()),
                         "overlaps_bun_core": overlap_box(c["bbox"], w.BUN_CORE),
                         "overlaps_h2_strip": overlap_box(c["bbox"], (2940, 620, 3040, 1010))})
        holes_b = [h["area"] for h in a13.holes_with_masks(masks[key_b])]
        pairs[f"{key_a}_vs_{key_b}"] = {"A": key_a, "B": key_b, "summary": diff["summary"],
                                        "components": rows, "enclosed_holes_of_B_ge_1000_px": holes_b}
        if (key_a, key_b) in SHEETS:
            keydiff.diff_sheet(photo, masks[key_a], masks[key_b], diff,
                               args.sheets / f"keydiff_{key_a}_vs_{key_b}.jpg", box=(2300, 250, 3300, 1300))
        print(f"{key_a} vs {key_b}: xor {diff['summary']['xor_px']} · thin {diff['summary']['thin_px']} · "
              + ", ".join(f"{r['id']} {r['kind']} {r['area_px']} {r['open_or_enclosed']} lat={r['px_in_lateral_D_region']}"
                          f"{' MOÑO' if r['overlaps_bun_core'] else ''}" for r in rows[:8]))

    out = {
        "schema": "pragma.aem1v14_keydiff_retro", "schema_version": "0.1.0",
        "nature": "EXPLORATORIO, después del desciegue y del cierre por doble llave; no cambia ningún veredicto",
        "question": "qué habría señalado la comprobación geométrica (DEC-025) tratando dos máscaras de v1.4 como dos llaves",
        "keydiff_sha256": sha(ROOT / "pragma_ae" / "keydiff.py"),
        "script_sha256": sha(Path(__file__)),
        "mapping_sha256": MAPPING_SHA256,
        "tolerance_px": keydiff.TOLERANCE_PX,
        "lateral_D_region_px": int(lateral.sum()),
        "mapping": {lab: mapping[lab]["candidate_id"] for lab in labels},
        "pairs": pairs,
    }
    (RUN / "keydiff_retrospectivo_v14.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n",
                                                        encoding="utf-8")
    print("región lateral D:", out["lateral_D_region_px"], "px")


if __name__ == "__main__":
    main()
