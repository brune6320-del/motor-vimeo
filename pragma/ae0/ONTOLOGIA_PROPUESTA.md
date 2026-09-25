# A‑E0 · Ontología propuesta y contrato de evaluación

> **Estado:** `PROPUESTA — NO RATIFICADA`. Versión `0.1.0-propuesta` · 2026‑09‑25.
> **Modo GENESIS:** dirección técnica + diagnóstico. Cada punto trae una recomendación
> explícita; **la decisión es tuya**, porque el inventario es la verdad contra la que se va a
> juzgar todo lo demás y la firma quien lo ratifica.
>
> Responde a P0‑3 del backlog y a las 13 preguntas abiertas de `PROJECT_STATE.md` §22.
> Mientras no se ratifique, cualquier medición A‑E1 es `INCONCLUSIVE` (invariante 14).

---

## 1. Las cuatro preguntas, aplicadas a PRAGMA

| Pregunta | Respuesta para esta fase |
|---|---|
| ¿Qué tiene que sentir quien lo use? | **Al primer contacto:** "agarré exactamente eso". **Tras cien exportaciones:** confianza en que el PNG nunca se lleva un trozo de otra persona. La segunda es la que el v4 rompió, y la que casi nadie mide. |
| ¿Dónde va a vivir? | Hoy: Colab con GPU y el Mac de la persona usuaria. Mañana: la extensión Chrome. La evaluación tiene que poder correr sin la extensión y sin servidor local (invariante 2). |
| ¿Quién lo mantiene y con qué? | Una persona, con Colab y traspasos entre IAs (Claude → Codex → ChatGPT → Claude Code). Por eso todo contrato vive en archivos con hash, no en la conversación. |
| ¿Qué hay aquí que no exista ya? | Una evaluación **anclada en las oclusiones**: el error se mide donde una instancia toca a la que tiene detrás, no en el IoU global. Ver §4. |

**Lentes que sostienen esta dirección:** *espacial* (el grafo de oclusión como estructura de la
escena), *lógico‑matemática* (normalizar la fuga por el área invadida, no por la propia) e
*interpersonal* (la pasada ciega antes de ver el borrador, §5). Si solo quedara la
lógico‑matemática, esto sería un benchmark impecable que no protege a nadie.

---

## 2. Qué cuenta como objeto: regla de tiers (propuesta)

La regla es explícita para que dos personas distintas lleguen al mismo tier sin discutir gustos.

| Tier | Regla | Cuenta para `PASS_PROPOSALS` |
|---|---|---|
| **A** | Instancia identificable por alguien sin contexto, con **oclusión `none`/`low`/`medium`** y **lado corto de caja ≥ 64 px**. **Toda persona es A**, siempre, con máscara GT obligatoria, aunque esté casi oculta. | Sí: IoU de máscara ≥ 0,70 y sin fusión (§4, DEC‑013‑Q) |
| **B** | Instancia identificable con oclusión `high`/`extreme` **o** lado corto entre 32 y 63 px. | Sí: ≥ 90 % con IoU de caja ≥ 0,50 |
| **C** | Subtipo obligatorio por `kind`: **C_PART** (`kind=part`, con `parent_id` = relación *part_of*), **C_STUFF** (`kind=stuff`: pared, suelo), **C_TEXT** (`kind=text`). | No: se reportan, no bloquean |
| **IGNORE** | Lado corto < 32 px (salvo `contact_critical`), sombras, reflejos, brillos. Siempre con `ignore_reason`. | No |

**v0.2 · cambios aceptados de ChatGPT (carta 001, R4):**

1. La oclusión es un **atributo categórico** estimado por una persona. Ya no es una fracción
   visible que finge conocer el objeto oculto: la regla usa el nivel, no un porcentaje.
2. El subtipo de C ya existía en el esquema como `kind`, y `parent_id` es la relación *part_of*
   que excluye los pares parte/entero de la fusión. Ahora queda nombrado explícitamente.
3. **Medida del mínimo:** lado corto de la caja semiabierta, en píxeles de la **imagen canónica**
   (4000 × 2248 tras aplicar EXIF, sin ningún redimensionado); el manifiesto registra esa resolución.
   **Excepción:** `contact_critical: true` para una instancia pequeña que forma parte de una frontera
   que se evalúa.

Además, las máscaras GT de A‑E0 son **modales (solo lo visible)**. Por eso el denominador de la
fusión, `|Gⱼ|`, mide "la fracción de la evidencia visible de la víctima que se absorbió".

