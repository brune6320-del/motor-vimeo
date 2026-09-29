"""Valida una llave de inventario A‑E0 antes de entregarla (formato en ``ae0/FORMATO_LLAVE_A-E0.md``).

    python3 work/validate_ae0_key.py <llave.json>

Comprueba el esquema ``pragma.scene_inventory`` con el validador del kit y el bloque ``key``: auditor,
declaración de ceguera, hash de la foto y ontología. Además, que no queden listas ``review`` sin
cerrar. Imprime el SHA‑256 del archivo, que es el que se compromete.
"""

from __future__ import annotations

import collections
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pragma_ae import EXPECTED_IMAGE_SHA256  # noqa: E402
from pragma_ae import inventory as inv  # noqa: E402

KEY_FIELDS = ("auditor", "blind_statement", "image_sha256", "ontology", "created")


def check(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    result = inv.validate(data, path.parent)
    errors = list(result["errors"])
    key = data.get("key") or {}
    errors += [f"key.{f} falta" for f in KEY_FIELDS if not key.get(f)]
    if key.get("image_sha256") and key["image_sha256"] != EXPECTED_IMAGE_SHA256:
        errors.append("key.image_sha256 no es la foto de PRAGMA")
    open_reviews = [o["id"] for o in data.get("objects", []) if o.get("review")]
    if open_reviews:
        errors.append(f"listas review sin cerrar: {open_reviews}")
    persons = [o["id"] for o in data.get("objects", []) if str(o.get("concept_en", "")).lower() == "person"]
    errors += [f"{oid}: toda persona es tier A (R1)" for oid in persons
               if next(o for o in data["objects"] if o["id"] == oid)["tier"] != "A"]
    objs = data.get("objects", [])
    return {
        "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "content_sha256": result.get("content_sha256"),
        "objects": len(objs),
        "tiers": dict(collections.Counter(o.get("tier") for o in objs)),
        "kinds": dict(collections.Counter(o.get("kind") for o in objs)),
        "persons": persons,
        "errors": errors,
        "warnings": result.get("warnings", []),
        "valid_key": not errors,
    }


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        raise SystemExit(__doc__)
    report = check(Path(args[0]))
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["valid_key"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
