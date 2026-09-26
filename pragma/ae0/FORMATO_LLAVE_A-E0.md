# A‑E0 · Formato de una llave de inventario y regla de comparación

> Fijado **antes de que exista ninguna llave** (carta 010). Vale igual para la llave de Claude y para
> la de ChatGPT. La regla de comparación (`pragma_ae/keymatch.py`) queda congelada por hash en el
> mismo commit que este documento.

## 1. Qué es una llave

Un inventario completo de `P1070614.JPG` hecho por **un** auditor, solo desde la foto, con la
ontología v0.2 ratificada (`RATIFICACION_ONTOLOGIA_v0_2.md`). Es un JSON con el esquema
`pragma.scene_inventory` 0.1.0 (el mismo del kit) más un bloque `key`.

```json
{
  "schema": "pragma.scene_inventory",
  "schema_version": "0.1.0",
  "status": "DRAFT_UNVERIFIED",
  "image": {"sha256": "8f6e3b6f5013265a45c7e89121e3f0a18e3386951e2e75378b28da6d02ec529d",
            "width": 4000, "height": 2248},
  "ontology": {"version": "0.2", "ratified": true, "ratified_by": "persona usuaria",
               "document": "RATIFICACION_ONTOLOGIA_v0_2.md",
               "min_short_side_px": 32, "tier_a_min_short_side_px": 64},
  "key": {
    "auditor": "chatgpt",
    "blind_statement": "no abrí scene_inventory.draft.json, su lámina ni la llave de Claude",
    "image_sha256": "8f6e3b6f5013265a45c7e89121e3f0a18e3386951e2e75378b28da6d02ec529d",
    "ontology": "v0.2 ratificada por la persona usuaria",
    "created": "2026-09-26"
  },
  "objects": [ … ]
}
```

## 2. Cada objeto

| Campo | Regla |
|---|---|
| `id` | `ae0_NNN`, numeración **propia** de la llave (no tiene que coincidir con la otra) |
| `canonical_name` | nombre descriptivo en español, único en la llave. **Nunca** transcribe el texto de una etiqueta con nombre (R5): «etiqueta con nombre de la persona del frente», no lo que dice |
| `synonyms` | lista, puede ir vacía |
| `concept_en` | concepto corto en inglés (`person`, `picture frame`, `hand`…); las personas llevan exactamente `person` |
| `kind` | `instance` · `part` · `stuff` · `text` |
| `tier` | `A` · `B` · `C` · `IGNORE`, por R1–R4: toda persona es A; `part`, `stuff` y `text` son C; A exige lado corto ≥ 64 px y oclusión ≤ `medium`; B, oclusión `high`/`extreme` o lado corto 32–63 px; IGNORE, < 32 px (salvo `contact_critical`), sombras, reflejos y brillos, siempre con `ignore_reason` |
| `bbox` | `[x1, y1, x2, y2]` enteros, **semiabierta**, a resolución completa 4000 × 2248 (EXIF aplicado, sin redimensionar) |
| `bbox_source` | `ai_visual_estimate` (u otra forma de obtenerla, declarada) |
| `occlusion`, `truncation` | `none` · `low` · `medium` · `high` · `extreme` · `unknown` |
| `parent_id` | el entero del que es parte (`part` → su `instance`), o `null` |
| `occluded_by` | ids de **esta misma llave** que lo tapan |
| `gt_required` | `true` para las personas |
| `gt_mask` | `null` (las máscaras vienen después, en otro paso) |
| `ignore_reason` | obligatorio en `IGNORE`; `null` en el resto |
| `review` | `[]`: la llave se entrega sin dudas abiertas; una duda real va a `notes` |
| `notes` | libre |

**Antes de entregar:** `python3 work/validate_ae0_key.py <llave.json>` debe dar `valid_key: true`.
Se entrega el JSON y su `file_sha256`.

## 3. Custodia (orden)

1. La persona usuaria ratifica la ontología.
2. Claude revisa su borrador, lo congela como llave y **compromete en git solo su SHA‑256**.
3. Con ese hash a la vista (carta 011), ChatGPT hace su llave solo desde la foto y la entrega con su
   SHA‑256.
4. Claude publica su llave y compara las dos con la regla del §4.
   - Ninguna llave se ajusta después de ver la otra.
   - Las correcciones van a la adjudicación, con registro.

## 4. Regla de comparación (`pragma_ae/keymatch.py`)

1. **Emparejamiento:**
   - son candidatos los pares con IoU de caja ≥ **0,5**;
   - se emparejan de forma voraz por IoU descendente, con empates por (id A, id B);
   - es uno a uno y determinista.
2. **Pares emparejados:**
   - con IoU ≥ **0,85**, la caja de referencia es la media redondeada de las dos; si no, se adjudica
     la caja;
   - se listan los desacuerdos de `kind`, `tier`, `occlusion` y `truncation`, y de `parent_id` y
     `occluded_by` traducidos por el emparejamiento.
3. **Sin pareja** (`A_ONLY_OBJECT` / `B_ONLY_OBJECT`):
   - se adjudica como `INCLUDE`, `EXCLUDE` (con motivo) o `SAME_AS:<id>`;
   - como pista van el mejor candidato y la contención. Una contención ≥ 0,9 sugiere un entero en
     una llave y sus partes en la otra.
4. **Una persona sin pareja** es prioridad alta.
5. **`GEOMETRIC_MATCH != SEMANTIC_ACCEPTANCE`** (ChatGPT 010). Un `BOX_AUTO_MEAN` resuelve solo la
   caja. Cualquier desacuerdo de `kind`, `tier`, `occlusion`, `truncation`, `parent_id` u
   `occluded_by` sigue necesitando resolución según el protocolo.
6. **Registro de anclaje:** si la llave de ChatGPT incluye el objeto sostenido en la mano de la persona
   del frente, se marca `possibly_anchored`. Es la contaminación menor declarada en la carta 010.

Después vienen las máscaras de las tres personas: cada llave traza sus polígonos por su cuenta y se
comparan con `keydiff` (DEC‑025).
