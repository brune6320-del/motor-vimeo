# PRAGMA · Fase A v3 → v4 · parche de crítica ejecutable

GENESIS · modo DIAGNÓSTICO + CONSTRUCCIÓN DE HERRAMIENTA
Fecha: 2026-08-10 · Sobre: `PRAGMA_Fase_A_SAM2_v3_autocontenido.ipynb`
SHA-256 auditado: `3d9b75a1944274a3d107d971c2cd6395dd49b0d835febf8cf5e04ed6870a4157`

**Declaración obligatoria (BLOQUE X):** de los tres hallazgos, el 1 y el 3 son
*"no funciona"* — afirmaciones falsables, con una línea de código que las
demuestra. El 2 es *"no funciona"* en sentido metodológico: el experimento
no puede sostener la conclusión que está autorizado a emitir. Ninguno es
*"no me gusta"*. No hay observaciones de gusto en este documento.

**Límite de esta crítica:** el sandbox de esta sesión no tiene GPU y su shell
cayó por disco. Todo lo verificado aquí es lectura de código y contraste
contra la fuente oficial (`sam2/sam2_image_predictor.py`, rama `main`).
Los parches requieren **una** ejecución de validación en Colab. Está indicada
al final y es barata.

---

## 1 · Qué funciona (con la misma precisión que el reproche)

No es cortesía. Estas piezas son mejores que el estándar del oficio y hay que
protegerlas del propio parche:

- **La política de precisión.** `select_precision(cuda, capability)` con
  asserts deterministas sobre (7,5)→fp16, (8,0)→bf16, CPU→fp32 es correcta y
  está probada sin hardware. Es la forma adulta de resolver el asunto BF16/T4.
- **La inmutabilidad del intento.** `latest_proposal[slug]` + `RuntimeError`
  si finalizas una propuesta que ya no es la última. Eso cierra el agujero por
  el que se cuela el 90% de los falsos PASS de un cuaderno interactivo.
- **El ZIP por lista blanca** con `expected_names` verificado contra
  `archive.namelist()`. Elimina el residuo entre sesiones, que es el error que
  nadie ve hasta que ya publicó.
- **`argmax` erradicado del camino ejecutable** y sustituido por una puerta
  explícita (`if SENOR_MASK_INDEX is None: PENDIENTE`). Correcto.
- **El refinamiento con `mask_input`** usa `proposal.logits[seed][None,:,:]`,
  que es exactamente la forma `1xHxW` que documenta la API oficial. Correcto.
- **La foto incrustada en Base64 con verificación SHA-256.** Resuelve el
  problema real de reproducibilidad en Colab. Es la mejor decisión del archivo.

---

## 2 · El problema raíz — UNO SOLO

> **Las 11 pruebas verifican que el cuaderno hace lo que el cuaderno dice.
> Ninguna verifica que el experimento pueda responder la pregunta para la que
> fue construido.**

Es un sistema de verificación **autorreferencial**. Impecable hacia dentro,
ciego hacia fuera. De ahí salen los tres síntomas siguientes, y los tres
desaparecen si se corrige el criterio de qué es una prueba válida:

| Test v3 | Qué prueba de verdad |
|---|---|
| `soft_alpha_preserved` → `alpha_values: [128]` | que `AlphaCompositor` sabe multiplicar. **No** que alguna vez reciba un 0.5. |
| `verdict_truth_table_and_evidence_gate` | que la tabla de verdad es consistente. **No** que sus entradas sean medibles. |
| `smoke_test → candidate_count: 3` | que el modelo cargó. **No** que segmentara algo. |

Los tres pasan. Los tres son verdaderos. Y los tres pueden coexistir con un
cuaderno que produce un veredicto en el que no deberías confiar.

---

## 3 · Los tres hallazgos, con su prueba

### HALLAZGO 1 · La alpha suave no existe en el camino real
**Severidad: alta. Demostrable en una línea.**

Cadena real en `finalize_candidate`:

```python
matte = pipeline.refiner.refine(image, proposal.masks[candidate_index].astype(np.float32))
```

`proposal.masks` viene de `predictor.predict(...)` con `return_logits=False`
(el defecto). En la fuente oficial:

```python
if not return_logits:
    masks = masks > self.mask_threshold      # mask_threshold = 0.0
```

→ `masks` es **booleano**. `.astype(np.float32)` da exactamente `{0.0, 1.0}`.
`IdentityRefiner` hace `np.clip` (no cambia nada). `AlphaCompositor` hace
`np.rint(matte*255)` → alpha ∈ `{0, 255}`.

