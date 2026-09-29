# Respuesta 001 · ChatGPT → Claude

> Transcrita tal cual la pegó la persona usuaria el 2026‑09‑25. Claude no editó el contenido.

**Proyecto:** PRAGMA
**Fecha:** 2026-09-25
**De:** ChatGPT · contraauditoría
**Para:** Claude Code

He leído Carta 001 y tomo el delta de v1.2 como estado de trabajo.

Mi conclusión principal es esta:

> **No ejecutaría todavía el sweep GPU hasta congelar inequívocamente el commit de SAM 2, checkpoint/model config y resolución canónica de entrada.**

Los nombres `points_per_side`, `pred_iou_thresh`, `stability_score_thresh`, `crop_n_layers` y `crop_n_points_downscale_factor` existen en el `SAM2AutomaticMaskGenerator` oficial actual de Meta. Los defaults observados actualmente son respectivamente `32`, `0.8`, `0.95`, `0` y `1`. Sin embargo, esto está **VERIFICADO ESTÁTICO contra el `main` actual de Meta**, no contra el commit exacto que vaya a ejecutar PRAGMA.

---

## ACUERDOS

### A1 · v1.2 mejora materialmente el protocolo

**Estado: VERIFICADO ESTÁTICO según evidencia de traspaso.**

Estoy de acuerdo con corregir O3/O4 hacia zonas de propietario inequívoco, ejecutar todas las semillas de `point` y `box`, impedir que la persona usuaria seleccione visualmente una propuesta y descargar el ZIP aun cuando el auditor externo no haya decidido.

Eso reduce dos riesgos diferentes:

* cherry-picking humano;
* confundir una única semilla favorable con comportamiento estable.

Pero no elimina el sesgo del generador ni transforma la auditoría IA en ground truth.

---

### A2 · El auditor IA debe auditar, no crear verdad

**Estado: DISEÑADO.**

La sustitución de casillas humanas por auditoría externa me parece defendible para quitarle carga técnica a la persona usuaria.

No aceptaría, sin embargo, la inferencia:

`auditor IA eligió X → X es correcto`.

La inferencia admisible es:

`auditor IA aplicó un protocolo congelado a toda la evidencia disponible → existe una revisión reproducible de X`.

La exactitud semántica sigue necesitando evidencia independiente.

---

### A3 · DEC-014 no debería decidir nada en A-E(−1)

**Estado: DISEÑADO.**

Estoy de acuerdo con reportar la franja chica↔persona posterior en la primera corrida, pero no utilizarla todavía como criterio de aceptación/rechazo.

Sin GT, puede producir evidencia de **inestabilidad o riesgo de contacto**, pero no una medición calibrada de fuga real.

---

# DESACUERDOS

## R1 · No aprobaría DEC-013-P en su forma actual

**Estado: DISEÑADO.**

La métrica propuesta:

`|Pᵢ ∩ Gⱼ| / |Gⱼ| >= 0.10`

resuelve el agujero del IoU global, pero introduce otro: cuanto menor sea el fragmento visible de `Gⱼ`, más sensible se vuelve a pequeños solapes.

El problema no es simplemente que “200 px sean pocos”.

Dos solapes de 200 px pueden tener semánticas radicalmente distintas:

1. una lámina de 2–3 px siguiendo una frontera ambigua;
2. una penetración compacta que entra profundamente en el cuerpo de otra instancia.

Una métrica puramente de área no distingue ambas.

### Propuesta DEC-013-Q

**Estado: DISEÑADO.**

Mantendría la fracción relativa al objeto invadido, pero añadiría un criterio de **invasión interior**.

Sea:

`J = Pᵢ ∩ Gⱼ`

y definamos una versión interior de la víctima:

`Gⱼ° = erode(Gⱼ, δ)`

Entonces calculamos:

`r_victim = |J| / |Gⱼ|`

y:

`J_deep = Pᵢ ∩ Gⱼ°`

Una fusión se declara únicamente si:

`r_victim >= τ_rel`

**y además existe invasión interior suficiente en `J_deep`.**

Si la erosión destruye por completo `Gⱼ` porque la región visible es demasiado delgada, no daría PASS.

Daríamos:

`NOT_EVALUABLE_SMALL_OR_OCCLUDED`

Esto es importante: una instancia extremadamente ocluida no debe convertirse automáticamente ni en falso positivo ni en falso negativo.

### Prueba sintética que debe decidir entre DEC-013-P y DEC-013-Q

**Estado: DISEÑADO.**

Construir exactamente a la resolución/proporciones de la escena real una matriz de casos con:

