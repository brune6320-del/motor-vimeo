# PRAGMA · Estado de traspaso Claude → Codex

> Documento operativo. Congela qué se recibió, qué se auditó, qué se portó y cuál es el siguiente paso verificable.
>
> Actualización: 10 de agosto de 2026 · Lima

---

## 1. Estado ejecutivo

Codex ya recibió y archivó byte por byte los dos documentos enviados por Claude. La conclusión es:

- `PRAGMA_Fase_A_v4_parche.md` queda como **antecedente histórico**. Fue escrito contra v3 y no debe aplicarse al v4 ligero actual; hacerlo reintroduciría incompatibilidades ya corregidas.
- `PRAGMA_A-E-1_cierre_fase_A_celdas.md` contiene una **buena hipótesis experimental**, pero no era un parche ejecutable ni podía cerrar honestamente Fase A.
- Codex portó su parte útil a un cuaderno independiente, ordenado, sin JavaScript obligatorio y con informe/manifiesto/ZIP propios.
- El cuaderno nuevo pasó **68 comprobaciones estáticas y lógicas** de estructura, sintaxis, estados, integridad y política. El experimento continúa `NOT_RUN` hasta la ejecución real con GPU en Colab.

El estado científico del proyecto no cambia por crear el cuaderno:

```text
Fase A dirigida por clic: INCONCLUSIVE
Fase A-E inventario de escena: PENDIENTE
Fase B: BLOQUEADA
SAM 2: NO rechazable todavía
Extensión: NO modificada
```

---

## 2. Objetivo actual

Hay dos preguntas distintas y no deben mezclarse:

1. **A‑E(−1), diagnóstico del caso chica:** comprobar si SAM 2.1 Large puede separar a la chica del frente de la tercera persona mediante punto, caja y correcciones negativas.
2. **A‑E, objetivo nuevo del producto:** descubrir, reconocer, segmentar y hacer seleccionable cada objeto visible de la foto.

El cuaderno portado responde solo la primera. Aunque A‑E(−1) funcione, no demuestra que todos los objetos estén inventariados ni reconocidos. Para el objetivo nuevo sigue siendo obligatorio A‑E0: fijar ontología e inventario humano antes de medir modelos.

---

## 3. Fuentes recibidas y hashes

| Artefacto | Estado | SHA‑256 |
|---|---|---|
| `claude_originals/PRAGMA_A-E-1_cierre_fase_A_celdas.md` | copia exacta archivada | `7e832ff61d28077612b9c4cabc4274669b09884f06ab340653e4cc259ace4e91` |
| `claude_originals/PRAGMA_Fase_A_v4_parche.md` | copia exacta archivada | `d5c05f4c2c02026e8ef34baec11b606c28bc1d6f3ae71d643b028548845fe722` |
| `PRAGMA_Fase_A_SAM2_v4_ligero.ipynb` | base Codex existente | `757e9722aa98a4d9420fdca4f287ef36fe78d7b09e2b9e12b3be6896e76e814a` |
| `PRAGMA_A-E-menos-1_diagnostico_caso_chica_Codex.ipynb` | port integrado nuevo | `5941be56b22fccc3efd4e299cc8ee6a12cb7c473d2977d4c0876e4e2ea73b706` |
| `PRAGMA_A-E-menos-1_Codex_verificacion.json` | `STATIC_VERIFICATION_PASS`; experimento `NOT_RUN` | `7067f1ebf6a84c939f41f2409c7d3f73191f47ce179c8e0f94fdd349ee519581` |

Foto de aceptación:

- `P1070614.JPG`
- 4000×2248 px
- SHA‑256 `8f6e3b6f5013265a45c7e89121e3f0a18e3386951e2e75378b28da6d02ec529d`

---

## 4. Qué acertó Claude y fue portado

- Probar caja y puntos negativos antes de atribuir el fallo a SAM 2.
- Mantener las candidatas visibles y elegir por contenido, no por `argmax`.
- Usar sondas KEEP/DROP para volver falsables pérdidas y fugas locales.
- Evitar el selector JavaScript que ya había colgado Colab/Brave.
- Mantener SAM 2.1 Large, el embedding compartido, tiempos y evidencias.
- Tratar la vista suave por logits como diagnóstico, no como matting.

