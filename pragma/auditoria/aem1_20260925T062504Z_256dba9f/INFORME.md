# Auditoría A‑E(−1) · corrida `20260925T062504Z_256dba9f`

> **Veredicto:** `INCONCLUSIVE_SELECTED_OUTPUT_FAILED` · **ACEPTADO por doble llave** (Claude +
> ChatGPT; la segunda llave estuvo parcialmente contaminada, ver abajo). **Ninguna de las 12
> candidatas separa a la chica completa sin la persona posterior.** El mejor intento, con las dos
> llaves y con la adjudicación, es `box+corrections:s1#0` (A).
> Proyecto: `INCONCLUSIVE_A_E0_REQUIRED` · Fase B bloqueada · SAM 2 **no** rechazable.

## Orden de los hechos (verificable en git)

| Paso | Commit | Qué fija |
|---|---|---|
| 1. Protocolo congelado antes de mirar | `2a9e264` | criterios, reglas y sonda; `PROTOCOLO_AUDITORIA_AEM1_v1.md` = `436937d4…0810` |
| 2. Juicios ciegos crudos antes de desciegar | `84530ff` | `juicios_crudos.json` = `e8286d21…2673`; mapeo sellado `f3e45f06…1325` |
| 3. Desciegue y veredicto de la 1ª llave | `23dbeab` | `aem1_tabla_desciegada.json`, `aem1_audit_verdict.json` |
| 4. Segunda llave (ChatGPT) y comparación | v1.4 | `segunda_llave_chatgpt.json`, `doble_llave.json` (`work/double_key_aem1.py`) |

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

## Doble llave (resultado)

Reproducible con `python3 work/double_key_aem1.py --zip <ZIP>`; el resultado queda en
[`doble_llave.json`](doble_llave.json). La llave de ChatGPT está transcrita en
[`segunda_llave_chatgpt.json`](segunda_llave_chatgpt.json), y su carta original, tal cual, en
[`dialogo/002_chatgpt_a_claude.md`](../../dialogo/002_chatgpt_a_claude.md).

**Veredicto concordante:** ninguna candidata pasa en ninguna de las dos llaves (12/12 candidatas
con el mismo resultado). Coinciden 42 de 48 celdas:

| Criterio | Acuerdo | κ de Cohen | Lectura |
|---|---:|---:|---|
| `other_person_excluded` | 12/12 | 1,00 | las dos llaves señalan las mismas 4 (F, G, I, K) |
| `background_excluded` | 12/12 | — (sin varianza) | todas TRUE en las dos llaves |
| `body_and_edges_complete` | 11/12 | 0,48 | F: UNSURE (Claude) frente a TRUE (ChatGPT) |
| `correct_subject` | 7/12 | 0,25 | C, E, H, J, G: FALSE (Claude) frente a TRUE (ChatGPT) |

**Adjudicación tras desciegar** (no reemplaza los juicios crudos):

| Celda | Claude | ChatGPT | Adjudicado | Por qué |
|---|:-:|:-:|:-:|---|
| C, E, H, J · S | ✗ | ✓ | ✓ | El texto congelado solo excluye a la persona posterior, al señor y el fondo. Una prenda de la chica no es nada de eso: mi ✗ añadía una condición no escrita |
| G · S | ✗ | ✓ | ✓ | **Medido:** al menos el 61,9 % del área de G cae dentro de A, que ambas llaves juzgaron sin persona posterior ni fondo |
| F · B | ? | ✓ | ✗ | **Medido:** 2 agujeros cerrados ≥ 1000 px (2540 y 1885 px), sobre el pelo de la chica junto al índice y sobre el tirante blanco del overol. Son defectos, no huecos de fondo |

- **Concedo 5 de 6 celdas a ChatGPT**; en la sexta, la medición refuta su TRUE y resuelve mi UNSURE.
- **Hueco del protocolo que compartimos:** B y D (un botón) son FALSE en las dos llaves, pero con el
  texto literal también serían «de la chica». Cada llave aplicó un umbral de extensión no escrito,
  y en sitios distintos. El protocolo v2 separa identidad (mayoría del área) y extensión.
- **Contaminación, acotada.** La carta 002 reveló cuántas candidatas había de cada tipo, no cuáles.
  - Las dos llaves reparten las etiquetas en los mismos cuatro grupos: fragmento {B, D}, solo prenda
    {C, E, H, J}, incluye a la persona posterior {F, G, I, K} y resto {A, L}.
  - Acertar esa partición por azar, conociendo solo los recuentos, tiene probabilidad 1/207 900.
  - El acuerdo por etiqueta es, por tanto, evidencia visual. Lo que la carta pudo sesgar son las
    expectativas de cuántas fallan.
- **Límites:**
  - la primera llave es un auto‑cegado;
  - la segunda no devolvió el SHA‑256 del paquete: la identidad se sostiene por la cadena de
    custodia y porque sus 12 descripciones corresponden a las 12 láminas;
  - la segunda llave juzgó JPEG de las mismas láminas PNG, con la misma geometría y una diferencia
    media de 1–3 niveles.