**Por qué 32 px de mínimo.** Es lo que conserva la llave colgada (≈ 42 px), el objeto más pequeño
que una persona querría recortar en esta foto. **No** se eligió por la cuadrícula del
`SAM2AutomaticMaskGenerator` (32×32 puntos ≈ una muestra cada 125×70 px): atar la verdad a lo
que el modelo alcanza a ver volvería circular la medición.

**Privacidad.** El texto de las etiquetas con nombre se inventaría como `kind=text` y **nunca se
transcribe**. Esta foto y todo lo que derive de ella se quedan fuera del repositorio público.

---

## 3. Contrato `SceneObject` (schema `pragma.scene_inventory` 0.1.0)

Se respetan los nombres ya diseñados en `PROJECT_STATE.md` §13.2 y se añaden **extensiones
propuestas** (marcadas ➕). Validador: `python3 -m pragma_ae validate <inventario>`.

| Campo | Tipo | Significado |
|---|---|---|
| `id` | `ae0_NNN` | Estable; nunca se renumera tras congelar |
| `canonical_name` | texto (es) | Nombre descriptivo único ("cuadro foto extremo derecho") |
| `synonyms` | lista | Otras formas de nombrarlo (para `LabelResolver`) |
| ➕ `concept_en` | texto | Concepto corto en inglés para modelos de vocabulario abierto (`person`, `picture frame`) |
| ➕ `kind` | `instance` · `part` · `stuff` · `text` | Qué clase de región es |
| `tier` | `A` · `B` · `C` · `IGNORE` | §2 |
| `bbox` | `[x1, y1, x2, y2]` enteros | Píxeles a resolución completa, **semiabierta** |
| ➕ `bbox_source` | texto | `draft_visual_estimate`, `human`, `from_gt_mask`… |
| `occlusion`, `truncation` | `none` · `low` (<25 %) · `medium` (25–50 %) · `high` (50–90 %) · `extreme` (>90 %) · `unknown` | Qué fracción está oculta por otra cosa / por el borde de la foto |
| `parent_id` | id o `null` | Parte → entero. Persona/mano no es fusión (§4) |
| ➕ `occluded_by` | lista de ids | Quién tapa a quién: define las franjas de contacto (§4) |
| ➕ `gt_required` | bool | Si la GT de máscara es obligatoria para congelar |
| `gt_mask` | `{path, mask_sha256}` o `null` | PNG binario 4000×2248 (0/255) y hash de contenido |
| `ignore_reason` | texto o `null` | Obligatorio en `IGNORE` |
| ➕ `review` | lista | Campos que alguien aún debe verificar; debe quedar vacía para congelar |
| ➕ `notes` | texto | Libre |

**Estados del inventario:** `DRAFT_UNVERIFIED` → `HUMAN_REVIEWED` → `FROZEN`. El validador
deriva el estado A‑E0 (`A_E0_DRAFT`, `…_PENDING_RATIFICATION`, `…_PENDING_REVIEW_ITEMS`,
`…_PENDING_GT`, `…_READY_TO_FREEZE`, `A_E0_FROZEN`) y **solo `A_E0_FROZEN` permite evaluar**.
Congelar exige `frozen_by` (una firma humana) y guarda el hash canónico del contenido; cualquier
edición posterior vuelve el inventario `A_E0_INVALID`.

---

## 4. El puente que cambió el contrato · VFX (rotoscopia) → evaluación

**Problema en una frase, sin adjetivos:** el contrato §9 mide cada instancia por su IoU global.

**Estructura aislada:** *el error se concentra en el umbral entre dos cuerpos a distinta
profundidad* (tensión en el contacto, no en el volumen).

**Traducción.** En rotoscopia de VFX un plano no se recorta "entero": se descompone por capas
de profundidad, y cada matte se juzga en sus **bordes de contacto** con la capa que tiene
delante o detrás, porque ahí es donde se ve el error en la composición final. El área interior
casi nunca falla.

**Operación importada (no el adorno):**

1. El inventario registra `occluded_by`: el grafo de profundidad de la escena.
2. La fuga de la mejor propuesta de *i* sobre otra instancia *j* se normaliza por **el área de
   *j***, no por la de *i*: `fusion_leak(i→j) = |P*ᵢ ∩ Gⱼ| / |Gⱼ|`.