La corrección iterativa usa la API oficial de `SAM2ImagePredictor`: los logits de baja resolución de una salida se pasan como `mask_input`, y los prompts múltiples corregidos se ejecutan con `multimask_output=False`.

Fuente oficial: <https://github.com/facebookresearch/sam2/blob/main/sam2/sam2_image_predictor.py>

---

## 5. Qué no podía trasladarse literalmente

El documento A‑E(−1) de Claude tenía bloqueos verificables:

1. Dos líneas con sintaxis inválida: `seed_candidate_index=<i>` y `mejor=<la candidata elegida>`.
2. Una caja con variables inexistentes: `BOX_CHICA=(x_min, y_min, x_max, y_max)`.
3. Pedía pegar celdas después de que el v4 ya hubiera emitido el veredicto y el ZIP; los resultados nuevos no entrarían en el informe.
4. Cada propuesta nueva invalidaba el trial aceptado, pero el documento nunca finalizaba la candidata ganadora ni generaba un token nuevo.
5. Reutilizaba varios puntos negativos como prompts y como evaluación: una fuga cero en esos puntos era parcialmente circular.
6. Mezclaba tercera persona, cuadro y mesa en un único DROP, impidiendo atribuir el fallo.
7. Convertía siete KEEP y cinco DROP en criterios globales `True`. Esas muestras pueden descubrir un defecto, pero no prueban cuerpo/bordes completos ni ausencia total de contaminación.
8. La modalidad `box+points` no encajaba con el auditor v4 y el baseline `point` dependía de estado RAM previo.
9. No guardaba overlay, configuración, resultados, propuesta/candidata, manifiesto ni ZIP auditado.
10. “Irresoluble por prompt” era una conclusión universal demasiado fuerte para tres intentos en una sola foto.

El parche v4 antiguo tampoco se aplica: cambiaba contratos de retorno, dejaba una función box incompleta, permitía prompts nulos incompatibles y fue escrito contra un SHA de v3, no contra el v4 ligero actual.

---

## 6. Cómo quedó el port Codex

El cuaderno nuevo:

- es independiente y tiene orden de ejecución completo;
- no contiene `eval_js`, selector por clic ni promesas que puedan quedar esperando;
- prellena caja y coordenadas sobre la foto exacta, pero exige confirmación visual;
- separa estrictamente prompts de sentinelas holdout;
- divide fugas en `otra persona` y `fondo`;
- evalúa un parche alrededor de cada sonda, no un único píxel;
- ejecuta cuatro protocolos coherentes:
  - `point`;
  - `box`;
  - `point+corrections` iterativo;
  - `box+corrections` iterativo;
- conserva las tres candidatas ambiguas iniciales;
- obliga a escoger las semillas y la salida final manualmente;
- nunca eleva el éxito de sentinelas a PASS sin inspección humana;
- liga selección, máscara y archivos a hashes y `inspection_token`;
- deriva el ZIP de una lista blanca de la ejecución actual y lo reabre para verificar bytes y SHA‑256;
- registra commit, checkpoint, foto, GPU, dtype, carga, embedding e inferencia por protocolo;
- mantiene `phase_b_blocked=true` en todos los resultados de este diagnóstico.

Estados posibles del caso:

- `PENDING_CONFIG`, `PENDING_PROTOCOLS`, `PENDING_REVIEW`, `PENDING_REVIEW_BINDING`, `PENDING_NOTES` o `PENDING_STALE_*`: falta completar o volver a ligar una etapa.
- `SEPARATION_DEMONSTRATED_UNDER_FIXED_AEM1_PROTOCOL`: sentinelas e inspección humana pasan para esta foto/protocolo.
- `INCONCLUSIVE_SELECTED_OUTPUT_FAILED`: la salida elegida falla, pero no se atribuye el fallo a las otras candidatas.

---

## 7. Pasos exactos en Colab

