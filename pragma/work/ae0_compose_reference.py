"""Compone el inventario de referencia A‑E0 adjudicado (DEC‑024) a partir de las dos llaves.

    python3 work/ae0_compose_reference.py [--codex <respuesta_codex.json>]

Entradas, todas en git:
- las dos llaves (`ae0/llaves/`);
- la propuesta de Claude (`ae0/comparacion/propuesta_adjudicacion_claude.json`);
- las decisiones de la segunda llave y la concesión de Claude en Q1
  (`ae0/comparacion/decisiones_segunda_llave.json`);
- la regla de la tercera revisión (`ae0/comparacion/tercera_revision_reglas.json`) y, si ya existe, la
  respuesta de Codex.

Salida: `ae0/scene_inventory.json`, con `status = AI_DOUBLE_KEY_REVIEWED` y
`reference_type = AI_CONSENSUS_REFERENCE`. Mientras falte la respuesta de Codex, C:022 y C:025 van en
`pending_third_review` y no en `objects`.

Reglas de composición (las declara la carta 013):
1. `SAME`: se parte del objeto de la llave de Claude. Se aplican la caja y los atributos adjudicados.
   Un atributo que la propuesta no nombra conserva el valor de Claude, y queda listado en
   `adjudication_log.unspecified_attribute_defaults` para que se pueda objetar.
2. `A_ONLY` / `B_ONLY` con `INCLUDE`: se copia el objeto de su llave. Los de ChatGPT reciben ids
   nuevos desde `ae0_060`, y sus relaciones se traducen por el emparejamiento. `EXCLUDE`: se retira,
   y su id no se reutiliza nunca.
3. Q1 = dos mesas: C:004 pasa a ser la mesa central (izquierda) y la mesa derecha es un objeto nuevo
   (desde G:020). Los manteles G:041 y G:042 son partes de cada una, con la caja de su mesa.
4. Q2: C:005 queda como superficie o mueble auxiliar, sin categoría más específica, y C:027 como
   objeto aparte. G:008 se retira porque su autora lo corrigió.
5. Q3: C:007 es una silla o sillón con el respaldo abierto. G:024 se retira: es la pared vista a
   través del respaldo.
6. El tier se recalcula para todos con R1–R4 (R‑tier).
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pragma_ae import inventory as inv  # noqa: E402

KA, KB = ROOT / "ae0/llaves/llave_claude_A-E0.json", ROOT / "ae0/llaves/llave_chatgpt_A-E0.json"
PROPOSAL = ROOT / "ae0/comparacion/propuesta_adjudicacion_claude.json"
DECISIONS = ROOT / "ae0/comparacion/decisiones_segunda_llave.json"
RULES = ROOT / "ae0/comparacion/tercera_revision_reglas.json"
OUT = ROOT / "ae0/scene_inventory.json"
FIRST_NEW_ID = 60
CENTRAL_TABLE_BOX = [1245, 1485, 2135, 2120]
RIGHT_TABLE_BOX = [3090, 1505, 3725, 2248]
ATTRS = ("occlusion", "truncation")


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tier_rule(o) -> str:
    if o["concept_en"] == "person":
        return "A"
    if o["kind"] != "instance":
        return "C"
    x1, y1, x2, y2 = o["bbox"]
    short = min(x2 - x1, y2 - y1)
    if short < 32 and not o.get("contact_critical"):
        return "IGNORE"
    if o["occlusion"] in ("high", "extreme") or short < 64:
        return "B"
    return "A"


def compose(codex=None) -> dict:
    A = json.loads(KA.read_text(encoding="utf-8"))
    B = json.loads(KB.read_text(encoding="utf-8"))
    AD, BD = {o["id"]: o for o in A["objects"]}, {o["id"]: o for o in B["objects"]}
    proposal = json.loads(PROPOSAL.read_text(encoding="utf-8"))["proposals"]
    decisions = json.loads(DECISIONS.read_text(encoding="utf-8"))
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    ref, b_to_ref, retired, defaults, log = {}, {}, [], [], []
    next_id = [FIRST_NEW_ID]

    def new_id():
        oid = f"ae0_{next_id[0]:03d}"
        next_id[0] += 1
        return oid

    def mean_box(a, b):
        return [round((p + q) / 2) for p, q in zip(a, b)]

    for p in proposal:
        if p["type"] != "SAME":
            continue
        a, b = AD[p["a_id"]], BD[p["b_id"]]
        o = copy.deepcopy(a)
        o["bbox"] = mean_box(a["bbox"], b["bbox"]) if isinstance(p["bbox"], str) else list(p["bbox"])
        for field, value in (p.get("attributes") or {}).items():
            if field in ("tier",):
                continue
            o[field] = value
        for field in ATTRS:
            if field not in (p.get("attributes") or {}) and a.get(field) != b.get(field):
                defaults.append({"ref_id": a["id"], "field": field, "claude": a.get(field), "chatgpt": b.get(field)})
        if p.get("canonical_name"):
            o["canonical_name"] = p["canonical_name"]
        if p.get("concept_en"):
            o["concept_en"] = p["concept_en"]
        o["sources"] = {"claude": a["id"], "chatgpt": b["id"]}
        o["bbox_source"] = "adjudicated_double_key"
        ref[a["id"]] = o
        b_to_ref[b["id"]] = a["id"]

    for p in proposal:
        if p["type"] == "A_ONLY":
            if p["verdict"] == "INCLUDE":
                o = copy.deepcopy(AD[p["id"]])
                o["sources"] = {"claude": p["id"], "chatgpt": None}
                o["bbox_source"] = "adjudicated_double_key"
                ref[p["id"]] = o
            else:
                retired.append({"id": p["id"], "key": "claude", "reason": p["basis"]})
    b_includes = [p for p in proposal if p["type"] == "B_ONLY" and p["verdict"].startswith("INCLUDE")]

    # Q1: dos mesas
    central = ref.pop("ae0_004", None) or copy.deepcopy(AD["ae0_004"])
    central.update({"bbox": CENTRAL_TABLE_BOX, "canonical_name": "mesa central (a la izquierda de la persona del frente)",
                    "concept_en": "table", "occlusion": "medium", "truncation": "none", "occluded_by": ["ae0_002"],
                    "sources": {"claude": "ae0_004 (parte izquierda)", "chatgpt": "ae0_007"},
                    "bbox_source": "adjudicated_double_key",
                    "notes": "Q1: dos mesas (concesión de Claude). Mantel blanco con rosas; la tapa en parte la persona del frente."})
    ref["ae0_004"] = central
    b_to_ref["ae0_007"] = "ae0_004"
    right_id = new_id()
    right = copy.deepcopy(BD["ae0_020"])
    right.update({"id": right_id, "bbox": RIGHT_TABLE_BOX, "canonical_name": "mesa redonda derecha",
                  "occlusion": "medium", "truncation": "low", "occluded_by": ["ae0_002"],
                  "sources": {"claude": "ae0_004 (parte derecha)", "chatgpt": "ae0_020"},
                  "bbox_source": "adjudicated_double_key",
                  "notes": "Q1: mesa aparte, más cerca de la cámara; sostiene los vasitos. Cortada por el borde inferior."})
    ref[right_id] = right
    b_to_ref["ae0_020"] = right_id
    # Q2
    for cid in ("ae0_005", "ae0_027"):
        ref[cid] = copy.deepcopy(AD[cid])
        ref[cid]["bbox_source"] = "adjudicated_double_key"
    ref["ae0_005"].update({"canonical_name": "superficie o mueble auxiliar cubierto (detrás de la mesa central)",
                           "concept_en": "furniture", "sources": {"claude": "ae0_005", "chatgpt": None}})
    ref["ae0_027"]["sources"] = {"claude": "ae0_027", "chatgpt": None}
    retired.append({"id": "ae0_008", "key": "chatgpt", "reason": "Q2: su autora corrigió la «silla» (superficie auxiliar + marco aparte)"})
    # Q3
    retired.append({"id": "ae0_024", "key": "chatgpt", "reason": "Q3: es la pared vista a través del respaldo abierto"})
    # Q4
    ref["ae0_021"] = copy.deepcopy(AD["ae0_021"])
    ref["ae0_021"]["sources"] = {"claude": "ae0_021", "chatgpt": None}
    pending = []
    for tag, item in rules["items"].items():
        cid = "ae0_" + item["key_ref"][2:]
        answer = (codex or {}).get(tag, {}).get("answer")
        obj = copy.deepcopy(AD[cid])
        obj["sources"] = {"claude": cid, "chatgpt": None}
        if answer is None:
            pending.append({"region": tag, "key_ref": item["key_ref"], "object": obj})
        elif answer == "DISTINCT_OBJECT":
            desc = codex[tag].get("description")
            if desc:
                obj["notes"] = f"Tercera revisión: {desc}"
            if codex[tag].get("bbox_if_distinct"):
                obj["bbox"] = list(codex[tag]["bbox_if_distinct"])
            ref[cid] = obj
        elif answer == "NOT_SEPARABLE":
            retired.append({"id": cid, "key": "claude", "reason": f"tercera revisión: NOT_SEPARABLE — {codex[tag].get('reason')}"})
        else:
            obj["tier"] = "IGNORE"
            obj["ignore_reason"] = "existencia no establecida: llaves en desacuerdo y tercera revisión sin decisión"
            ref[cid] = obj

    # Partes y stuff solo de ChatGPT
    for p in b_includes:
        b = BD[p["id"]]
        o = copy.deepcopy(b)
        oid = new_id()
        o["id"] = oid
        if p.get("bbox"):
            o["bbox"] = list(p["bbox"])
        if p["id"] == "ae0_041":
            o["bbox"] = list(CENTRAL_TABLE_BOX)
        if p["id"] == "ae0_042":
            o["bbox"] = list(RIGHT_TABLE_BOX)
        o["sources"] = {"claude": None, "chatgpt": p["id"]}
        o["bbox_source"] = "adjudicated_double_key"
        o.pop("contact_critical", None)
        ref[oid] = o
        b_to_ref[p["id"]] = oid
    for p in b_includes:
        o = ref[b_to_ref[p["id"]]]
        if o.get("parent_id"):
            o["parent_id"] = b_to_ref.get(o["parent_id"])
        o["occluded_by"] = sorted({b_to_ref[x] for x in (o.get("occluded_by") or []) if x in b_to_ref})

    # Relaciones: sin apuntar a objetos retirados o pendientes; la silla la tapa la mesa derecha
    alive = set(ref)
    ref["ae0_007"]["occluded_by"] = sorted({right_id if x == "ae0_004" else x for x in ref["ae0_007"]["occluded_by"]})
    for o in ref.values():
        o["occluded_by"] = [x for x in (o.get("occluded_by") or []) if x in alive and x != o["id"]]
        if o.get("parent_id") and o["parent_id"] not in alive:
            log.append(f"{o['id']}: parent_id {o['parent_id']} no existe en la referencia → null")
            o["parent_id"] = None
        o["tier"] = tier_rule(o) if o.get("tier") != "IGNORE" or not o.get("ignore_reason") else "IGNORE"
        o["review"] = []
        o.setdefault("gt_mask", None)
        o["gt_required"] = o["concept_en"] == "person"
        if o["tier"] != "IGNORE":
            o["ignore_reason"] = None

    # Cobertura: cada objeto de cada llave termina en la referencia, retirado o pendiente
    retired_ids = {(r["key"], r["id"]) for r in retired}
    in_ref_a = {src for o in ref.values() for src in [str((o.get("sources") or {}).get("claude") or "")] if src}
    for oid in AD:
        seen = any(s_.startswith(oid) for s_ in in_ref_a) or ("claude", oid) in retired_ids \
            or any(p_["key_ref"] == "C:" + oid[4:] for p_ in pending)
        if not seen:
            raise SystemExit(f"C:{oid[4:]} no quedó cubierto")
    for oid in BD:
        if oid not in b_to_ref and ("chatgpt", oid) not in retired_ids:
            raise SystemExit(f"G:{oid[4:]} no quedó cubierto")

    A_meta = {"auditor": "claude", "inventory_sha256": sha(KA), "content_sha256": inv.content_sha256(A),
              "committed_in": "81e26dc"}
    B_meta = {"auditor": "chatgpt", "inventory_sha256": sha(KB), "content_sha256": inv.content_sha256(B),
              "archived_in": "424e89d"}
    out = {
        "schema": inv.SCHEMA, "schema_version": inv.SCHEMA_VERSION,
        "status": "AI_DOUBLE_KEY_REVIEWED", "reference_type": "AI_CONSENSUS_REFERENCE",
        "image": A["image"],
        "ontology": {**A["ontology"], "ratification_record": "ae0/RATIFICACION_REGISTRO_v0_2.json"},
        "double_key": {"keys": [A_meta, B_meta],
                       "comparison": "ae0/comparacion/keymatch_v0_1.json",
                       "adjudication": {"proposal": {"file": PROPOSAL.relative_to(ROOT).as_posix(), "sha256": sha(PROPOSAL)},
                                        "second_key": {"file": DECISIONS.relative_to(ROOT).as_posix(), "sha256": sha(DECISIONS)},
                                        "third_review_rules": {"file": RULES.relative_to(ROOT).as_posix(), "sha256": sha(RULES)},
                                        "third_review_answer": "pendiente" if codex is None else "incorporada"}},
        "provenance": {"method": "doble llave de IA (DEC-024) con adjudicación por evidencia; ninguna persona ratificó píxeles",
                       "composer": {"file": "work/ae0_compose_reference.py", "sha256": sha(Path(__file__))},
                       "bbox_convention": A["provenance"]["bbox_convention"]},
        "objects": sorted(ref.values(), key=lambda o: o["id"]),
        "pending_third_review": pending,
        "retired_ids": retired,
        "adjudication_log": {"unspecified_attribute_defaults": defaults, "notes": log},
    }
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--codex", type=Path)
    args = parser.parse_args(argv)
    codex = json.loads(args.codex.read_text(encoding="utf-8")) if args.codex else None
    out = compose(codex)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    result = inv.validate(out, OUT.parent)
    print(json.dumps({k: result[k] for k in ("state", "reference_type", "tier_counts", "errors", "warnings")},
                     ensure_ascii=False, indent=1))
    print("objetos:", len(out["objects"]), "· pendientes:", [p["key_ref"] for p in out["pending_third_review"]],
          "· retirados:", [r["id"] + "/" + r["key"] for r in out["retired_ids"]],
          "· atributos por defecto:", len(out["adjudication_log"]["unspecified_attribute_defaults"]))


if __name__ == "__main__":
    main()