**Todo PNG exportado por la v3 tiene alpha binaria con borde en escalera.**
El test `soft_alpha_preserved` pasa porque se le pasa un array sintético con
un 0.5 dentro; en producción ese 0.5 no se genera nunca.

El coste no es estético: el criterio humano nº 2 del checklist es
*"cuerpo y contornos completos"*, y la zona difícil declarada de la foto de
aceptación es *"contacto visual difícil entre pelo/hombro de la chica y la
tercera persona"*. Vas a juzgar pelo contra un borde de un solo bit.

**Falsador (BLOQUE III, paso 4).** Métrica objetiva, 3 líneas, sin ground truth:

```python
def soft_band_fraction(matte, lo=0.02, hi=0.98):
    """Fracción de píxeles con alpha intermedia. En la v3 es exactamente 0.0."""
    return float(((matte > lo) & (matte < hi)).sum()) / float(matte.size)
```

En v3 devuelve `0.0`. Si tras el parche devuelve `> 0`, el arreglo es real.
Si devuelve `0.0`, el parche no se aplicó. No admite interpretación.

**Honestidad sobre el alcance:** el borde suave que produce este parche es la
rampa bilineal del upsample de los logits 256×256 a 4000×2248 que ya hace
`postprocess_masks`. Es **estrictamente mejor que la escalera** y hace que el
contrato de alpha suave sea cierto, de modo que BiRefNet entre en Fase B sin
tocar el compositor. **No es matting de pelo.** El pelo sigue siendo Fase B.
Prometer otra cosa sería exactamente lo que el BLOQUE XIII prohíbe.

---

### HALLAZGO 2 · El experimento no puede atribuir su propio fracaso
**Severidad: la más cara de las tres.**

El §10 del estado dice: si hay FAIL, *"no se integra YOLO-seg, BiRefNet ni
FastAPI hasta decidir conscientemente si SAM 2 sigue siendo válido como
segmentador del pipeline"*. Es decir: **un FAIL aquí autoriza a matar SAM 2.**

Pero la única modalidad de prompt implementada es *un punto positivo*
(`ClickSelector` → `PromptSet(point, [1])`), más clics de corrección de uno en
uno. `propose_with_points` acepta negativos pero la interfaz nunca los produce.
Y `box=` no aparece en el cuaderno.

La API oficial lo soporta de primera clase, y además combina caja y puntos:

```python
def predict(self, point_coords=None, point_labels=None, box=None, ...)
# ...
if boxes is not None:
    box_labels = torch.tensor([[2, 3]], ...)
    concat_coords = torch.cat([box_coords, concat_points[0]], dim=1)   # caja + puntos
```

El punto suelto es la modalidad **más débil** de SAM para instancia completa —
por eso el propio modelo devuelve tres máscaras: está declarando que el prompt
es ambiguo. Con una persona parcialmente ocluida detrás de la chica, es
justamente donde va a sangrar.

**Conclusión estructural:** un FAIL de la v3 dice *"SAM 2 con un punto
positivo falla"* y se va a leer como *"SAM 2 falla"*. El diseño puede matar el
método correcto por la razón equivocada, y ese error cuesta semanas de Fase B.

**El puente que produjo el arreglo (BLOQUE III).**

- *Estructura aislada:* cómo se emite un juicio de identidad bajo evidencia parcial.
- *Traducción — inteligencia naturalista:* un taxónomo no determina una especie
  "mirando más". Registra **qué caracteres examinó**. Un espécimen determinado
  por un solo carácter no está determinado: está *provisionalmente* determinado,
  y esa categoría tiene nombre propio precisamente para que nadie la confunda
  con una determinación.
- *Operación importada (no el adorno):* el veredicto deja de ser
  `sujeto → PASS/FAIL` y pasa a ser `sujeto × modalidad → resultado`.
  FAIL solo es enunciable cuando el eje de modalidades está agotado.
- *Decisión concreta que pudo haber sido otra:* aparece un cuarto estado,
  `INCONCLUSIVE`, y `sam2_rejectable` deja de ser sinónimo de "no PASS".
- *Veredicto del puente:* **válido.** Cambió una regla, no una frase.

---

### HALLAZGO 3 · El smoke test no puede fallar por contenido
**Severidad: media. Peligro: alto, porque el §9 lo presenta como validación.**

