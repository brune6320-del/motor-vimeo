# Auditoría A‑E(−1) · corrida `20260925T062504Z_256dba9f`

> **Veredicto (primera llave, Claude):** `INCONCLUSIVE_SELECTED_OUTPUT_FAILED`: **ninguna de las 12
> candidatas separa a la chica completa sin la persona posterior**. El mejor intento es
> `box+corrections:s1#0`. **Pendiente de contraauditoría ciega de ChatGPT (segunda llave).**
> Proyecto: `INCONCLUSIVE_A_E0_REQUIRED` · Fase B bloqueada · SAM 2 **no** rechazable.

## Orden de los hechos (verificable en git)

| Paso | Commit | Qué fija |
|---|---|---|
| 1. Protocolo congelado antes de mirar | `2a9e264` | criterios, reglas y sonda; `PROTOCOLO_AUDITORIA_AEM1_v1.md` = `436937d4…0810` |
| 2. Juicios ciegos crudos antes de desciegar | `84530ff` | `juicios_crudos.json` = `e8286d21…2673`; mapeo sellado `f3e45f06…1325` |
| 3. Desciegue y veredicto | este commit | `aem1_tabla_desciegada.json`, `aem1_audit_verdict.json` |

## Evidencia de la corrida

- ZIP `e6bb7a46…1976` (4 702 312 bytes): 24/24 entradas del manifiesto correctas y `run_kind = REAL_GPU`.
- Entorno: SAM 2 commit `2b90b9f5…01a4`, `sam2.1_hiera_large`, checkpoint `2647878d…d318`,
  torch `2.11.0+cu128`, NVIDIA L4, bf16, pico 1,262 GiB.
- Foto `8f6e3b…529d` · 4000×2248 · desviación de luma 0,0 frente al preflight.
- **Reproducción de v4:** la candidata `point#1` reproduce la corrida histórica. Scores 0,906 / 0,002
  / 0,006 y área 15,56 %, idénticos a los aceptados en v4 con el mismo commit y checkpoint. La
  auditoría ciega de hoy, hecha sin saber qué candidata era, coincide con la auditoría visual que
  corrigió aquel PASS a `INCONCLUSIVE`.

## Tabla desciegada

`S` = `correct_subject` · `B` = `body_and_edges_complete` · `O` = `other_person_excluded` ·
`G` = `background_excluded`. `✓` TRUE · `✗` FALSE · `?` UNSURE, que cuenta como ✗.

| Ciega | Candidata | S | B | O | G | Sentinelas fallidos | Defecto principal |
|---|---|:-:|:-:|:-:|:-:|---|---|
| **A** | **box+corrections:s1#0** | ✓ | ✗ | ✓ | ✓ | K5 | sin el pelo de la chica; mangas oscuras perforadas |
| B | point#0 | ✗ | ✗ | ✓ | ✓ | K1–K7 | solo un botón |
| C | box+corrections:s2#0 | ✗ | ✗ | ✓ | ✓ | K1–K6 | solo el overol (prenda) |
| D | point+corrections:s0#0 | ✗ | ✗ | ✓ | ✓ | K1–K7 | solo un botón |
| E | box+corrections:s0#0 | ✗ | ✗ | ✓ | ✓ | K1–K6 | solo el overol (prenda) |
| F | box#1 | ✓ | ? | ✗ | ✓ | O2, O3 | la más completa, pero **incluye el moño posterior** |
| G | box#0 | ✗ | ✗ | ✗ | ✓ | K4, K7, O2, O3 | fusión con blusa, hombro y moño posteriores |
| H | point+corrections:s2#0 | ✗ | ✗ | ✓ | ✓ | K1–K6 | solo el overol inferior |
| I | box#2 | ✓ | ✗ | ✗ | ✓ | K4, K7, O2, O3 | moño incluido; mano en V perforada en cuadrícula |
| J | point#2 | ✗ | ✗ | ✓ | ✓ | K1–K6 | overol inferior y un tirante |
| K | point#1 (≡ v4) | ✓ | ✗ | ✗ | ✓ | K5 | fragmentos del moño; pelo deshilachado; mangas perforadas |
| L | point+corrections:s1#0 | ✓ | ✗ | ✓ | ✓ | K1, K5, K6 | cara y mano perforadas; sin pelo ni mangas |

La conciliación con los sentinelas no cambió ningún juicio: todos los fallos de sentinela coinciden
con criterios ya marcados ✗. Al revés no siempre ocurre: en **K** vi fragmentos dispersos del moño
que ningún sentinela v1.2 tocó. Los sentinelas falsan, pero no demuestran limpieza, y la inspección
visual sigue siendo necesaria.

## Lo que la corrida enseña (diagnóstico, no verdad de referencia)

1. **El conflicto es de textura, no de posición.** Las correcciones negativas sobre la persona
   posterior, que es pelo y tela oscuros, eliminan también lo oscuro de la chica (su pelo y sus
   mangas). Sin correcciones, lo oscuro entra entero y arrastra el moño (F, I, K). En este caso, el
   protocolo punto/caja/negativos no encuentra una frontera que conserve el pelo de la chica y
   excluya el de la persona posterior.
2. **La semilla decide.** Las tres semillas de `box+corrections` producen resultados incompatibles
   en la zona de contacto (IoU 0,13–0,83). En `point+corrections`, dos de las tres ni llegan a esa
   zona. Elegir una sola semilla a mano habría ocultado esa inestabilidad (R2 de ChatGPT).
3. **El preflight tenía razón.** El O2 de v1.0, sobre la pared, no detecta el moño en ninguna
   candidata; los O2/O3 de v1.2, dentro del moño, lo detectan en las tres `box`. El O3 ambiguo de
   v1.0 marcaba `point#1`, pero sobre un píxel cuyo propietario no se puede asegurar.

## Sonda de riesgo de contacto (solo informa; no decide)

Caja `(2150, 250, 2900, 1300)`, reglas prerregistradas en el protocolo §5:

| Grupo | Etiqueta | IoU mínimo | Nota |
|---|---|---:|---|
| semillas `point+corrections` | `NOT_EVALUABLE` | — | s0 y s2 tienen 0 px en la caja |
| semillas `box+corrections` | `CONFLICT` | 0,135 | s1 frente a s0/s2; el conflicto refleja sobre todo máscaras incompletas, no dos dueños distintos del mismo píxel |
| `point` frente a `box` corregidos | `CONFLICT` | 0,000 | el mejor par (s1↔s1) llega a 0,726 |

## Siguiente experimento (propuesta: prerregistrar antes de correr)

Dentro de A‑E(−1), sin tocar A‑E1:

- **(a) Prompts positivos explícitos** sobre el pelo de la chica y sobre sus mangas oscuras. Deben
  ser coordenadas nuevas, disjuntas de los holdouts, validadas con preflight. Es la prueba directa
  del punto 1.
- **(b) Prompt recíproco** a la persona posterior (R5‑4 de ChatGPT), para ver qué región reclama cada máscara.
- **(c) Perturbación** de ±15 px en punto y caja (R5‑3).

Criterio de éxito que se fija antes de correr: el mismo protocolo §6 con los mismos cuatro
criterios, en auditoría ciega.

## Doble llave

- Material para ChatGPT: las 12 láminas ciegas A–L, sin mapeo ni juicios, compartidas en privado
  por la persona usuaria.
- Si ChatGPT marca como `TRUE` los cuatro criterios de alguna candidata que yo marqué `✗`, se revisa
  juntos y decide la persona usuaria.