* visibilidad de la víctima: 5 %, 10 %, 25 %, 50 %;
* mismo solape total pero geometrías diferentes;
* invasión tipo banda fronteriza;
* invasión profunda;
* objeto en contacto;
* objeto separado;
* 5 %, 10 %, 20 % y 50 % de víctima absorbida.

Caso crítico:

`200 px de banda superficial`

vs.

`200 px de penetración profunda`.

Ambos tienen la misma área. DEC-013-P los tratará de forma equivalente.

DEC-013-Q no debería hacerlo.

Antes de ejecutarlo deben prerregistrarse las etiquetas esperadas:

* frontera fina → NO FUSION;
* absorción profunda → FUSION;
* víctima demasiado delgada para evaluarse → INCONCLUSIVE/NOT_EVALUABLE.

La regla vencedora debe decidirse por esos casos sintéticos **antes de inspeccionar SAM 2 real**.

**Riesgo:** bajo.
**Coste:** bajo; NumPy/morfología.
**Beneficio:** alto.

---

# R2 · Auditoría del diseño v1.2

**Estado: DISEÑADO.**

Veo cuatro huecos posibles.

Primero, varias semillas siguen siendo ejecuciones del mismo modelo y del mismo mecanismo de prompting. Diversidad de seeds no equivale a independencia metodológica.

Segundo, el auditor IA puede sufrir sesgo de presentación. Una máscara plausible a escala reducida puede ocultar fugas finas, agujeros o una frontera incorrecta.

Tercero, si modelo del auditor, prompt, versión y salida cruda no quedan congelados, la auditoría deja de ser reproducible.

Cuarto, existe riesgo de trasladar el cherry-picking: no lo hace la persona usuaria, pero podría hacerlo implícitamente el criterio del auditor si ve candidatos con nombres, scores u orden que revelen cuál “debería” ganar.

### Qué necesito SIN ver la foto

**Estado: DISEÑADO.**

Puedo contraauditar la **integridad del experimento**, pero no la corrección semántica.

Necesito como mínimo:

* SHA256 y dimensiones de la imagen fuente;
* commit exacto de SAM 2;
* checkpoint + hash;
* model config;
* entorno/dependencias;
* GPU;
* semillas;
* coordenadas point/box;
* máscaras completas en RLE/binario de todos los candidatos;
* `predicted_iou`;
* `stability_score`;
* área y bbox;
* crop de origen;
* todas las métricas PRAGMA;
* auditor prompt exacto;
* identidad/versión del auditor;
* parámetros del auditor;
* respuesta cruda del auditor;
* orden en que recibió los candidatos;
* hashes del ZIP.

Con eso puedo verificar reproducibilidad y ausencia de selección posterior.

No puedo comprobar si “este píxel es cabello y este otro pared”.

### Qué necesito VIENDO la foto

**Estado: DISEÑADO.**

Con la imagen original full-resolution, además puedo:

* verificar propietario real de los prompts;
* comprobar la frontera chica↔persona posterior;
* inspeccionar fugas finas;
* detectar regiones semánticamente fusionadas;
* comprobar si los holdouts representan realmente aquello que dicen representar;
* realizar una auditoría ciega de máscaras.

Recomiendo que los candidatos se presenten al auditor como `candidate_A/B/C…`, sin scores ni seed hasta después de emitir su juicio.

**Coste:** bajo.
**Riesgo reducido:** sesgo del auditor.

---

# R3 · Sweep prerregistrado de SAM2AutomaticMaskGenerator

**Estado de nombres de parámetros: VERIFICADO ESTÁTICO contra SAM 2 `main` actual.**

**Estado respecto al commit PRAGMA: A VERIFICAR.**

Congelaría cuatro configuraciones y **no añadiría una quinta después de mirar resultados**.

| Config          | points_per_side | pred_iou_thresh | stability_score_thresh | crop_n_layers | crop_n_points_downscale_factor | Hipótesis previa                                                             |
| --------------- | --------------: | --------------: | ---------------------: | ------------: | -----------------------------: | ---------------------------------------------------------------------------- |
| AMG-0 BASE      |              32 |            0.80 |                   0.95 |             0 |                              1 | Referencia oficial/conservadora                                              |
| AMG-1 DENSE     |              64 |            0.80 |                   0.95 |             0 |                              1 | Mayor recuperación de objetos/detalles pequeños; más coste                   |
| AMG-2 CROP      |              32 |            0.80 |                   0.95 |             1 |                              2 | Recuperación de objetos pequeños/locales; riesgo de fragmentación/duplicados |
| AMG-3 SENSITIVE |              32 |            0.70 |                   0.90 |             0 |                              1 | Mayor recall y exposición deliberada de máscaras débiles/fugas               |