```python
smoke_prompts = PromptSet([[720, 1050]], [1])
# ... assert candidate_count == 3
```

`multimask_output=True` devuelve **siempre** tres máscaras. El assert es
tautológico: se cumple si el punto cae en una cara, en una pared o fuera de
todo. El procedimiento §9 paso 4 pide confirmar `status: PASS` de este bloque
antes de seguir — es decir, pide confiar en una prueba que no puede fallar.

Es el mismo defecto que el §4 del estado le reprocha (con razón) al cuaderno
anterior: *"usa un `assert` final tautológico"*. Sobrevivió a la v3 en otra forma.

---

## 4 · Los tres cambios, ordenados por coste / impacto

### CAMBIO 1 · Alpha suave real — **< 1 hora**, aislado, alto impacto

**Reemplaza `SAM2MaskGenerator`:**

```python
class SAM2MaskGenerator:
    """v4: pide logits sin umbralizar. `alpha_gain` (k) es la nitidez de la
    rampa de alpha y es un parámetro de dirección, no un detalle: k pequeño
    da borde algodonoso, k grande devuelve la escalera. Se registra en el informe."""

    def __init__(self, predictor, alpha_gain: float = 3.0):
        self.predictor = predictor
        self.alpha_gain = float(alpha_gain)

    def prepare(self, image):
        synchronize(); start = time.perf_counter()
        with torch.inference_mode(), inference_precision():
            self.predictor.set_image(image)
        synchronize()
        return time.perf_counter() - start

    def generate(self, prompts, mask_input=None, multimask_output=True, box=None):
        synchronize(); start = time.perf_counter()
        with torch.inference_mode(), inference_precision():
            hr_logits, scores, low_res_logits = self.predictor.predict(
                point_coords=prompts.points if prompts is not None else None,
                point_labels=prompts.labels if prompts is not None else None,
                box=box,
                mask_input=mask_input,
                multimask_output=multimask_output,
                return_logits=True,          # <<< la corrección
            )
        synchronize()
        # float16: 3 x 4000 x 2248 x 2 B = 54 MiB por propuesta (float32 serían 108).
        hr_logits = np.asarray(hr_logits, dtype=np.float16)
        masks = np.asarray(hr_logits, dtype=np.float32) > 0.0   # mask_threshold oficial = 0.0
        return masks, hr_logits, scores, low_res_logits, time.perf_counter() - start
```

**Añade (celda del pipeline):**

```python
def matte_from_logits(hr_logits_c, gain):
    z = np.asarray(hr_logits_c, dtype=np.float32) * float(gain)
    return (1.0 / (1.0 + np.exp(-z))).astype(np.float32)

def soft_band_fraction(matte, lo=0.02, hi=0.98):
    return float(((matte > lo) & (matte < hi)).sum()) / float(matte.size)

ALPHA_GAIN = 3.0
```

**En `finalize_candidate`, sustituye la línea de la matte:**

```python
# v3:  matte = pipeline.refiner.refine(image, proposal.masks[candidate_index].astype(np.float32))
matte = pipeline.refiner.refine(
    image, matte_from_logits(proposal.hr_logits[candidate_index], ALPHA_GAIN)
)
SOFT_BAND = soft_band_fraction(matte)
assert SOFT_BAND > 0.0, "La alpha sigue siendo binaria: el parche no se aplicó."
```

**En `bbox_from_matte`, baja el umbral** (si no, el crop corta justo el borde
suave que acabas de ganar):

```python
def bbox_from_matte(matte, padding=20, threshold=0.05):   # v3: matte > 0.5
    ys, xs = np.where(matte > threshold)
```

`Proposal` gana el campo `hr_logits`. `register_proposal`, la galería y
`proposal_areas` siguen usando `proposal.masks` (booleano) sin cambios.

**Guarda `SOFT_BAND` y `ALPHA_GAIN` en `REPORT`.** Ese número es la prueba
de que la corrección existe, y es comparable entre ejecuciones.

---

### CAMBIO 2 · Eje de modalidad + estado `INCONCLUSIVE` — ~2 horas, impacto máximo

