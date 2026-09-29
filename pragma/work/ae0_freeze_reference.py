"""Congela la referencia A‑E0 (ORDEN 181): composición final, ``gt_mask`` e ``inv.freeze``.

    python3 work/ae0_freeze_reference.py            # compone, escribe ae0/gt/, registra y congela
    python3 work/ae0_freeze_reference.py --check    # valida el inventario congelado contra ae0/gt/

Pasos:
1. Comprueba por SHA‑256 todo lo que se aplica:
   - las adjudicaciones y los dos archivos de parches;
   - las dos respuestas de ChatGPT que los aceptaron (017 y 018) y la de Codex.
   La custodia de las dos llaves de polígonos la comprueba ``compose``.
2. ``ae0_compose_masks.compose`` con los 6 parches de la 017 y los 8 de la 018, en ese orden.
3. Escribe ``ae0/gt/<persona>_estimate.png`` y ``_uncertain.png`` (0/255; no versionado, DEC‑017).
4. Registra en cada persona su ``gt_mask``:
   - ``derivation = AI_POLYGON_RASTER`` y ``mask_sha256`` (``packed_sha256`` de la estimación);
   - la zona incierta, con su ruta y su hash;
   - ``estimate_policy``.
5. Añade ``gt_provenance`` y congela con ``pragma_ae.inventory.freeze``, de modo que el
   ``content_sha256`` cubre las máscaras y su procedencia.
6. Escribe ``ae0/CONGELADO_REFERENCIA_A-E0.json`` y ``composicion_referencia_final.json``: solo
   hashes y cifras.
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
sys.path.insert(0, str(ROOT / "work"))

from pragma_ae import inventory as inv  # noqa: E402
from pragma_ae.masks import packed_sha256  # noqa: E402

CP = "ae0/comparacion_poligonos"
INVENTORY = ROOT / "ae0/scene_inventory.json"
GT = ROOT / "ae0/gt"
RECORD = ROOT / "ae0/CONGELADO_REFERENCIA_A-E0.json"
FINAL = ROOT / CP / "composicion_referencia_final.json"
INPUTS = {
    "adjudications": (f"{CP}/adjudicacion_poligonos_final.json", "f7f8abe4cf2f49aad40845521018090fe73e8a510a1a384ecc5a993a2bcd311e"),
    "patches_017": (f"{CP}/parches_propuestos_v0.json", "1d1e08c06affe2f8e41bd19cd661290a86aaa1ab2c678f296bc970e0fa7ae095"),
    "patches_018": (f"{CP}/parches_codex_propuestos_v0.json", "56e033925ee088432bc39ad701d467083a5719800380ae1c7f77baf609ab3ff8"),
    "chatgpt_017": (f"{CP}/revision_chatgpt_teselas_A-E0.json", "35af1ea1a75fe02269db7739f0e0c5c7970913991b085eefee6214686dc313cd"),
    "chatgpt_018": (f"{CP}/adjudicacion_chatgpt_codex_A-E0_ORDEN181.json", "b7ecc701f17147197b1ba7bf5c91fd1387259e3edf2281d8682479ac539160e3"),
    "codex": (f"{CP}/revision_codex_teselas_A-E0.json", "77cc16cd968394c14916d6f24830bfdca1cbea64c6de8551c0970f9982c61cd2"),
}
STAGE = ("ETAPA_1 (ae0/ONTOLOGIA_PROPUESTA.md §6): máscaras de las 3 personas y cajas de todos los objetos. "
         "Techo de A-E1: INCONCLUSIVE_GT_INCOMPLETE (35 Tier A sin máscara). Lo que sí mide: "
         "tier_a_box_screen_failures, IoU de cada persona con sus cotas, fusión y contacto entre personas")
FROZEN_BY = ("doble llave de IA: claude (polígonos 39a071e0…04c5) + chatgpt (polígonos d7b93141…2fc2); "
             "GO de ChatGPT en la ORDEN 181 (b7ecc701…60e3)")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_inputs() -> dict:
    out = {}
    for name, (rel, want) in INPUTS.items():
        got = sha(ROOT / rel)
        if got != want:
            raise SystemExit(f"{name}: {rel} tiene {got}, se esperaba {want}")
        out[name] = {"file": rel, "sha256": got}
    for name in ("chatgpt_017", "chatgpt_018"):
        summary = json.loads((ROOT / INPUTS[name][0]).read_text(encoding="utf-8"))["summary"]
        if summary.get("patches_contest", 0) or summary.get("contest", 0):
            raise SystemExit(f"{name}: hay parches contestados; la regla conjunta exige recomponer sin ellos")
    return out


def build():
    from PIL import Image
    from ae0_compose_masks import PERSONS, compose
    inputs = check_inputs()
    adjudications = json.loads((ROOT / INPUTS["adjudications"][0]).read_text(encoding="utf-8"))["adjudications"]
    patches = [p for key in ("patches_017", "patches_018")
               for p in json.loads((ROOT / INPUTS[key][0]).read_text(encoding="utf-8"))["patches"]]
    out = compose(adjudications, patches=patches)
    GT.mkdir(parents=True, exist_ok=True)
    inventory = inv.load(INVENTORY)
    if inventory.get("status") != "AI_DOUBLE_KEY_REVIEWED":
        raise SystemExit(f"el inventario está en {inventory.get('status')!r}: ya congelado o sin revisar")
    by_id = {o["id"]: o for o in inventory["objects"]}
    persons = {}
    for oid in PERSONS:
        est, unc = out["refs"][oid]["estimate"], out["refs"][oid]["uncertain"]
        files = {}
        for name, mask in (("estimate", est), ("uncertain", unc)):
            path = GT / f"{oid}_{name}.png"
            Image.fromarray(mask.astype(np.uint8) * 255).save(path)
            back = np.asarray(Image.open(path).convert("L")) > 0
            if not np.array_equal(back, mask):
                raise SystemExit(f"{path}: el PNG no reproduce la máscara")
            files[name] = {"path": f"gt/{oid}_{name}.png", "mask_sha256": packed_sha256(mask), "png_sha256": sha(path)}
        by_id[oid]["gt_mask"] = {
            "path": files["estimate"]["path"], "mask_sha256": files["estimate"]["mask_sha256"],
            "derivation": "AI_POLYGON_RASTER", "estimate_policy": "MIDLINE",
            "uncertain_path": files["uncertain"]["path"], "uncertain_mask_sha256": files["uncertain"]["mask_sha256"],
        }
        persons[oid] = {"files": files, **{k: v for k, v in out["report"][oid].items() if k != "keydiff"}}
    inventory["gt_provenance"] = {
        "derivation": "AI_POLYGON_RASTER",
        "polygon_keys": {"claude": "39a071e0bbde68efb23035a31cc67e09e0f74319bc0db2cb64a988dead7504c5",
                         "chatgpt": "d7b93141…2fc2 (ae0/RECEPCION_POLIGONOS_CHATGPT_A-E0.json)"},
        "composition": "work/ae0_compose_masks.py: keydiff + MIDLINE + unión de uncertain_rings + EXCLUSIVITY + parches",
        "cross_person_rule": "EXCLUSIVITY",
        "estimate_policy": "MIDLINE",
        "inputs": inputs,
        "three_state": "gt_mask es la estimación binaria; uncertain_path es la zona incierta. Toda métrica A-E1 "
                       "lleva sus cotas min/max (keydiff.iou_with_uncertainty)",
    }
    frozen = inv.freeze(inventory, ROOT / "ae0", frozen_by=FROZEN_BY)
    result = inv.validate(frozen, ROOT / "ae0")
    if result["state"] != "A_E0_FROZEN":
        raise SystemExit(f"tras congelar, estado {result['state']}: {result['errors']}")
    INVENTORY.write_text(json.dumps(frozen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    final = {"schema": "pragma.ae0_reference_final", "schema_version": "0.1.0", "inputs": inputs,
             "patches_applied": out["patches_applied"], "estimate_policy": "MIDLINE", "cross_person_rule": "EXCLUSIVITY",
             "persons": persons}
    FINAL.write_text(json.dumps(final, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    record = {
        "schema": "pragma.ae0_reference_freeze_record", "schema_version": "0.1.0",
        "what": "referencia A-E0 de las tres personas: inventario con gt_mask congelado (FROZEN)",
        "reference_type": frozen["freeze"]["reference_type"],
        "stage": STAGE,
        "inventory": {"file": "ae0/scene_inventory.json", "file_sha256": sha(INVENTORY),
                      "content_sha256": frozen["freeze"]["content_sha256"], "validator_state": result["state"],
                      "errors": result["errors"], "warnings": len(result["warnings"])},
        "freeze": frozen["freeze"],
        "masks": {oid: persons[oid]["files"] for oid in PERSONS},
        "final_composition": {"file": FINAL.relative_to(ROOT).as_posix(), "sha256": sha(FINAL)},
        "not_versioned": "ae0/gt/*.png (DEC-017): en git solo van los hashes",
    }
    RECORD.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return record


def check() -> int:
    frozen = inv.load(INVENTORY)
    result = inv.validate(frozen, ROOT / "ae0")
    ok = result["state"] == "A_E0_FROZEN"
    for o in frozen["objects"]:
        entry = o["gt_mask"]
        if entry and "uncertain_path" in entry:
            unc = inv.load_gt_mask(ROOT / "ae0", {"path": entry["uncertain_path"]}, (4000, 2248))
            ok &= packed_sha256(unc) == entry["uncertain_mask_sha256"]
    print(json.dumps({"state": result["state"], "errors": result["errors"], "uncertain_hashes_ok": ok,
                      "content_sha256": result["content_sha256"]}, ensure_ascii=False))
    return 0 if ok else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        raise SystemExit(check())
    record = build()
    print(json.dumps({"inventory": record["inventory"], "masks": record["masks"]}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
