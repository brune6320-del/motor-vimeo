"""Propuesta de adjudicación de Claude para la comparación de llaves A‑E0 (después de keymatch v0.1).

    python3 work/ae0_adjudication_proposal.py

Escribe ``ae0/comparacion/propuesta_adjudicacion_claude.json``. Es una PROPUESTA: la segunda llave
(ChatGPT) la acepta u objeta punto por punto, con las mismas láminas de evidencia. Lo que siga en
disputa va a la tercera revisión (Codex), como manda el protocolo v2 rev. 1 §5.2.

Reglas que aplica la propuesta (declaradas, para que se puedan objetar):
- R-box: si las dos llaves nombran el mismo objeto, la caja de referencia es la que mejor ajusta la
  extensión visible en la lámina 1:1. Si cada una acierta en bordes distintos, se toma cada borde de
  la que lo ajusta.
- R-kind: la ropa y los accesorios llevados (gorra, collar, arete, mosquetón) son ``part`` de la
  persona (R3), igual en todas las personas.
- R-dup: dos objetos de una misma llave que son el mismo objeto físico → se excluye el duplicado.
- R-include: un objeto que está en una sola llave se incluye si la lámina muestra un objeto distinto;
  si no, va a tercera revisión.
- R-tier: el tier se recalcula con la caja y la oclusión adjudicadas (R1–R4).
- MATCH_REJECTED: un emparejamiento de keymatch v0.1 entre clases distintas (parte↔entero,
  entero↔stuff) se rechaza y cada objeto se empareja con su correspondiente. Es un veredicto nuevo,
  declarado después de ver los datos: corrige la adjudicación, no la regla v0.1.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = json.loads((ROOT / "ae0/llaves/llave_claude_A-E0.json").read_text(encoding="utf-8"))
B = json.loads((ROOT / "ae0/llaves/llave_chatgpt_A-E0.json").read_text(encoding="utf-8"))
AD = {o["id"]: o for o in A["objects"]}
BD = {o["id"]: o for o in B["objects"]}


def a(i): return f"ae0_{i:03d}"


def box(k, i): return (AD if k == "A" else BD)[a(i)]["bbox"]


P = []   # propuestas


def same(ai, bi, bbox, ev, basis, attrs=None, name=None, concept=None):
    P.append({"type": "SAME", "a_id": a(ai), "b_id": a(bi), "bbox": bbox, "evidence": ev, "basis": basis,
              "attributes": attrs or {}, "canonical_name": name, "concept_en": concept, "status": "PROPOSED"})


def only(side, i, verdict, ev, basis, same_as=None, bbox=None, attrs=None):
    P.append({"type": f"{side}_ONLY", "id": a(i), "verdict": verdict, "same_as": same_as, "bbox": bbox,
              "evidence": ev, "basis": basis, "attributes": attrs or {}, "status": "PROPOSED"})


def rejected(ai, bi, basis):
    P.append({"type": "MATCH_REJECTED", "a_id": a(ai), "b_id": a(bi), "basis": basis, "status": "PROPOSED"})


def third(qid, question, involves, ev, claude_view):
    P.append({"type": "THIRD_REVIEW", "id": qid, "question": question, "involves": involves, "evidence": ev,
              "claude_view": claude_view, "status": "PROPOSED_FOR_CODEX"})


# Emparejamientos de keymatch v0.1 que se rechazan
rejected(55, 1, "chaqueta (parte) emparejada con la persona izquierda (entero): el entero se roba por IoU; la persona es C:001↔G:001 y la chaqueta C:055↔G:045")
rejected(4, 39, "mesa (instancia) emparejada con el suelo (stuff): no son el mismo objeto")

# Personas
same(1, 1, [220, 265, 1200, 2248], ["E1", "E2"],
     "brazos y codos desde x≈220 y manos desde y≈265; las piernas, en pantalón oscuro, siguen hasta el borde inferior pero no se distinguen del fondo: la caja llega a 2248 y la máscara marcará las piernas como incertidumbre",
     {"occlusion": "low", "truncation": "low", "occluded_by": []})
same(2, 2, "BOX_AUTO_MEAN", ["E5", "E6"], "IoU 0,89: media automática", {"occlusion": "none"})
same(3, 3, [2200, 305, 2815, 1195], ["E5", "E6"], "los bordes del hombro y del moño difieren poco: media de bordes",
     {"truncation": "none", "occlusion": "high", "occluded_by": [a(2)]})

# Muebles y superficies
same(6, 4, [0, 1010, 545, 2200], ["E1", "E2"],
     "el tablero con la plancha empieza en y≈1010 (G); el encaje visible termina en x≈545 y en y≈2200 (C)",
     {"occlusion": "medium", "truncation": "medium", "occluded_by": [a(1)]}, name="mesa izquierda con mantel de encaje")
only("B", 40, "INCLUDE", ["E2"], "el mantel de encaje es una parte válida (C) de la mesa izquierda", bbox=[0, 1265, 545, 2200],
     attrs={"parent": "C:006"})
same(7, 23, box("A", 7), ["E4"], "el respaldo oscuro empieza en x≈3390; x 3200–3390 es el brazo de la persona del frente",
     {"truncation": "medium"}, name="silla o sillón oscuro de la derecha", concept="chair")
same(8, 19, box("A", 8), ["E2"], "el asiento tapizado visible ocupa x 1090–1275; el resto de la caja G es mantel",
     {"occlusion": "medium", "tier": "A"}, name="asiento tapizado junto a la mesa central (silla o banqueta)", concept="chair")
only("A", 9, "INCLUDE", ["E4"], "bolso negro con asas visibles delante del mueble oscuro; la llave G lo absorbe en el «sofá»")
same(53, 6, box("A", 53), ["E1"],
     "la puerta es la franja negra de bordes rectos x 1145–1405; x 760–1145 es pared en sombra con el cuadro C:019",
     {"occlusion": "low", "truncation": "medium", "tier": "A"}, name="puerta oscura entre la persona izquierda y la pared clara")

# Pared
for ai, bi, extra in ((10, 27, {}), (12, 26, {}), (13, 28, {}), (14, 29, {}), (17, 32, {}),
                      (15, 30, {"occlusion": "none", "occluded_by": [], "tier": "A"}),
                      (16, 31, {"occluded_by": [a(2)]}),
                      (11, 25, {"tier": "B"}), (18, 33, {"tier": "B"})):
    same(ai, bi, box("A", ai), ["E5", "E3"] if ai == 18 else ["E5"],
         "las cajas C ajustan el marco u objeto en la lámina 1:1; las G son más holgadas o están desplazadas", extra)
only("A", 19, "INCLUDE", ["E1"], "cuadro con paspartú claro, claramente visible; la llave G lo incluye dentro de su «puerta»")
only("A", 20, "INCLUDE", ["E1"], "panel oscuro rectangular con reflejo vertical en el borde: objeto distinto")
only("A", 52, "INCLUDE", ["E1"], "stuff: pared en sombra (C, no bloquea)")
only("B", 39, "INCLUDE", ["E2"], "stuff: suelo oscuro (C, no bloquea)")
same(51, 38, "BOX_AUTO_MEAN", ["E5"], "IoU 0,89: media automática (stuff)")

# Objetos de las mesas
for ai, bi, extra, nm, cc in ((23, 5, {}, None, None), (28, 10, {}, None, None), (30, 12, {}, None, None),
                              (32, 13, {}, None, None), (34, 14, {}, None, None), (36, 18, {}, None, None),
                              (37, 17, {}, None, None),
                              (26, 9, {}, "objeto negro sobre la superficie posterior (probable bolso)", "bag"),
                              (29, 11, {"occlusion": "low", "tier": "A"}, "vaso o recipiente translúcido posterior", "cup"),
                              (31, 37, {"occlusion": "medium"}, "botella translúcida junto al brazo de la persona del frente", "bottle"),
                              (35, 16, {}, "papel arrugado o flor blanca", "tissue")):
    same(ai, bi, box("A", ai), ["E3", "E8"] if ai in (26, 29) else (["E2"] if ai == 23 else ["E3"]),
         "la caja C ajusta el objeto en la lámina; la G lo incluye con margen o desplazada", extra, nm, cc)
same(33, 15, [1913, 1367, 2169, 1615], ["E3"], "la bolsa transparente sigue hasta y≈1615 (debajo de la etiqueta)",
     {"occlusion": "medium"})
only("A", 24, "INCLUDE", ["E1"], "caja o estuche oscuro con un logo claro, visible detrás de la plancha")
only("A", 38, "INCLUDE", ["E3"], "tapa blanca pequeña junto al envoltorio (tier B)")
same(39, 21, [3175, 1745, 3315, 1940], ["E7"], "vasito izquierdo con palito: la caja incluye su borde superior (antes C:041)")
same(40, 22, [3285, 1690, 3455, 1950], ["E7"], "vasito derecho con palito: la caja incluye su borde superior (antes C:042)")
only("A", 41, "EXCLUDE", ["E7"], "R-dup: es la parte alta del vasito C:039, no otro vasito (error de Claude)", same_as="C:039")
only("A", 42, "EXCLUDE", ["E7"], "R-dup: es la parte alta del vasito C:040, no otro vasito (error de Claude)", same_as="C:040")

# Partes, accesorios y texto
same(43, 48, box("A", 43), ["E1"], "gorra bajo las manos", {"occlusion": "medium"})
same(44, 47, box("A", 44), ["E1"], "la caja C ajusta la etiqueta (sin transcribir)")
same(45, 55, box("A", 45), ["E6"], "la caja C ajusta el texto (sin transcribir)")
same(46, 35, box("A", 46), ["E6"], "el collar baja hasta y≈1150 (C); la caja G incluye la barbilla. R-kind: parte", {"kind": "part", "tier": "C"})
same(47, 36, box("A", 47), ["E6"], "el aro blanco está en x≈2680–2705; la caja G cae sobre el hombro de la persona posterior. R-kind: parte", {"kind": "part", "tier": "C"})
same(48, 51, box("A", 48), ["E5", "E6"], "la mano en V empieza en x≈2730; x > 3350 es la manga")
same(49, 56, [2636, 305, 2795, 560], ["E5"], "el moño ocupa x 2636–2795; x 2440–2600 de la caja G es el cuadro C:015")
same(55, 45, [230, 420, 1195, 1660], ["E1", "E2"], "la chaqueta incluye las mangas de los brazos levantados (hasta los codos, x≈230 y x≈1195) y baja hasta y≈1660")
same(56, 53, "MEAN", ["E6"], "camiseta de rayas: cajas parecidas (IoU 0,78); media de bordes")
same(57, 54, "MEAN", ["E6"], "overol: cajas parecidas (IoU 0,78); media de bordes")
same(58, 57, box("A", 58), ["E6"], "el estampado floral visible ocupa x 2250–2560, y 690–1040")
same(59, 52, box("A", 59), ["E2"], "la mano izquierda con el teléfono termina en y≈2180")
same(50, 34, box("A", 50), ["E2"], "teléfono: visible casi entero, los dedos tapan el borde → oclusión media, tier A; possibly_anchored registrado",
     {"occlusion": "medium", "tier": "A", "possibly_anchored": True})
only("A", 54, "INCLUDE", ["E2"], "mosquetón o llavero metálico en el cinturón (parte)")
for bi, why in ((43, "rostro de la persona izquierda"), (44, "mano de la persona izquierda"), (46, "camiseta oscura de la persona izquierda"),
                (49, "rostro de la persona del frente"), (50, "cabello de la persona del frente")):
    only("B", bi, "INCLUDE", ["E1", "E5", "E6"], f"{why}: parte válida (C, no bloquea), con la caja de la llave G")
only("B", 41, "INCLUDE_PENDING_Q1", ["E3"], "mantel de la mesa central: parte válida; su entero depende de Q1")
only("B", 42, "INCLUDE_PENDING_Q1", ["E4"], "mantel de la mesa derecha: parte válida; su entero depende de Q1")

# Tercera revisión (Codex)
third("Q1", "¿La tela blanca con rosas a la izquierda de la persona del frente (x≈1250–2120) y la de su derecha (x≈3100–3700) cubren la MISMA mesa o dos mesas distintas?",
      ["C:004", "G:007", "G:020"], ["E3", "E4", "E2"],
      "una sola mesa redonda que la persona del frente tapa por el centro (mismo mantel)")
third("Q2", "¿Qué es el objeto con tela floral gris en x≈1415–1830, y≈1230–1490, y el rectángulo claro con borde oscuro en x≈1610–1795, y≈1031–1212: una silla (asiento y respaldo), o una superficie tapizada con un marco encima?",
      ["C:005", "C:027", "G:008", "G:007"], ["E8", "E3"],
      "superficie o mueble tapizado posterior con un marco de mesa encima; el respaldo de una silla ocuparía todo el ancho del asiento")
third("Q3", "El mueble oscuro de la derecha (x≈3390–4000, y≈1175–2248): ¿silla o sofá? La zona clara en x≈3710–3950, y≈1300–1550: ¿cojín, o la pared vista a través de un hueco del respaldo?",
      ["C:007", "G:023", "G:024"], ["E4"],
      "silla o sillón con un hueco en el respaldo: la zona clara tiene la textura de la pared")
third("Q4", "En la zona oscura del borde izquierdo: ¿son objetos distinguibles el rectángulo oscuro x 0–164, y 0–536, los brillos de vidrio x 0–60, y 519–744, y la forma redondeada x 0–112, y 1021–1349?",
      ["C:021", "C:022", "C:025"], ["E1"],
      "C:021 sí (borde vertical nítido); C:022 y C:025 dudosos")


def main():
    h = lambda p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
    counts = {}
    for p in P:
        counts[p["type"]] = counts.get(p["type"], 0) + 1
    covered_a = {p["a_id"] for p in P if p["type"] == "SAME"} | {p["id"] for p in P if p["type"] == "A_ONLY"}
    covered_b = {p["b_id"] for p in P if p["type"] == "SAME"} | {p["id"] for p in P if p["type"] == "B_ONLY"}
    for q in (p for p in P if p["type"] == "THIRD_REVIEW"):
        for ref in q["involves"]:
            (covered_a if ref.startswith("C:") else covered_b).add("ae0_" + ref[2:])
    missing_a = sorted(set(AD) - covered_a)
    missing_b = sorted(set(BD) - covered_b)
    out = {"schema": "pragma.ae0_adjudication_proposal", "schema_version": "0.1.0", "author": "claude",
           "status": "PROPOSED: la segunda llave acepta u objeta cada punto; lo que siga en disputa va a Codex",
           "key_a": {"auditor": "claude", "sha256": h("ae0/llaves/llave_claude_A-E0.json")},
           "key_b": {"auditor": "chatgpt", "sha256": h("ae0/llaves/llave_chatgpt_A-E0.json")},
           "keymatch_v0_1": "ae0/comparacion/keymatch_v0_1.json",
           "rules": __doc__.split("Reglas que aplica la propuesta", 1)[1].strip(),
           "counts": counts, "uncovered": {"a": missing_a, "b": missing_b},
           "proposals": P}
    path = ROOT / "ae0/comparacion/propuesta_adjudicacion_claude.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(counts, "sin cubrir:", missing_a, missing_b)


if __name__ == "__main__":
    main()