```python
REQUIRED_MODALITIES = {"point", "point+negatives", "box"}
MODALITIES_TRIED = {"senor_izquierda": set(), "chica_frente": set()}

def propose_with_box(subject, slug, box_xyxy, positive_points=None, negative_points=None):
    """Caja XYXY en píxeles de la imagen original. Se puede combinar con puntos:
    la API oficial concatena caja y puntos en un solo prompt."""
    box = np.asarray(box_xyxy, dtype=np.float32).reshape(4)
    pts = list(positive_points or []) + list(negative_points or [])
    lbl = [1]*len(positive_points or []) + [0]*len(negative_points or [])
    prompts = PromptSet(pts, lbl) if pts else None
    masks, hr_logits, scores, low_res, elapsed = pipeline.generator.generate(
        prompts, box=box, multimask_output=True
    )
    MODALITIES_TRIED[slug].add("box")
    # ...construye y registra la Proposal igual que propose_with_points...

def subject_status(slug, checklist, trials, modalities):
    values = [checklist[slug][k] for k in CRITERIA]
    invalid = [v for v in values if v not in (True, False, None)]
    if invalid: raise ValueError(f"Valores inválidos en {slug}: {invalid}")
    if any(v is False for v in values):
        if not checklist[slug]["notes"].strip():
            raise ValueError(f"{slug}: notes es obligatorio cuando hay FAIL.")
        if not REQUIRED_MODALITIES.issubset(modalities.get(slug, set())):
            faltan = sorted(REQUIRED_MODALITIES - modalities.get(slug, set()))
            checklist[slug]["notes"] += f" [modalidades sin probar: {faltan}]"
            return "INCONCLUSIVE"     # no autoriza rechazar SAM 2
        return "FAIL"
    if all(v is True for v in values):
        if slug not in trials:
            raise ValueError(f"{slug}: no puede pasar sin candidata y evidencias.")
        return "PASS"
    return "PENDING"

_ORDER = ["FAIL", "INCONCLUSIVE", "PENDING", "PASS"]
def overall_status(statuses):
    return min(statuses.values(), key=_ORDER.index)

assert overall_status({"a":"FAIL","b":"PENDING"})        == "FAIL"
assert overall_status({"a":"INCONCLUSIVE","b":"PASS"})   == "INCONCLUSIVE"
assert overall_status({"a":"PASS","b":"PENDING"})        == "PENDING"
assert overall_status({"a":"PASS","b":"PASS"})           == "PASS"
```

Y en `REPORT`, separa las dos preguntas que la v3 tenía fusionadas:

```python
"phase_b_blocked":  OVERALL_STATUS != "PASS",     # igual que antes
"sam2_rejectable":  OVERALL_STATUS == "FAIL",     # NUEVO: solo un FAIL real autoriza
                                                  # reconsiderar SAM 2 en el pipeline
"modalities_tried": {k: sorted(v) for k, v in MODALITIES_TRIED.items()},
```

Esta es la línea que impide que una tarde de clics mate el método correcto.

---

### CAMBIO 3 · Smoke test con dientes — ~30 min

```python
def _iou(a, b):
    inter = np.logical_and(a, b).sum(); union = np.logical_or(a, b).sum()
    return float(inter) / float(union) if union else 0.0

areas = [float(m.mean()) for m in smoke_masks]
pares = [_iou(smoke_masks[i], smoke_masks[j]) for i, j in ((0,1), (0,2), (1,2))]

checks = {
    "tres_candidatas":      len(smoke_masks) == 3,
    "no_vacia":             min(areas) > 1e-4,     # el punto tocó algo
    "no_engulle_el_cuadro": max(areas) < 0.60,     # no devolvió media foto
    "candidatas_distintas": min(pares) < 0.98,     # el decoder no es degenerado
    "dtype_esperado":       PRECISION["dtype"] in ("float16", "bfloat16"),
}
SMOKE_TEST = {
    "status": "PASS" if all(checks.values()) else "FAIL",
    "checks": checks, "areas": areas, "pairwise_iou": pares,
    "candidate_count": len(smoke_masks),
    "dtype": PRECISION["dtype"], "point": smoke_prompts.points.tolist(),
}
assert SMOKE_TEST["status"] == "PASS", SMOKE_TEST
```

Ahora el bloque puede fallar. Un test que no puede fallar no es un test:
es una decoración con sintaxis de assert.

---

## 5 · Qué NO tocar

El punto que casi nadie escribe y que el BLOQUE XIII exige. Toda crítica pone
en peligro lo que ya estaba bien:

1. **`select_precision` y su matriz de asserts.** Está resuelto. No lo
   reescribas "de paso".
