# PRAGMA · State file — de selección por clic a inventario exhaustivo de escena

> Documento de traspaso para Claude o Codex. Sustituye cualquier conclusión anterior que
> trate el resultado v4 como una validación suficiente del producto.
>
> Última actualización: 10 de agosto de 2026, Lima
> (ejecución auditada: `20260811T001154Z_6e6a9ae1`, hora UTC).
>
> Traspaso a Codex completado: el diagnóstico A‑E(−1) fue integrado en
> `PRAGMA_A-E-menos-1_diagnostico_caso_chica_Codex.ipynb`. Véase
> `PRAGMA-ESTADO-TRASPASO-CLAUDE-A-CODEX.md`. Esto no cambia el veredicto
> `INCONCLUSIVE` ni desbloquea Fase B.

---

## 1. Resumen ejecutivo

La Fase A v4 demostró que **SAM 2.1 Large funciona técnicamente en Colab/L4**, recibe
un punto, genera tres candidatas y exporta PNG RGBA, alpha, capturas, tiempos y hashes.
También mostró que elegir por contenido es imprescindible: en ambos sujetos la máscara
aceptada fue la candidata `1`, aunque el score predicho favorecía otras máscaras parciales.

Sin embargo, el directorio exportado termina en `_PASS` y el JSON declara `PASS` porque
el checklist manual se rellenó con `True`. **Las evidencias visuales contradicen ese PASS**:

- el señor queda aislado de forma gruesa, pero presenta agujeros y bordes erosionados;
- la chica conserva partes claras de la tercera persona situada detrás y pierde zonas de
  cabello, cabeza, hombro, brazo y mano;
- solo se probó la modalidad `point`; no se probaron `point+corrections` ni `box`.

El veredicto defendible de la ejecución es por tanto:

```text
FASE A v4: INCONCLUSIVE
Fase B: BLOQUEADA
SAM 2: todavía NO rechazable
```

Además, el objetivo del proyecto cambió. Ya no basta con separar dos personas conocidas.
El nuevo objetivo expresado por el usuario es:

> **Descubrir, reconocer, segmentar y hacer seleccionable cada objeto visible posible de
> la fotografía, para poder conservar o eliminar cualquier instancia individual.**

Esto no es un ajuste menor del test anterior. Abre una subfase distinta, denominada en
este documento **Fase A-E · Inventario exhaustivo de escena**. No se debe tocar todavía
la extensión, FastAPI, YOLO-seg, BiRefNet ni la Fase B.

---

## 2. Evidencia congelada

### Imagen de aceptación

- Ruta local: `/Users/usuario/Desktop/P1070614.JPG`
- Dimensiones: `4000 × 2248`
- SHA-256: `8f6e3b6f5013265a45c7e89121e3f0a18e3386951e2e75378b28da6d02ec529d`
- Contenido relevante: señor a la izquierda, chica al frente y una tercera persona
  parcialmente oculta detrás de ella, además de cuadros, mesa, muebles, botellas,
  recipientes y otros objetos pequeños.

### Ejecución exportada

- Carpeta: `/Users/usuario/Desktop/PRAGMA_Fase_A_v4_20260811T001154Z_6e6a9ae1_PASS/`
- No renombrar ni borrar: el sufijo `_PASS` forma parte de la evidencia histórica, aunque
  el veredicto corregido sea `INCONCLUSIVE`.
- Archivos: `16`
- Tamaño total: `74,390,186` bytes
- Reporte: `reporte_fase_a_v4.json`
- SHA-256 del reporte: `5e575d34d2a599dd99f891b599525ce172567e7c5c3588ed31011479838ca185`
- Manifiesto: `manifest.json`
- SHA-256 del manifiesto: `64233e31c4593f10c388970884ff5bb7604ef71ffad1386b6fc6ee36f2d7b233`
- Se verificaron de nuevo los bytes y SHA-256 de los 15 payloads del manifiesto: todos
  coinciden.

### Notebook disponible después de la ejecución

- Ruta: `/Users/usuario/Documents/Codex/2026-08-10/referenced-chatgpt-conversation-this-is-an/outputs/PRAGMA_Fase_A_SAM2_v4_ligero.ipynb`
- SHA-256 actual: `757e9722aa98a4d9420fdca4f287ef36fe78d7b09e2b9e12b3be6896e76e814a`
- Nota: esta copia incluye correcciones posteriores de importación, advertencia de Pillow
  y fallback para Brave. El reporte no guardó el hash del notebook ejecutado, por lo que
  no debe afirmarse que esta copia sea byte por byte la que produjo el ZIP.