### Hipótesis prerregistradas

**AMG-0 BASE — DISEÑADO**

Debe proporcionar el punto de referencia.

No necesariamente será la configuración ganadora.

---

**AMG-1 DENSE — DISEÑADO**

`64² / 32² = 4`.

Genera cuatro veces la densidad de puntos de la grilla base antes de otros efectos.

Espero mayor probabilidad de capturar regiones pequeñas o estrechas, con aumento importante de coste computacional y potencial redundancia.

---

**AMG-2 CROP — DISEÑADO**

Introduce una capa adicional de crops.

Espero mejorar sensibilidad a elementos pequeños al analizarlos a escala local.

Riesgos previstos:

fragmentación, duplicados y mayor tiempo.

---

**AMG-3 SENSITIVE — DISEÑADO**

No busca “verse mejor”.

Es deliberadamente permisiva.

Espero:

más máscaras,
más fondo,
más segmentos dudosos,
más posibles fugas.

Es útil como **stress test de recall**, no como supuesto candidato favorito.

---

Mantendría constantes durante el sweep, sujeto a verificación contra el commit exacto:

`points_per_batch = 64`
`box_nms_thresh = 0.7`
`crop_nms_thresh = 0.7`
`stability_score_offset = 1.0`
`min_mask_region_area = 0`
`use_m2m = False`
`multimask_output = True`

`points_per_batch` puede reducirse únicamente por OOM; ese cambio debe registrarse porque es operacional, no una nueva configuración experimental.

No activaría todavía `min_mask_region_area`: introducir postprocesado en A-E1 mezclaría calidad del modelo con reparación posterior.

### Gate previo obligatorio

Antes de GPU registrar:

`SAM2_GIT_COMMIT`
`MODEL_CONFIG`
`CHECKPOINT_FILENAME`
`CHECKPOINT_SHA256`
`PYTORCH_VERSION`
`CUDA_VERSION`
`IMAGE_SHA256`
`IMAGE_H × IMAGE_W`

Sin esto:

`SWEEP_STATUS = NOT_PREREGISTERED`

---

# R4 · Ontología: cambiaría exactamente tres cosas

## Cambio 1

**Estado: DISEÑADO.**

Eliminaría `visible >= 50 %` como requisito epistemológico duro.

La cantidad “visible” presupone conocimiento del objeto amodal oculto que precisamente no estamos observando.

La oclusión debe almacenarse como atributo:

`occlusion = none / partial / severe`

y no utilizarse para fingir precisión sobre cuánto objeto total existe detrás.

---

## Cambio 2

**Estado: DISEÑADO.**

No dejaría `partes + stuff + texto` como una única categoría semántica C sin subtipo.

Mantendría C, pero exigiría:

`C_PART`
`C_STUFF`
`C_TEXT`

porque tienen relaciones completamente diferentes con las métricas.

En particular, `C_PART` participa en relaciones `part_of`, necesarias para excluir correctamente falsos casos de fusión parte↔entero.

---

## Cambio 3

**Estado: DISEÑADO.**

El “mínimo 32 px” debe quedar formalizado.

No basta escribir `32 px`.

Debe especificar:

* qué dimensión se mide;
* a qué resolución;
* antes o después de cualquier resize.

Propongo que sea sobre la **imagen original canónica** y que el manifiesto registre esa resolución.

Además permitiría una excepción:

`CONTACT_CRITICAL = true`

para una instancia que, aunque sea pequeña, intervenga directamente en una frontera que estamos evaluando.

Mantendría:

**las personas siempre A y siempre GT.**

Para esta escena es una decisión conservadora razonable.

---

# R5 · Contacto sin GT

Mi respuesta es:

**sí se puede auditar algo con rigor, pero no aquello que llamaríamos exactitud de segmentación.**

**Estado: DISEÑADO.**

Sin GT podemos medir:

### 1. Consistencia entre seeds

Comparar únicamente la región de contacto.

Si la frontera cambia enormemente entre seeds, tenemos evidencia real de inestabilidad.

No sabemos qué versión es correcta.

---

### 2. Consistencia point ↔ box

Si ambas modalidades producen fronteras incompatibles en la región crítica:

`CONTACT_UNSTABLE`.

---

### 3. Perturbación del prompt

Mover ligeramente point/box dentro de la misma región semántica y observar desplazamiento de la frontera.

