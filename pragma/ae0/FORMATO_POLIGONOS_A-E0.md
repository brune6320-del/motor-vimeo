# A‑E0 · Máscaras de las tres personas: formato de polígonos y custodia

> Propuesto en la carta 013, antes de que exista ningún polígono. Vale igual para Claude y para
> ChatGPT. Derivación `AI_POLYGON_RASTER` con refinamiento `NUMPY_MINIMAL` (DEC‑024; ChatGPT 006 y
> 007). SAM 2 no interviene: es lo que A‑E1 va a medir.

## 1. Qué se entrega

Un JSON por llave. Cada persona del inventario adjudicado (`ae0/scene_inventory.json`) es un conjunto
de **anillos** con vértices a resolución completa:

```json
{
  "schema": "pragma.ae0_polygons",
  "key": {
    "auditor": "chatgpt",
    "blind_statement": "no abrí los polígonos de Claude",
    "image_sha256": "8f6e3b6f5013265a45c7e89121e3f0a18e3386951e2e75378b28da6d02ec529d",
    "derivation": "AI_POLYGON_RASTER",
    "created": "2026-09-27"
  },
  "persons": {
    "ae0_001": {"rings": [[[x, y], [x, y], "…"]], "uncertain_rings": [], "notes": ""},
    "ae0_002": {"rings": ["…"], "uncertain_rings": ["…"], "notes": ""},
    "ae0_003": {"rings": ["…"], "uncertain_rings": [], "notes": ""}
  }
}
```

- **Modal:** solo lo visible. Lo que tapa otra persona o un objeto no se traza.
- **Anillos:** cada anillo tiene al menos 3 vértices `[x, y]`, en coordenadas de la foto.
  - Se rellenan por la regla **par‑impar**: un anillo dentro de otro es un agujero, por ejemplo el
    hueco entre el brazo y el torso.
  - Un píxel cuenta si **su centro** cae dentro (`pragma_ae/polygon.py`).
- **Partes separadas:** si una persona aparece en trozos que no se tocan (la persona posterior, por
  ejemplo), cada trozo es un anillo más.
- **`uncertain_rings`:** zonas donde tú mismo no puedes justificar el borde, como el pelo fino o las
  piernas oscuras contra el fondo oscuro de la persona izquierda.
  - No sustituyen al trazo: el anillo principal decide igual qué es primer plano.
  - La zona incierta se añade a `uncertain`, no se borra.
- **Precisión:** trabaja a resolución completa o con zooms. La comparación tolera 2 px de diferencia
  de trazo (DEC‑025, `t` = 2). Más que eso es una discrepancia que se adjudica.
- **Validación:** `python3 work/validate_ae0_polygons.py <poligonos.json>` comprueba:
  - las tres personas exactas;
  - anillos válidos y máscaras no vacías;
  - **vértices crudos** de `rings` y de `uncertain_rings`: finitos y dentro de la foto,
    `0 ≤ x ≤ 4000` y `0 ≤ y ≤ 2248`. Si no, `rasterize` recortaría en silencio lo que sale de la
    imagen (parche de ChatGPT 013);
  - que ni la máscara ni la **zona incierta** se salgan de la caja adjudicada de su persona
    (±40 px). Sin esto, una zona incierta enorme neutralizaría parte del benchmark, porque DEC‑025 la
    excluye de las métricas (ChatGPT 013).
  - **No** exige `uncertain ⊆ mask`, porque una banda incierta legítima cruza la frontera. Tampoco
    pone un máximo de área incierta: DEC‑025 ya reporta `uncertain_area_px` y `uncertain_fraction`.
  - Imprime el SHA‑256 que se compromete.

## 2. Custodia (el mismo orden que las llaves de inventario)

1. Se congela el inventario adjudicado, con la respuesta de Codex ya incorporada.
2. Claude traza sus polígonos y compromete en git **solo su SHA‑256**.
3. Con ese hash a la vista, ChatGPT traza los suyos solo desde la foto y los entrega con su SHA‑256.
4. Claude publica los suyos. Ningún polígono se ajusta después de ver el otro.

## 3. Después: comparación y referencia (DEC‑025)

1. Por persona: `keydiff.compare_keys(A, B)`, con `A_ONLY`/`B_ONLY`, `THICK`/`ISLAND`/`thin`,
   `OPEN`/`ENCLOSED` y la lámina `diff_sheet`.
2. Se adjudica cada componente que lo exige: toda `ISLAND` y todo `THICK` ≥ 100 px.
3. Se compone la referencia con `compose_reference` (`MIDLINE` declarada). Su zona incierta es la de
   `keydiff` más la unión de los `uncertain_rings` de las dos llaves.
4. **Omisión compartida:**
   - teselas de contorno 1:1 (`contour_tiles`, 512 px con 64 de solape);
   - las recorren Claude y ChatGPT;
   - Codex revisa a ciegas las teselas de desafío: pelo, contacto entre personas, manos, objetos
     sostenidos y zonas inciertas.
5. Se registran `gt_mask` con `derivation = AI_POLYGON_RASTER`, se congela como
   `AI_CONSENSUS_REFERENCE` y, en el mismo commit, se congela el contrato A‑E1.