1. Sube `PRAGMA_A-E-menos-1_diagnostico_caso_chica_Codex.ipynb` a Google Colab.
2. Elige **GPU L4** o **A100**. T4 también sirve; usará fp16.
3. Ejecuta desde el inicio hasta la sección **5. Configuración**.
4. Cuando lo pida, sube `P1070614.JPG`. El nombre puede variar; el hash debe coincidir.
5. Amplía el overlay y lee la tabla ID→región. Si las etiquetas caen en las regiones descritas, marca `AEM1_CONFIG_CONFIRMADA=True` y reejecuta esa celda. Si una está mal, deja `False` y devuelve una captura a Codex.
6. Ejecuta **Baselines: punto y caja**. Mira las seis candidatas.
7. En **Correcciones iterativas**, cambia cada semilla de `-1` al índice 0/1/2 que hayas elegido, marca `AEM1_SEEDS_CONFIRMADAS=True` y ejecuta.
8. Mira las dos salidas corregidas y compara las cuatro modalidades.
9. Primera ejecución de **Elegir y revisar**: selecciona protocolo e índice y deja `AEM1_REVIEW_COMPLETE=False`; se crearán captura, primeros planos y `selection_id`.
10. Amplía y revisa cabeza/pelo, hombro, manos, torso y contacto con la persona posterior. Copia el ID en `AEM1_REVIEWED_SELECTION_ID`, marca `AEM1_REVIEW_COMPLETE=True`, rellena los cuatro criterios y añade notas si alguno es falso. Reejecuta la misma celda.
11. Ejecuta **Informe, manifiesto y ZIP**. El archivo solo se descarga automáticamente cuando la revisión ya no está PENDING.
12. Devuelve a Codex el ZIP y, de ser posible, el `.ipynb` ejecutado. Codex contrastará el veredicto con las capturas; el nombre del ZIP no bastará como prueba.

Si Brave no muestra la subida, **detén esa celda** y usa el panel **Archivos** para colocar la foto en `/content/P1070614.JPG`; después reejecútala. Si la descarga queda girando, **detén la celda después de que imprima `ZIP_PATH`** y descarga ese archivo desde el panel: el ZIP ya quedó escrito y verificado.

No uses **Ejecutar todo** como sustituto de las dos decisiones humanas. A diferencia del v4 anterior, hacerlo no colgará Brave, pero el resultado correcto será PENDING hasta confirmar configuración, semillas y revisión.

---

## 8. Pruebas ya ejecutadas por Codex

La verificación local comprueba, entre otras cosas:

- JSON/nbformat válido;
- 10/10 celdas de código con sintaxis válida;
- cero outputs viejos y cero execution counts heredados;
- hashes exactos de las fuentes archivadas y de la base;
- política T4→fp16, Ampere→bf16, CPU→fp32;
- SAM 2.1 Large sin degradación silenciosa a Small;
- ausencia de `eval_js`, placeholders, `argmax` y registro global caducable;
- prompts y holdouts disjuntos;
- categorías separadas para otra persona y fondo;
- cuatro protocolos y refinamiento con `mask_input`;
- tabla de verdad de estados;
- sentinelas limpios incapaces de generar por sí solos un PASS;
- lista blanca y verificación de hashes al reabrir el ZIP.

Resultado: **68/68 `STATIC_VERIFICATION_PASS`**; `experiment_status=NOT_RUN`.

Límite honesto: esta prueba es estática y lógica. No puede sustituir la corrida GPU real sobre la fotografía.

---

## 9. Próximo paso después de A‑E(−1)

Independientemente de que la separación de la chica funcione o falle, el objetivo “cada objeto posible” exige:

1. **A‑E0:** definir qué cuenta como objeto, tiers, inventario humano, bboxes y GT de las tres personas.
2. **A‑E1 inventario:** ejecutar `SAM2AutomaticMaskGenerator` como baseline class‑agnostic y medir cobertura, duplicación, fraccionamiento, separación y coste.
3. Solo si se requieren nombres, probar después un reconocedor open‑vocabulary con vocabulario oracle, separado del generador de máscaras.

No integrar aún YOLO‑seg, BiRefNet, FastAPI, localhost ni la extensión.

---

## 10. Invariantes de propiedad Codex

- Los dos documentos Claude originales permanecen inmutables en `outputs/claude_originals/`.
- Todo cambio nuevo se hace en artefactos Codex versionados; no se “parchea” el original en silencio.
- Una etiqueta PASS nunca sustituye la inspección de evidencia.
- El resultado v4 histórico `_PASS` sigue corregido a `INCONCLUSIVE` por evidencia visual.
- Fase B solo se desbloquea mediante el contrato A‑E ratificado, no por este diagnóstico de una persona.
- `pragma-extension.zip` permanece intacto.