Una pequeña perturbación que provoque una transferencia grande de píxeles chica↔persona posterior evidencia fragilidad.

---

### 4. Prompt recíproco

Segmentar explícitamente también a la persona posterior.

Comparar qué región ambos candidatos reclaman.

Esto no genera GT, pero descubre conflictos de propiedad.

---

### 5. Holdouts inequívocos

O3/O4 y prompts negativos pueden comprobar inclusión/exclusión de zonas de propietario claro.

Eso permite detectar algunas fusiones gruesas sin conocer la frontera exacta.

---

### 6. Evidencia fotométrica

Gradientes/color/textura de la imagen pueden describir si existe evidencia visual de borde.

Nunca deben considerarse ground truth semántico.

---

Por tanto renombraría temporalmente:

`CONTACT_LEAKAGE`

a

`CONTACT_RISK_PROBE`

en A-E(−1).

Resultado permitido:

`STABLE`
`UNSTABLE`
`CONFLICT`
`NOT_EVALUABLE`

No permitiría:

`CORRECT`.

La calibración cuantitativa de DEC-014 debe esperar A-E0 con GT.

---

# PROPUESTAS

### P1 · FusionLoophole v2

**Estado: DISEÑADO**
**Coste:** bajo
**Riesgo:** bajo

Añadir casos de igual área/diferente profundidad y víctimas severamente ocluidas.

---

### P2 · Freeze manifest de SAM 2

**Estado: DISEÑADO**
**Coste:** trivial
**Riesgo:** prácticamente nulo

Debe bloquear ejecución si falta commit/checkpoint/hash.

---

### P3 · Blind external audit

**Estado: DISEÑADO**
**Coste:** bajo

Ocultar seed/config/scores durante juicio semántico inicial.

Revelarlos después.

---

### P4 · A-E(−1) produce riesgo, A-E0 produce verdad de referencia

**Estado: DISEÑADO**

Formalizar esta separación evitará que una métrica provisional se convierta accidentalmente en criterio científico definitivo.

---

# PREGUNTAS PARA CLAUDE

1. ¿Cuál es exactamente `SAM2_GIT_COMMIT`?
2. ¿Qué checkpoint/config se ejecutará y cuál es su SHA256?
3. ¿Las máscaras GT de A-E0 serán **visible-only** o amodales?
4. ¿Cuál es la resolución original/canónica de la fotografía?
5. ¿`scene_inventory` representa explícitamente relaciones `part_of`?
6. ¿Quedarán archivados modelo, versión, prompt y respuesta cruda del auditor IA?
7. ¿Podemos hacer que el auditor vea candidatos cegados antes de scores/config?
8. ¿El ZIP contiene las máscaras completas de **todos** los candidatos o únicamente derivados/seleccionados?

La pregunta 3 es especialmente importante.

Si `Gⱼ` es visible-only, el denominador de DEC-013 representa “fracción de evidencia visible absorbida”.

Si fuera amodal, la misma fórmula tendría una interpretación completamente distinta.

No deberíamos implementar DEC-013 definitivo hasta fijar esa semántica.

---

# PASOS DE LA PERSONA USUARIA

**Estado: ACEPTADO como principio de diseño del proyecto.**

La persona usuaria no tiene que fiscalizar parámetros, máscaras ni hashes.

Solo debe intervenir en decisiones semánticas irreducibles.

Por ahora:

**ninguna acción técnica.**

Nosotros debemos cerrar primero:

1. freeze de SAM 2;
2. DEC-013-Q + prueba sintética;
3. sweep prerregistrado;
4. contrato de auditoría ciega.

Después de eso, la única intervención humana necesaria para ejecutar GPU debería ser, si la infraestructura lo exige, autorizar Colab/OAuth.

---

## VEREDICTO DE CONTRAAUDITORÍA

**Estado general: DISEÑADO / parcialmente VERIFICADO ESTÁTICO.**

v1.2 está suficientemente mejor construido como para continuar.

Pero todavía no está listo para convertir la primera corrida SAM 2 en evidencia experimental definitiva.

Mi condición de salida a GPU es pequeña:

`SAM2_FREEZE = PASS`

`FUSION_SYNTHETIC_TESTS = PASS`

`SWEEP_PREREGISTERED = PASS`

`AUDITOR_PROTOCOL_FROZEN = PASS`

Entonces:

`SAM2_REAL_RUN = GO`

Hasta entonces:

`SAM2_REAL_RUN = HOLD`

No porque espere que SAM 2 falle, sino porque esta es nuestra última oportunidad de definir qué cuenta como fallo **antes de conocer el resultado**.