3. Para cada par en contacto por oclusión se mide la fuga dentro de la franja
   `dilatar(Gᵢ, 24 px) ∩ Gⱼ`: `contact_leak`.

**Falsación (¿cambió alguna decisión?).** Sí, con números. En una escena con las proporciones
reales del caso (chica = 15,6 % de la foto, área aceptada en v4; persona posterior visible ≈ 1,7 %),
una máscara que añade a la chica **el 58 % visible de la persona posterior** — el defecto auditado
en v4 — mantiene **IoU = 0,94** con la GT de la chica. El umbral §9 de 0,70 la **aprueba**. La
cláusula de fusión la **rechaza** (`tests/test_metrics.py::FusionLoophole::test_v4_like_contamination_passes_iou_but_not_fusion`).
Veredicto del puente: **válido**.

**Otro puente, también válido:** la *hoja de contactos* de la fotografía analógica → preflight de
coordenadas. Operación: juzgar cada toma a su tamaño, no la tira entera. Decisión que cambió:
3 coordenadas de A‑E(−1) movidas (ver `preflight/PREFLIGHT_A-E-menos-1_v1_0.md`).

**Un puente descartado (para que se vea la falsación):** *naturalista* → taxonomía linneana de
objetos (reino/familia/especie para muebles, recipientes…). Produjo nombres más bonitos para las
categorías y **ninguna** decisión de medición distinta. Era decoración; no entra.

### Decisiones propuestas (requieren ratificación)

- **DEC‑013‑P · Fusión medible.** "Ninguna máscara Tier A fusiona dos instancias Tier A" se
  operacionaliza como `fusion_leak ≥ 0,10` → fallo, excluyendo pares parte/entero.
  Implementado en `pragma_ae/metrics.py` como `gates.section9_operational`.
- **DEC‑014‑P · Franja de contacto.** `contact_leak ≥ 0,20` en una franja de 24 px → fallo.
  **Recomendación:** en la primera corrida A‑E1 **reportarlo sin bloquear** y calibrar el umbral
  con datos reales antes de convertirlo en gate (`gates.proposed_v1_1`). Un umbral sin calibrar
  que bloquea es otra forma de PASS falso, al revés.
- **DEC‑015‑P · Pasada ciega.** La lista humana se hace antes de mirar el borrador (§5).
- **DEC‑016‑P · Preflight por ID.** Ninguna configuración de coordenadas se confirma sin hoja de
  contactos a resolución nativa.
- **DEC‑017 · Entradas fuera del repo público.** Vigente desde v1.1 del state file.

---

## 5. Las 13 preguntas abiertas: recomendación para cada una