---

## 3. Qué se ejecutó realmente

### Modelo y entorno

- Modelo: `sam2.1_hiera_large`
- Parámetros declarados: `224.4 M`
- Checkpoint: `898,083,611` bytes
- SHA-256 checkpoint: `2647878d5dfa5098f2f8649825738a9345572bae2d4350a2468587ece47dd318`
- Commit SAM 2: `2b90b9f5ceec907a1c18123530e92e794ad901a4`
- GPU: NVIDIA L4
- Precisión: `bfloat16`
- Pico de GPU: `1.262 GiB`
- Carga del modelo: `3.293 s`
- Embedding compartido de la imagen: `0.945 s`
- Inferencia por prompt aceptado: `0.033 s` aproximadamente
- Composición y exportación por sujeto: `18.9–19.7 s`

### Intentos aceptados formalmente

| Sujeto | Modalidad | Punto | Candidata | Scores de las 3 candidatas | Área aceptada |
|---|---|---:|---:|---|---:|
| Señor izquierda | `point` | `(755.47, 1005.14)` | `1` | `0.969 / 0.185 / 0.277` | `12.12%` |
| Chica frente | `point` | `(2588.47, 1785.38)` | `1` | `0.906 / 0.002 / 0.006` | `15.56%` |

La candidata de mayor score no era la persona completa. Esto confirma que **no se puede
usar `argmax` como selector automático de la salida deseada**.

### Inspection tokens

- Señor: `50c86479da326a9254c809570e14353070b28c594c3aa4f696c3505d3db9df10`
- Chica: `283c4de04ea1c17597f376ebaadab9d4a9e3074d38dcc875a4a764a75dced63e`

---

## 4. Auditoría visual y corrección del veredicto

### Señor de la izquierda · candidata 1

Lo que sí funciona:

- identifica al sujeto correcto;
- excluye a la chica, cuadros y muebles como componentes grandes;
- conserva aproximadamente brazos, manos, torso y la parte de pantalón visible.

Defectos verificables en `acceptance_binary_alpha.png` y la captura sobre damero:

- agujeros transparentes dentro de cara/cabeza;
- pequeños agujeros en torso y pantalón;
- borde inferior y derecho del pantalón dentado y erosionado;
- no es un acabado limpio listo para afirmar `body_and_edges_complete=True`.

Resultado honesto: **aislamiento grueso, necesita refinamiento**.

### Chica del frente · candidata 1

El caso bloqueante no pasa:

- la máscara incorpora claramente parte de la tercera persona posterior, incluido el
  torso floral y masa de cabeza/cabello detrás de la chica;
- existen pérdidas y fragmentación severa en cabello, cabeza, hombro, brazo y mano;
- hay contaminación rugosa alrededor del cabello y el costado derecho;
- las candidatas 0 y 2 son fragmentos y tampoco resuelven el sujeto completo.

Esto contradice al menos estos valores guardados como `True` en el checklist:

- `body_and_edges_complete`;
- `other_people_excluded`;
- `background_and_frames_excluded`.

Resultado honesto de la modalidad punto: **FAIL para este intento**, pero no FAIL de SAM 2
como método porque faltan correcciones y caja.

### Alpha

- La salida de aceptación es binaria (`0/255`), no matting.
- La vista por logits del señor suaviza bordes pero no repone pérdidas.
- En la chica, la vista por logits genera una neblina semitransparente extensa: `12.40%`
  de banda suave según la captura y `25.38%` de alpha intermedia U8 según el reporte.
- La vista por logits es solo diagnóstico; no debe convertirse en gate ni llamarse
  refinamiento de pelo.

### Inconsistencia interna del reporte

- `overall` dice `PASS` y `phase_b_blocked` dice `false`;
- `modalities_tried` registra solamente `point`;
- `modalities_missing` registra `box` y `point+corrections` para ambos sujetos;
- `modality_reviews.*.point` conserva `proposal_id=None`, `result=None` e índices vacíos;
- el PASS procede del checklist manual, no de una verificación automática de contenido.

