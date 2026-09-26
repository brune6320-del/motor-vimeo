"""A-E0 · contrato, validación y congelado de ``scene_inventory.json``.

El inventario es la referencia contra la que se medirán los proponentes. Por eso este
módulo es deliberadamente estricto: un inventario solo se puede congelar cuando la
ontología está ratificada, la revisión está hecha, no quedan campos por verificar y
todas las máscaras GT obligatorias existen y coinciden por hash.

Dos modos de revisión (DEC-024):

- ``HUMAN_REVIEWED`` → ``reference_type = HUMAN_GT``;
- ``AI_DOUBLE_KEY_REVIEWED`` → ``reference_type = AI_CONSENSUS_REFERENCE``: dos llaves de IA
  registradas por hash, ontología ratificada por la persona usuaria (``ratified_by``) y cada
  máscara GT con ``derivation`` que no dependa de SAM 2 (``AI_POLYGON_RASTER`` o
  ``AI_POLYGON_CLASSICAL_REFINEMENT``; ChatGPT 006). ``AI_CONSENSUS_REFERENCE`` nunca se
  convierte en ``HUMAN_GT``; solo una máscara con ``human_ratified`` cuenta como humana.

Los nombres de campo siguen el contrato ``SceneObject`` de PROJECT_STATE §13.2
(``id``, ``canonical_name``, ``synonyms``, ``tier``, ``bbox``, ``gt_mask``,
``occlusion``, ``truncation``, ``parent_id``, ``ignore_reason``). Las extensiones
propuestas (``concept_en``, ``kind``, ``occluded_by``, ``review``, ``notes``,
``bbox_source``, ``gt_required``) están documentadas en ``ae0/ONTOLOGIA_PROPUESTA.md``.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from . import EXPECTED_IMAGE_SHA256, EXPECTED_IMAGE_SIZE
from .masks import mask_bbox, packed_sha256

SCHEMA = "pragma.scene_inventory"
SCHEMA_VERSION = "0.1.0"
STATUSES = ("DRAFT_UNVERIFIED", "HUMAN_REVIEWED", "AI_DOUBLE_KEY_REVIEWED", "FROZEN")
REFERENCE_TYPES = ("HUMAN_GT", "AI_CONSENSUS_REFERENCE")
REVIEW_TO_REFERENCE = {"HUMAN_REVIEWED": "HUMAN_GT", "AI_DOUBLE_KEY_REVIEWED": "AI_CONSENSUS_REFERENCE"}
DERIVATIONS = ("AI_POLYGON_RASTER", "AI_POLYGON_CLASSICAL_REFINEMENT", "SAM2_ASSISTED", "HUMAN_PAINTED")
# SAM2_ASSISTED es secundaria y no bloqueante (ChatGPT 006): no puede ser la referencia de A-E1.
AI_REFERENCE_DERIVATIONS = ("AI_POLYGON_RASTER", "AI_POLYGON_CLASSICAL_REFINEMENT")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
TIERS = ("A", "B", "C", "IGNORE")
KINDS = ("instance", "part", "stuff", "text")
LEVELS = ("none", "low", "medium", "high", "extreme", "unknown")
# Fracción visible aproximada que representa cada nivel (para reglas de tier).
LEVEL_HIDDEN_RANGE = {
    "none": (0.00, 0.00), "low": (0.00, 0.25), "medium": (0.25, 0.50),
    "high": (0.50, 0.90), "extreme": (0.90, 1.00), "unknown": (0.0, 1.0),
}
ID_PATTERN = re.compile(r"^ae0_\d{3}$")
REQUIRED_OBJECT_FIELDS = (
    "id", "canonical_name", "concept_en", "kind", "tier", "bbox",
    "occlusion", "truncation", "parent_id", "occluded_by", "gt_required",
    "gt_mask", "ignore_reason", "review",
)


def sha256_file(path, chunk: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def load(path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def canonical_bytes(inventory: dict) -> bytes:
    """Serialización canónica sin el bloque ``freeze`` (lo que se firma)."""
    body = {k: v for k, v in inventory.items() if k != "freeze"}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def content_sha256(inventory: dict) -> str:
    return hashlib.sha256(canonical_bytes(inventory)).hexdigest()


def load_gt_mask(inventory_dir: Path, entry: dict, size) -> np.ndarray:
    """Lee una máscara GT PNG (0/255 o 0/1) y la devuelve booleana."""
    from PIL import Image

    path = (inventory_dir / entry["path"]).resolve()
    with Image.open(path) as handle:
        array = np.asarray(handle.convert("L"))
    if (array.shape[1], array.shape[0]) != tuple(size):
        raise ValueError(f"{entry['path']}: tamaño {array.shape[1]}×{array.shape[0]} ≠ {size[0]}×{size[1]}")
    values = set(np.unique(array).tolist())
    if not values <= {0, 1, 255}:
        raise ValueError(f"{entry['path']}: la GT debe ser binaria (0/255); valores {sorted(values)[:6]}…")
    return array > 0


class Report:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str):
        self.errors.append(message)

    def warn(self, message: str):
        self.warnings.append(message)


def _ancestors(objects: dict, oid: str, report: Report | None = None) -> list[str]:
    chain, seen, current = [], {oid}, objects[oid].get("parent_id")
    while current is not None:
        if current in seen:
            if report is not None:
                report.error(f"{oid}: ciclo en parent_id ({' → '.join(chain + [current])})")
            break
        if current not in objects:
            break
        chain.append(current)
        seen.add(current)
        current = objects[current].get("parent_id")
    return chain


def lineage(objects: dict, oid: str) -> set[str]:
    """Antepasados y descendientes: pares que NO cuentan como fusión."""
    related = set(_ancestors(objects, oid))
    for other in objects:
        if oid in _ancestors(objects, other):
            related.add(other)
    return related


def validate(inventory: dict, inventory_dir=None, image_sha256: str | None = None) -> dict:
    """Valida el inventario y deriva su estado A-E0. Nunca modifica la entrada."""
    report = Report()
    inventory_dir = Path(inventory_dir or ".")

    if inventory.get("schema") != SCHEMA:
        report.error(f"schema debe ser {SCHEMA!r}")
    if inventory.get("schema_version") != SCHEMA_VERSION:
        report.error(f"schema_version debe ser {SCHEMA_VERSION!r}")
    status = inventory.get("status")
    if status not in STATUSES:
        report.error(f"status inválido: {status!r}")
    reviewed_as = (inventory.get("freeze") or {}).get("reviewed_as", "HUMAN_REVIEWED") if status == "FROZEN" else status
    ai_mode = reviewed_as == "AI_DOUBLE_KEY_REVIEWED"
    declared_type = inventory.get("reference_type")
    if declared_type is not None and declared_type not in REFERENCE_TYPES:
        report.error(f"reference_type inválido: {declared_type!r}")
    expected_type = REVIEW_TO_REFERENCE.get(reviewed_as)
    if expected_type == "AI_CONSENSUS_REFERENCE" and declared_type != expected_type:
        report.error("una revisión por doble llave de IA exige reference_type = AI_CONSENSUS_REFERENCE (nunca HUMAN_GT)")
    if expected_type == "HUMAN_GT" and declared_type not in (None, "HUMAN_GT"):
        report.error("una revisión humana declara reference_type = HUMAN_GT")
    reference_type = expected_type or declared_type
    if ai_mode:
        keys = (inventory.get("double_key") or {}).get("keys", [])
        auditors = [str(k.get("auditor", "")).strip() for k in keys]
        if len(keys) != 2 or len(set(auditors)) != 2 or not all(auditors) \
                or not all(HEX64.match(str(k.get("inventory_sha256", ""))) for k in keys):
            report.error("double_key.keys exige dos llaves de auditores distintos, cada una con inventory_sha256")

    image = inventory.get("image", {})
    if image.get("sha256") != EXPECTED_IMAGE_SHA256:
        report.error("image.sha256 no es la foto de aceptación")
    if image_sha256 is not None and image_sha256 != image.get("sha256"):
        report.error("la imagen entregada no coincide con image.sha256")
    size = (image.get("width"), image.get("height"))
    if size != EXPECTED_IMAGE_SIZE:
        report.error(f"tamaño declarado {size} ≠ {EXPECTED_IMAGE_SIZE}")
    width, height = EXPECTED_IMAGE_SIZE

    ontology = inventory.get("ontology", {})
    min_side = int(ontology.get("min_short_side_px", 32))
    tier_a_side = int(ontology.get("tier_a_min_short_side_px", 64))
    ratified = bool(ontology.get("ratified", False))
    if ai_mode and ratified and not str(ontology.get("ratified_by", "")).strip():
        report.error("en modo doble llave de IA, la ontología la ratifica la persona usuaria: falta ontology.ratified_by")

    raw_objects = inventory.get("objects", [])
    objects: dict[str, dict] = {}
    for position, obj in enumerate(raw_objects):
        missing = [f for f in REQUIRED_OBJECT_FIELDS if f not in obj]
        oid = obj.get("id", f"#{position}")
        if missing:
            report.error(f"{oid}: faltan campos {missing}")
            continue
        if not ID_PATTERN.match(str(oid)):
            report.error(f"{oid}: id debe seguir ae0_NNN")
        if oid in objects:
            report.error(f"{oid}: id duplicado")
        objects[oid] = obj

    names: dict[str, str] = {}
    gt_status: dict[str, str] = {}
    gt_reference: dict[str, dict] = {}
    pending_review: list[str] = []
    for oid, obj in objects.items():
        tier, kind = obj["tier"], obj["kind"]
        if tier not in TIERS:
            report.error(f"{oid}: tier inválido {tier!r}")
        if kind not in KINDS:
            report.error(f"{oid}: kind inválido {kind!r}")
        for field in ("occlusion", "truncation"):
            if obj[field] not in LEVELS:
                report.error(f"{oid}: {field} inválido {obj[field]!r}")

        name = str(obj["canonical_name"]).strip()
        if not name:
            report.error(f"{oid}: canonical_name vacío")
        elif name in names:
            report.warn(f"{oid}: canonical_name repetido con {names[name]} ({name!r}); desambigua")
        names.setdefault(name, oid)

        bbox = obj["bbox"]
        if not (isinstance(bbox, list) and len(bbox) == 4 and all(isinstance(v, int) for v in bbox)):
            report.error(f"{oid}: bbox debe ser [x1, y1, x2, y2] enteros")
            continue
        x1, y1, x2, y2 = bbox
        if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
            report.error(f"{oid}: bbox {bbox} fuera de la imagen o vacía (semiabierta)")
        short_side = min(x2 - x1, y2 - y1)

        if tier == "IGNORE" and not obj["ignore_reason"]:
            report.error(f"{oid}: tier IGNORE exige ignore_reason")
        if tier != "IGNORE" and obj["ignore_reason"]:
            report.warn(f"{oid}: ignore_reason presente pero tier={tier}")
        contact_critical = obj.get("contact_critical", False)   # ChatGPT 001 R4: excepción de tamaño
        if not isinstance(contact_critical, bool):
            report.error(f"{oid}: contact_critical debe ser booleano")
        if tier in ("A", "B") and short_side < min_side and not contact_critical:
            report.warn(f"{oid}: lado corto {short_side}px < mínimo {min_side}px; ¿IGNORE below_min_size?")
        if tier == "A" and short_side < tier_a_side and obj["concept_en"] != "person":
            report.warn(f"{oid}: Tier A con lado corto {short_side}px < {tier_a_side}px; ¿Tier B?")
        if tier == "A" and obj["concept_en"] != "person" and obj["occlusion"] in ("high", "extreme"):
            report.warn(f"{oid}: Tier A con oclusión {obj['occlusion']}; la regla propuesta sugiere Tier B")
        if tier == "C" and kind == "instance" and obj["parent_id"] is None:
            report.warn(f"{oid}: Tier C suele ser parte/stuff/texto; instancia sin padre")
        if kind == "part" and obj["parent_id"] is None:
            report.error(f"{oid}: kind=part exige parent_id")

        if obj["concept_en"] == "person":
            if tier != "A":
                report.error(f"{oid}: toda persona es Tier A (regla de la fase)")
            if not obj["gt_required"]:
                report.error(f"{oid}: las personas exigen máscara GT (gt_required=true)")

        parent = obj["parent_id"]
        if parent is not None and parent not in objects:
            report.error(f"{oid}: parent_id {parent!r} no existe")
        if parent == oid:
            report.error(f"{oid}: parent_id apunta a sí mismo")
        for other in obj["occluded_by"]:
            if other not in objects:
                report.error(f"{oid}: occluded_by {other!r} no existe")
            elif other == oid:
                report.error(f"{oid}: no puede ocluirse a sí mismo")
        if obj["occluded_by"] and obj["occlusion"] == "none":
            report.warn(f"{oid}: occluded_by no vacío pero occlusion='none'")

        if obj["review"]:
            pending_review.append(oid)

        entry = obj["gt_mask"]
        if entry is None:
            gt_status[oid] = "missing" if obj["gt_required"] else "not_required"
            continue
        derivation = entry.get("derivation")
        if derivation is not None and derivation not in DERIVATIONS:
            report.error(f"{oid}: derivation inválida {derivation!r}")
        if ai_mode and derivation not in AI_REFERENCE_DERIVATIONS:
            report.error(f"{oid}: en modo doble llave de IA la GT necesita derivation en {AI_REFERENCE_DERIVATIONS} "
                         f"(recibida {derivation!r}; SAM2_ASSISTED es secundaria y no bloqueante)")
        human = entry.get("human_ratified", False)
        if human and not str(entry.get("human_ratified_by", "")).strip():
            report.error(f"{oid}: human_ratified exige human_ratified_by")
        gt_reference[oid] = {"derivation": derivation,
                             "reference_type": "HUMAN_GT" if (human or reference_type == "HUMAN_GT") else reference_type}
        path = inventory_dir / entry.get("path", "")
        if not path.is_file():
            gt_status[oid] = "file_missing"
            report.error(f"{oid}: gt_mask {entry.get('path')!r} no existe")
            continue
        try:
            mask = load_gt_mask(inventory_dir, entry, EXPECTED_IMAGE_SIZE)
        except ValueError as exc:
            gt_status[oid] = "invalid"
            report.error(f"{oid}: {exc}")
            continue
        if entry.get("mask_sha256") != packed_sha256(mask):
            gt_status[oid] = "hash_mismatch"
            report.error(f"{oid}: mask_sha256 no coincide con el contenido de {entry['path']}")
            continue
        box = mask_bbox(mask)
        if box is None:
            gt_status[oid] = "empty"
            report.error(f"{oid}: máscara GT vacía")
            continue
        tolerance = max(8, int(0.02 * max(x2 - x1, y2 - y1)))
        if (box[0] < x1 - tolerance or box[1] < y1 - tolerance
                or box[2] > x2 + tolerance or box[3] > y2 + tolerance):
            report.error(f"{oid}: la GT {box} se sale de bbox {bbox} (tolerancia {tolerance}px)")
        gt_status[oid] = "valid"

    for oid in objects:
        _ancestors(objects, oid, report)

    counts = {tier: sum(1 for o in objects.values() if o["tier"] == tier) for tier in TIERS}
    gt_missing = sorted(oid for oid, s in gt_status.items() if s not in ("valid", "not_required"))

    if status == "FROZEN":
        freeze = inventory.get("freeze") or {}
        if freeze.get("content_sha256") != content_sha256(inventory):
            report.error("FROZEN pero content_sha256 no coincide: el inventario cambió después de congelarse")

    if report.errors:
        state = "A_E0_INVALID"
    elif status == "DRAFT_UNVERIFIED":
        state = "A_E0_DRAFT"
    elif not ratified:
        state = "A_E0_PENDING_RATIFICATION"
    elif pending_review:
        state = "A_E0_PENDING_REVIEW_ITEMS"
    elif gt_missing:
        state = "A_E0_PENDING_GT"
    elif status == "FROZEN":
        state = "A_E0_FROZEN"
    else:
        state = "A_E0_READY_TO_FREEZE"

    return {
        "state": state,
        "status": status,
        "review_mode": "AI_DOUBLE_KEY" if ai_mode else ("HUMAN" if reviewed_as == "HUMAN_REVIEWED" else None),
        "reference_type": reference_type,
        "gt_reference": gt_reference,
        "ontology_ratified": ratified,
        "objects": len(objects),
        "tier_counts": counts,
        "gt_required": sorted(o for o, v in objects.items() if v["gt_required"]),
        "gt_status": gt_status,
        "gt_missing_or_invalid": gt_missing,
        "pending_review": pending_review,
        "errors": report.errors,
        "warnings": report.warnings,
        "content_sha256": content_sha256(inventory),
        "evaluation_allowed": state == "A_E0_FROZEN",
        "note": "Solo un inventario A_E0_FROZEN puede usarse como GT de A-E1; cualquier otro estado implica INCONCLUSIVE.",
    }


def freeze(inventory: dict, inventory_dir=None, frozen_by: str = "", now: datetime | None = None) -> dict:
    """Devuelve una copia congelada o lanza ValueError con el motivo."""
    reviewed_as = inventory.get("status")
    if reviewed_as not in REVIEW_TO_REFERENCE:
        raise ValueError("Solo se congela un inventario con status HUMAN_REVIEWED o AI_DOUBLE_KEY_REVIEWED")
    result = validate(inventory, inventory_dir)
    if result["state"] != "A_E0_READY_TO_FREEZE":
        raise ValueError(f"No se puede congelar: estado {result['state']}; errores={result['errors']}")
    if not frozen_by.strip():
        raise ValueError("frozen_by es obligatorio: firma quien congela (la persona usuaria, o las dos llaves de IA)")
    frozen = copy.deepcopy(inventory)
    frozen["status"] = "FROZEN"
    frozen.pop("freeze", None)
    frozen["freeze"] = {
        "frozen_by": frozen_by.strip(),
        "reviewed_as": reviewed_as,
        "reference_type": REVIEW_TO_REFERENCE[reviewed_as],
        "frozen_utc": (now or datetime.now(timezone.utc)).isoformat(),
        "gt_mask_sha256": {
            o["id"]: o["gt_mask"]["mask_sha256"] for o in frozen["objects"] if o["gt_mask"]
        },
    }
    frozen["freeze"]["content_sha256"] = content_sha256(frozen)
    return frozen