| # | Pregunta (§22) | Recomendación | Por qué | Si decides otra cosa |
|---:|---|---|---|---|
| 1 | ¿Solo enteros o también partes y `stuff`? | **Enteros cuentan (A/B); partes, `stuff` y texto se inventarían como C con `parent_id`, sin bloquear.** | La galería del producto trata con instancias; la jerarquía se conserva para después sin inflar el gate. | Si las partes bloquean, el número de GT se triplica y A‑E1 casi seguro "falla" por fraccionamiento que no importa aún. |
| 2 | ¿Área mínima? | **Lado corto de caja ≥ 32 px; Tier A ≥ 64 px.** | §2. | Bajar a 16 px mete ruido de JPEG y joyería en el recall. |
| 3 | ¿Texto, reflejos, sombras, casi ocultos? | **Texto = C (sin transcribir). Reflejos/sombras = IGNORE. Casi ocultos (>90 %) = B si se identifican; si no, IGNORE.** Personas: siempre A. | Los efectos ópticos no son objetos exportables. | — |
| 4 | ¿Basta una región sin nombre? | **Sí para `PASS_PROPOSALS`.** El nombre es otro gate (`PASS_LABELS`, A‑E2). | Ya decidido en DEC‑010; se mantiene. | — |
| 5 | ¿Jerarquía persona/cara/ropa? | **Sí, como `parent_id`, nunca fusionando.** La galería muestra la persona; las partes se despliegan. | Evita que "mano" y "persona" compitan como duplicados. | — |
| 6 | ¿Idioma? | **UI e inventario en español; `concept_en` en inglés para prompts.** | Los modelos de vocabulario abierto se entrenan mayormente en inglés; la persona trabaja en español. | — |
| 7 | ¿Todo offline/local o se permiten APIs y modelos gated? | **Colab/local primero; ningún modelo gated ni API hasta cerrar A‑E1.** | A‑E1 solo necesita SAM 2.1 Large, ya auditado. | Decidir ahora sobre SAM 3 no cambia nada de A‑E0/A‑E1. |
| 8 | ¿Licencia/acceso de SAM 3/3.1? | **Diferir a A‑E2.** | No se necesita antes. | — |
| 9 | ¿Presupuesto? | **Colab L4; sweep AMG de 4 configuraciones fijadas antes de mirar resultados; ≤ 60 propuestas en la galería de primer nivel.** | Una persona puede recorrer ~50 miniaturas con atención; más es ruido. | Si el sweep crece después de ver resultados, deja de ser prefijado (invariante 13). |
| 10 | ¿Exportar todos o el seleccionado? | **Producto: el seleccionado. "Exportar todos" solo como diagnóstico.** | Es el caso de uso original (una firma, una persona). | — |
| 11 | ¿Qué imágenes adicionales? | **Cuatro no bloqueantes:** (a) una **firma escaneada** — el caso que originó PRAGMA, como prueba de regresión; (b) un producto sobre fondo liso; (c) 3–5 personas sin oclusión fuerte; (d) una mesa con objetos pequeños sin personas. | Una sola foto no valida generalización (§2.6). La (a) impide que el proyecto olvide para qué nació. | — |
| 12 | ¿Se ratifican los umbrales §9? | **Sí, más DEC‑013‑P (fusión 0,10). DEC‑014‑P (contacto) solo como reporte en la primera corrida.** | §4. | Sin DEC‑013‑P, el contrato aprueba el defecto de v4. |
| 13 | ¿Recuperar la carpeta v4? | **Buscar en Descargas, Drive y Papelera `PRAGMA_Fase_A_v4_20260811T001154Z_6e6a9ae1`.** Si aparece, verificar los 15 payloads contra su manifiesto. | Es la única evidencia visual cruda del fallo. | Si no aparece, declarar pérdida definitiva en el state file. |

---

## 6. Coste real (no esconderlo)

| Etapa | Quién | Tiempo estimado |
|---|---|---|
| Ratificar esta propuesta | tú | 20–30 min |
| Pasada ciega + revisión del borrador de 52 objetos con la lámina | tú | 45–60 min |
| **GT de las 3 personas** (pincel/polígono a 4000 px; pelo y contacto chica↔posterior) | tú | **1,5–3 h** |
| GT de los otros 21 Tier A (para poder declarar `PASS_PROPOSALS`) | tú | 2–4 h |
| Congelar | tú (firma) | 5 min |

**Recomendación de orden (etapas):** 1) GT de las 3 personas + cajas del resto → congelar una
versión `stage1`; 2) correr A‑E1 y mirar `tier_a_box_screen_failures`: si algún Tier A no tiene
ninguna propuesta con IoU de caja ≥ 0,5, el proponente ya falló y no hace falta pagar las 21
máscaras restantes para saberlo; 3) solo si la etapa 1 no muestra fallos evidentes, completar las
máscaras para poder afirmar `PASS_PROPOSALS`. Una etapa 1 nunca puede dar PASS: su techo es
`INCONCLUSIVE_GT_INCOMPLETE`.

**Sobre máscaras GT asistidas por SAM:** ahorran horas, pero una GT hecha con el modelo que se
va a evaluar hace la medición circular justo en los bordes que importan. Si se usan, registrar
`bbox_source`/`notes` = `sam_assisted_corrected` y corregir a mano **siempre** las franjas de
contacto. Para las tres personas: recomendación, **a mano**.

---

## 7. Qué no tocar

- Los veredictos históricos: v4 = `INCONCLUSIVE`, Fase B = `BLOQUEADA`, SAM 2 = no rechazable.
- `pragma-extension.zip`, FastAPI, localhost, YOLO‑seg, BiRefNet: fuera de A‑E0/A‑E1.
- DEC‑005 (sin `argmax` como selector): el "mejor IoU" de `metrics.py` es un oráculo de
  evaluación frente a la GT, nunca un selector de producto.
- El cuaderno Codex v1.0: se conserva byte a byte; v1.1 es un artefacto aparte.

*¿Estoy diciendo que no funciona o que no me gusta?* §4 dice **no funciona**: el contrato actual
aprueba un defecto documentado, y hay un test que lo demuestra. §5 son recomendaciones: ahí
manda tu criterio.