Conclusión corregida: **`INCONCLUSIVE`; Fase B bloqueada**.

---

## 5. El nuevo objetivo necesita una definición operativa

“Cada objeto posible” no es medible sin decidir granularidad. Una persona también puede
dividirse en cara, pelo, manos, chaqueta, camiseta y etiqueta; una mesa puede dividirse en
mesa, mantel y todos sus objetos; un cuadro puede ser marco e imagen. Ningún modelo puede
demostrar exhaustividad frente a un universo que no ha sido enumerado.

Antes de ejecutar otro modelo, congelar una ontología humana para esta foto:

- **Tier A — obligatorio:** instancias completas y seleccionables que una persona
  identificaría como objetos principales; incluye las tres personas por separado, muebles,
  mesa, cuadros/marcos y objetos claramente visibles sobre las superficies.
- **Tier B — difícil:** objetos pequeños, parcialmente ocultos o truncados.
- **Tier C — opcional/diagnóstico:** partes de objetos, regiones `stuff` (pared, suelo),
  texto, sombras, reflejos y detalle interno.

El umbral de tamaño y la inclusión de Tier C deben ratificarse con el usuario. Mientras la
lista humana esté incompleta, el único estado válido es `INCONCLUSIVE`.

También deben separarse dos capacidades:

1. **Segmentar todo:** producir regiones/máscaras, aunque todavía no tengan nombre.
2. **Reconocer todo:** asignar nombres y separar instancias de conceptos conocidos o
   descubiertos.

Una máscara correcta sin nombre es un éxito del segmentador y un pendiente del etiquetador;
un nombre correcto con máscara mala es el caso inverso.

---

## 6. Arquitectura objetivo de Fase A-E

```text
Imagen verificada por hash
  → SceneInventory / ground truth humano
  ├─ ClassAgnosticProposer
  └─ ConceptSegmenter
  → ProposalRegistry inmutable
  → OverlapContainmentGraph
  → LabelResolver
  → GallerySelector por ID estable
  → InteractiveRefiner
  → AlphaRefiner (más adelante)
  → Compositor + evidencias + manifiesto
```

Contratos mínimos:

- `SceneObject`: ID, nombre canónico, sinónimos, tier, bbox, máscara GT opcional,
  oclusión/truncamiento, parent ID e `ignore_reason`.
- `Proposal`: ID estable, máscara/RLE, bbox, área, score, fuente/modelo, prompt,
  parámetros, tiempo, hash y relaciones parent/child.
- `ClassAgnosticProposer`: imagen → propuestas geométricas sin etiquetas.
- `ConceptSegmenter`: imagen + concepto/lista oracle → cajas, máscaras, etiquetas y scores.
- `LabelResolver`: conserva `unlabeled`, sinónimos y múltiples etiquetas; no inventa una
  certeza única.
- `OverlapContainmentGraph`: registra duplicados, solapamientos y parte/entero sin borrar
  propuestas originales.
- `Selector`: consume propuestas/detecciones; nunca llama directamente al modelo global.
- `InteractiveRefiner`: puntos/caja sobre una propuesta ya elegida.
- `AlphaRefiner`: matte suave posterior; BiRefNet pertenece aquí, no a descubrimiento.

---

## 7. Modelos candidatos y límites

### Baseline primero: SAM 2 Automatic Mask Generator

La implementación oficial `SAM2AutomaticMaskGenerator` genera máscaras de toda la imagen
mediante una cuadrícula de puntos y filtra por IoU predicho, estabilidad y NMS. Devuelve
máscara/RLE, bbox, área, score, punto y crop. Es el siguiente experimento más limpio porque
reutiliza el SAM 2.1 Large ya instalado y contesta primero la pregunta geométrica.