2. **`latest_proposal` + el `RuntimeError` de propuesta caduca.** Es la única
   defensa contra el falso PASS por confusión de rondas. Si tocas
   `register_proposal` para meter `hr_logits`, no muevas esa comprobación.
3. **El ZIP por lista blanca y `expected_names`.** No lo cambies por
   `make_archive` "para simplificar". Añade los nuevos ficheros a la lista.
4. **La foto en Base64 con verificación SHA-256.** Es la mejor decisión del
   cuaderno. No la sustituyas por una descarga.
5. **La prohibición de `argmax`.** El CAMBIO 3 introduce comparaciones entre
   candidatas para el *smoke test* de sanidad. No las conviertas en selección
   automática para el veredicto. Siguen siendo tres, sigue eligiendo un humano.
6. **`torch.inference_mode()` en `prepare`/`generate`.** Es redundante
   (`set_image` y `_predict` ya llevan `@torch.no_grad()`), pero es inofensivo
   y explícito. Quitarlo no gana nada y arriesga un despiste.

---

## 6 · Validación exigida antes de dar el parche por bueno

Una sola pasada en Colab, y estos cinco números:

| # | Qué | Criterio |
|---|---|---|
| 1 | `SMOKE_TEST.status` | `PASS`, con los 5 `checks` en `True` |
| 2 | `soft_band_fraction(matte)` de la v3 | `== 0.0` — confirma el hallazgo 1 |
| 3 | `soft_band_fraction(matte)` de la v4 | `> 0.0` — confirma el arreglo |
| 4 | Recorte a 400% sobre pelo/hombro, v3 vs v4 | escalera visible → rampa |
| 5 | `modalities_tried` tras la sesión | las 3, si el veredicto va a ser FAIL |

Si el 3 sale `0.0`, el parche no está aplicado y nada más de este documento
cuenta. Empieza por ahí.

---

## 7 · Las tres inteligencias que sostienen esta dirección

Regla de las tres (BLOQUE III). Si solo pudiera nombrar una, la dirección
estaría ilustrada, no terminada:

- **Lógico-matemática** — el álgebra del veredicto: precedencia de estados,
  y una métrica escalar (`soft_band_fraction`) que sustituye una opinión
  por un número falsable.
- **Naturalista** — la taxonomía de la determinación: registrar qué caracteres
  se examinaron antes de nombrar la especie. De ahí sale `INCONCLUSIVE`,
  que es el aporte real de este parche.
- **Intrapersonal** — la honestidad del operador: la única defensa contra
  confundir *"SAM 2 no puede"* con *"me cansé de hacer clic"*. El eje de
  modalidad convierte esa honestidad en una comprobación automática, que es
  la única forma en que la honestidad sobrevive a un viernes por la tarde.

---

## 8 · Lo que este parche NO arregla (y hay que decirlo)

- **El pelo.** El borde suave es rampa de upsample, no matting. Fase B.
- **N = 1 foto, 2 sujetos.** Toda la evidencia sobre la que se va a decidir el
  segmentador de PRAGMA es una imagen. Un PASS aquí no predice el tráfico real
  de la extensión y un FAIL aquí condena un método con una muestra.
  Recomendación explícita: mantener esta foto como caso **bloqueante** y añadir
  4 más incrustadas, elegidas por eje de dificultad nombrado (pelo fino sobre
  fondo cargado · dos personas superpuestas · bajo contraste sujeto/fondo ·
  borde con desenfoque de movimiento), registradas como **no bloqueantes**.
  Coste: una hora. Es lo que hará comparable la Fase B.
- **La ausencia de ground truth.** Cinco booleanos por sujeto no son
  reproducibles entre personas ni entre meses, y no dejan un número que
  BiRefNet pueda intentar batir. Una sola alpha pintada a mano para **un**
  sujeto convierte todo esto en IoU + IoU de frontera. Veinte minutos,
  reutilizable para siempre. No es urgente hoy; es lo primero que echarás de
  menos en Fase B.

---

## Fuentes primarias consultadas para esta crítica

- `SAM2ImagePredictor.predict` / `_predict` / `_prep_prompts` — rama `main`:
  https://github.com/facebookresearch/sam2/blob/main/sam2/sam2_image_predictor.py
  (verificado: `mask_threshold=0.0`; `if not return_logits: masks = masks > self.mask_threshold`;
  firma `predict(..., box=None, ..., return_logits=False)`; concatenación caja+puntos en `_predict`)
- Repositorio oficial SAM 2: https://github.com/facebookresearch/sam2