Fuente oficial: [Meta SAM 2 · automatic_mask_generator.py](https://github.com/facebookresearch/sam2/blob/main/sam2/automatic_mask_generator.py)

Límite: produce partes, enteros, duplicados y solapamientos; no asigna nombres y no garantiza
que cada máscara corresponda a “un objeto” según nuestra ontología.

### Reconocimiento abierto: comparar después, uno por vez

- **SAM 3/3.1:** puede segmentar exhaustivamente todas las instancias de **un concepto
  abierto especificado** mediante frase corta o ejemplar. No descubre por sí solo la lista
  completa de conceptos presentes. Requiere auditoría separada de checkpoint, acceso,
  licencia, peso, GPU y privacidad antes de elegirlo.
  Fuente oficial: [Meta SAM 3](https://github.com/facebookresearch/sam3)
- **Grounding DINO → SAM 2:** texto → cajas/labels → máscaras SAM 2. Mantiene detector y
  segmentador intercambiables. Probar primero con vocabulario humano oracle; no confundir un
  concepto omitido con un fallo de la máscara.
  Fuente oficial: [IDEA Research · Grounding DINO](https://github.com/IDEA-Research/GroundingDINO)
- **YOLO-seg:** útil como baseline rápido de vocabulario cerrado y para objetos de sus clases,
  pero un checkpoint preentrenado sobre COCO no puede demostrar “cada objeto posible”. No
  integrarlo todavía como solución principal.
  Fuente oficial: [Ultralytics · Instance Segmentation](https://docs.ultralytics.com/tasks/segment)
- **BiRefNet:** conservar únicamente como punto de extensión de borde/matting después de
  que descubrimiento, separación y selección hayan pasado. No introducirlo en A-E0/A-E1.

Para SAM 3 no usar “señor de la izquierda” como concepto principal. Usar `person` para
obtener todas las personas y asignar `izquierda/frente/posterior` después mediante geometría
o revisión humana.

---

## 8. Orden obligatorio de la nueva validación

### A-E0 · Ground truth antes del modelo

1. Crear `scene_inventory.json` sobre la foto exacta.
2. Crear una lámina numerada con todos los objetos humanos del inventario.
3. Registrar ID, nombre, tier, bbox, oclusión, truncamiento y relaciones parte/entero.
4. Crear máscaras manuales GT al menos para todos los Tier A bloqueantes; las tres personas
   son obligatorias.
5. Congelar hash del inventario y de las anotaciones antes de evaluar modelos.

### A-E1 · SAM 2 AMG, sin reconocimiento

1. Probar un sweep pequeño y fijado de `points_per_side`, `pred_iou_thresh`,
   `stability_score_thresh` y `crop_n_layers`.
2. Usar RLE para no multiplicar memoria a 4000×2248.
3. Guardar todas las propuestas antes de deduplicar.
4. Medir cobertura, duplicación, fraccionamiento, tiempo y memoria.
5. Si un Tier A no tiene ninguna propuesta, falla el proposer; no culpar al selector.

### A-E2 · Nombres con vocabulario oracle

1. Usar la lista humana completa como `OracleVocabularyProvider`.
2. Comparar solo una opción por ejecución: SAM 3 o Grounding DINO→SAM 2.
3. Añadir conceptos negativos ausentes para medir falsos positivos.
4. No usar todavía un captioner/VLM para generar automáticamente el vocabulario; mezclaría
   descubrimiento de nombres con localización.

### A-E3 · Unión, jerarquía y selección

1. Reconciliar propuestas sin etiqueta y propuestas etiquetadas por IoU/containment.
2. Conservar propuestas `unlabeled`; pueden representar conceptos omitidos.
3. No fusionar destructivamente persona/cara o cuadro/marco.
4. Mostrar galería numerada por ID, máscara, box, label, score y procedencia.

### A-E4 · Refinamiento y exportación

1. Probar que cada Tier A puede seleccionarse por ID estable.
2. Refinar solo la propuesta elegida con puntos/caja SAM 2.
3. Exportar la máscara exacta registrada y verificar su hash.
4. Mantener borde/matting como métrica separada.

### A-E5 · Vocabulario automático, después

Solo después de pasar con vocabulario oracle, evaluar un `AutoVocabularyProvider` y medir
qué objetos/nombres omite o inventa. No aceptar el prompt `everything` como prueba de
exhaustividad.

---

## 9. Contrato PASS / FAIL propuesto

Los umbrales siguientes son propuesta explícita y deben ratificarse; no convertirlos en una
decisión silenciosa.

### Métricas separadas

- Cobertura de cajas: recall por best box-IoU ≥ `0.50`.
- Cobertura de máscaras: recall y best mask-IoU por objeto, reportado a `0.50` y `0.75`.
- Separación: ninguna máscara Tier A puede fusionar dos personas o dos instancias Tier A.
- Fraccionamiento: número mínimo de propuestas necesarias para reconstruir un objeto.
- Duplicación: propuestas que empatan con el mismo GT y carga final de galería.
- Reconocimiento: label recall, label precision y falsos positivos con prompts negativos.
- Selección: objeto direccionable por ID, acciones/tiempo y hash exportado.
- Borde: Boundary-F con tolerancia declarada, separado de recall de inventario.
- PRAGMA: peso, commit, licencia/acceso, descargas, backend, tiempos por etapa, pico
  RAM/VRAM, condición de fallo y fallback.

### Gates provisionales

- `PASS_PROPOSALS`: 100% de Tier A tiene al menos una máscara con IoU ≥ `0.70`; ≥90% de
  Tier B tiene box-IoU ≥ `0.50`; ninguna máscara Tier A fusiona dos personas.
- `PASS_LABELS`: 100% de Tier A reconocido con vocabulario oracle; precisión ≥ `0.95`
  incluyendo conceptos negativos.
- `PASS_SELECTION`: todos los Tier A seleccionables por ID y exportados con la máscara
  registrada; muestra prefijada de Tier B.
- `PASS_A_E`: pasan los tres gates anteriores y existen reporte, evidencias, tiempos,
  inventario y hashes.
- `INCONCLUSIVE`: ontología/GT incompleto, pesos/licencia no disponibles, OOM/entorno,
  vocabulario automático aún no validado o protocolos no agotados.
- `FAIL_COMPONENT`: solo después de agotar el sweep o protocolo prefijado de ese componente.

La Fase B permanece bloqueada salvo `PASS_A_E`.

---

## 10. Decisiones que el agente debe presentar, no asumir

1. ¿“Objeto” significa solo instancia entera o también partes y regiones `stuff`?
2. ¿Qué tamaño mínimo cuenta? ¿Cuentan texto, llave, reflejos, sombras y objetos casi
   totalmente ocultos?
3. ¿Se exige nombre automático o basta una región visual seleccionable?
4. ¿Se puede seleccionar a la vez persona completa, cara y ropa como jerarquía?
5. ¿La UI y el inventario serán en español, con prompts internos bilingües/canónicos?
6. ¿Todo debe correr offline/local o se permiten API/tokens/modelos gated?
7. ¿Se acepta la licencia y acceso de SAM 3/3.1?
8. ¿Cuál es el presupuesto máximo de GPU, RAM, tiempo y número de máscaras visibles?
9. ¿Se exportan PNG de todos los objetos o solo del objeto seleccionado?
10. ¿Esta fotografía es únicamente el caso bloqueante? Una sola imagen no valida
    generalización; antes de producto deben añadirse casos no bloqueantes por dificultad.

---

## 11. Invariantes del proyecto

- No modificar `pragma-extension.zip` durante Fase A-E.
- No construir FastAPI, localhost ni integración de extensión.
- No avanzar a Fase B por el `PASS` textual del reporte auditado.
- No reemplazar SAM 2 en silencio ni degradar de Large a Small.
- No usar `argmax` para decidir la máscara correcta.
- No llamar matting a la sigmoid de logits.
- Mantener módulos intercambiables:
  `detección/propuestas → selector → máscara → refinamiento → compositor`.
- Cada modelo debe registrar peso, dónde corre, tiempo, licencia/acceso y comportamiento al
  fallar.
- Toda afirmación de PASS debe estar ligada a una evidencia, propuesta, máscara e inventario
  congelados por hash.

---

## 12. Próxima tarea exacta para Codex

> Después de ejecutar y auditar A‑E(−1), no rehagas la extensión ni integres nuevos modelos.
> Crea primero **A-E0** como un
> cuaderno/artefacto de anotación sobre `P1070614.JPG`: inventario humano numerado,
> `scene_inventory.json`, bboxes y máscaras GT de las tres personas, con hashes y definición
> de tiers. Después crea **A-E1** usando únicamente el `SAM2AutomaticMaskGenerator` oficial
> sobre la misma foto y compara sus propuestas contra el inventario congelado. Entrega una
> galería addressable por ID, métricas de cobertura/duplicación/fraccionamiento, tiempos,
> VRAM y un veredicto `PASS_PROPOSALS / INCONCLUSIVE / FAIL_COMPONENT`. No añadas nombres
> automáticos, YOLO-seg, BiRefNet, FastAPI ni Fase B hasta terminar esa comparación.
