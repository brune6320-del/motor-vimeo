# Auditoría A‑E(−1) v1.3 · corrida `20260926T040705Z_bee282c1`

> **Veredicto (doble llave, protocolo v2 rev. 1):** `INCONCLUSIVE_SELECTED_OUTPUT_FAILED`. Ninguna
> de las 18 candidatas ciegas cumple los cuatro criterios.
>
> - **Mejor intento:** C01 = `+POS_HAIR+SLEEVE|box+corrections|s1`. Su único defecto es un agujero
>   de 3011 px: el pelo de la chica entre la cara y el dedo índice.
> - **Hallazgo principal:** la separación de la persona posterior ya se consigue. Con positivos en el
>   pelo (H1) y la manga (S1), en `box+corrections`, las dos llaves marcan `other_person_excluded`
>   TRUE, sin fugas en los sentinelas.
> - **Lo que impide el PASS ahora** es la completitud, no la persona posterior.
> - SAM 2 **no** rechazable · proyecto `INCONCLUSIVE_A_E0_REQUIRED` · Fase B bloqueada.

## 1. Orden de los hechos (verificable en git)

| Paso | Commit | Qué fija |
|---|---|---|
| Prerregistro, protocolo v2 rev. 1 y código de análisis congelado por hash | `423d809` | `content_sha256` `5800f2bf…2a8c` |
| GO de ChatGPT (carta 004) | `0f14566` | archivado antes de abrir nada |
| 2 · Integridad sin resultados | `0f14566` | `INTEGRITY_PASS` · `REAL_GPU` · L4 · bf16 · 178/178 llamadas · 210 máscaras |
| 3 · Paquete ciego y mapeo sellado | `0f14566` | `a77a47b5…051e` · `e1986a2b…c63f` |
| 5 · Juicios de Claude, solo el hash | `abd3f32` | `8dde158b…57bf` |
| 6 · Llave de ChatGPT (con el SHA‑256 del paquete) y apertura del compromiso | `c353cd5` | el hash coincide |
| 7 · Desciegue, adjudicación y análisis | este commit | `work/unblind_aem1_v1_3.py` |

## 2. Mapeo y consenso

S = sujeto correcto · B = cuerpo y bordes completos · O = otra persona fuera · G = fondo fuera.
Pelo y mangas son las preguntas auxiliares. D = área de los agujeros que las dos llaves marcaron como
defecto.

| Ciega | Candidata | S | B | O | G | Pelo | Mangas | D (px) |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|---:|
| **C01** | **+POS_HAIR+SLEEVE · box+corr · s1** | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | **3011** |
| C02 | +POS_HAIR · box+corr · s2 | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | 15287 |
| C03 | +POS_HAIR+SLEEVE · box+corr · s0 | ✓ | ✗ | ✗ᵃ | ✓ | ✓ | ✓ | 14736 |
| C04 | +POS_SLEEVE · point+corr · s0 | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | 1697 |
| C05 | +POS_SLEEVE · box+corr · s1 | ✓ | ✗ | ✓ᵇ | ✓ | ≠ | ✓ | 15886 |
| C06 | +POS_HAIR+SLEEVE · point+corr · s0 | ✓ | ✗ | ✗ (moño) | ✓ | ✓ | ✓ | 37216 |
| C07 | +POS_HAIR+SLEEVE · point+corr · s2 | ✓ | ✗ | ✓ᵇ | ✓ | ✗ | ✗ | 25114 |
| C08 | +POS_HAIR · box+corr · s0 | ✓ | ✗ | ✗ | ✓ | ✓ | ✓ | 0 |
| C09 | +POS_SLEEVE · point+corr · s2 | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | 0 |
| C10 | +POS_HAIR+SLEEVE · box+corr · s2 | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | 23940 |
| C11 | +POS_HAIR · box+corr · s1 | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | 7226 |
| C12 | +POS_HAIR · point+corr · s1 | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ | 10329 |
| C13 | +POS_HAIR · point+corr · s2 | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | 0 |
| C14 | +POS_HAIR+SLEEVE · point+corr · s1 | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | 7324 |
| C15 | +POS_SLEEVE · box+corr · s2 | ✓ | ✗ | ✓ | ✓ | ✗ | ≠ | 18950 |
| C16 | +POS_SLEEVE · point+corr · s1 | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | 0 |
| C17 | +POS_HAIR · point+corr · s0 | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ | 35632 |
| C18 | +POS_SLEEVE · box+corr · s0 | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | 9509 |

- ᵃ Adjudicado por medición.
- ᵇ Adjudicado por medición, **provisional** hasta que ChatGPT lo confirme.
- ≠ Sin consenso en una auxiliar. La regla prerregistrada solo cuenta las auxiliares con TRUE en ambas llaves.
- **BASE:** las 12 se reproducen **bit a bit** (`BIT_EXACT`), así que su referencia es
  `BASE_V2_REFERENCE`.
- **Agujero de la mano que cuelga:** las dos llaves lo marcan L. Claude lo describe como el teléfono
  que sostiene y ChatGPT como un hueco entre la mano y el torso: misma etiqueta, descripción distinta.

## 3. Comparación de llaves y adjudicación técnica

| | Acuerdo |
|---|---:|
| Criterios | 69/72 |
| Auxiliares | 34/36 |
| Agujeros D/L | 56/56 |
| Total de celdas | 103/108 |

**Regla de medición para O, fijada antes de medir:** cualquier píxel de máscara dentro de un núcleo
de la persona posterior (≥ 10 px de la frontera ambigua) da FALSE. Los núcleos son el material
oscuro del moño en 2610–2780 × 315–415 y el hombro/blusa en 2400–2520 × 840–990.

| Celda | Claude | ChatGPT | Adjudicado | Evidencia |
|---|:-:|:-:|:-:|---|
| C03 · O | ✓ | ✗ | **✗** | isla de 5 px **dentro del núcleo del moño** (2616–2620 × 399–401). Tenía razón ChatGPT |
| C05 · O | ✓ | ✗ | ✓ (provisional) | 0 px en todos los núcleos y en O1–O4. Sus islas están en la corona y la frente de la chica: 693 px en 2657–2695 × 540–565 y 452 px en 2783–2839 × 447–458, a la derecha y por debajo del borde visible del moño |
| C07 · O | ✓ | ✗ | ✓ (provisional) | 0 px en todos los núcleos; su isla más alta (63 px en 2789–2807 × 448–455) está en la corona de la chica |
| C05 · pelo, C15 · mangas | — | — | sin consenso | regla prerregistrada: una auxiliar cuenta solo con TRUE en ambas llaves |

**Corrección declarada tras medir.** El borde inferior del núcleo hombro/blusa (y 980–990) toca el
hombro de la chica.

- Los píxeles de C03, C08, C12, C14, C16 y C17 en esa franja pertenecen a la componente principal de
  la chica, que baja hasta y = 1149 (verificado por conectividad).
- Solo cuentan las islas separadas: C04 (179 px) y C06 (14 px).

**Ninguna adjudicación cambia**, y ninguna discrepancia cambia el veredicto (B es FALSE en las 18) ni
el resultado de ninguna hipótesis.

## 4. Hipótesis prerregistradas

| ID | Resultado | Por qué |
|---|---|---|
| H‑C1 (Claude) | **REFUTADA** | 4 de las 6 de +POS_HAIR (C02, C11, C12, C17) recuperan el pelo en ambas llaves **sin** arrastrar el moño: O TRUE en ambas y sin fuga O2/O3 |
| H‑C2 (Claude) | **SE CUMPLE** | P+1 perturbado en `point`: la salida 0 es `UNSTABLE` (IoU mínimo 0,005: la máscara del botón cambia por completo); la salida 1 es `CONFLICT` (O3 pasa de 0,006 a 0,231 y 0,331) |
| H‑G1 (ChatGPT) | **REFUTADA** | solo 1 de 6 de +POS_SLEEVE (C05) recupera las mangas en ambas llaves |
| H‑G2 (ChatGPT) | **SE CUMPLE** | el recíproco es `UNSTABLE` (IoU mínimo 0,689 en contacto) pero nunca `CONFLICT`: ninguna semilla incluye a la chica |
| H‑G3 (ChatGPT) | **SE CUMPLE** | `R_ref` (s0) cubre O2 y O3; BASE box#0–2 y C06 arrastran el moño y son `SHARED` con `R_ref` (\|T∩R\|/\|R\| entre 0,26 y 0,49; \|T∩R\|/\|T\| entre 0,07 y 0,14) |
| H‑G4 (ChatGPT) | **SE CUMPLE** | 5 de 6 de +POS_HAIR+SLEEVE (C01, C03, C06, C10, C14) recuperan pelo y mangas en ambas llaves |

## 5. Perturbación y recíproco (solo informan)

**Caja:**

- traslación, expansión y contracción son `STABLE` en `box` y `box+corrections`, en las 3 salidas.

**Punto:**

| Punto perturbado | Cadena | Resultado |
|---|---|---|
| P+1 | `point` | `UNSTABLE`, `CONFLICT`, `STABLE` |
| P+1 | `point+corrections` | `UNSTABLE`, `UNSTABLE`, `STABLE` |
| H1 | `box+corrections` | `STABLE` ×3 |
| H1 | `point+corrections` | `CONFLICT`, `STABLE`, `UNSTABLE` |
| S1 | `box+corrections` | `STABLE` ×3 |
| S1 | `point+corrections` | `STABLE`, `STABLE`, `UNSTABLE` |

- **H1 en `point+corrections` s0 (C06):** bajar H1 15 px quita el moño; O2 pasa de 0,52 a ≤ 0,05 y
  O3 de 0,77 a ≤ 0,03. En área casi no cambia (IoU 0,989), pero cruza el moño.
- **La cadena `box+corrections` con H1+S1 es robusta a ±15 px.**

**Recíproco:**

- `R-corrections` es `UNSTABLE`: IoU 0,715, 0,689 y 0,815. Solo la semilla s0 atribuye el moño a la
  persona posterior; s1 y s2 cubren la blusa (O1, O4) pero no el moño.
- La tabla de interpretación prerregistrada devuelve `NO_INFERENCE` para todas, porque R no es `STABLE`.

## 6. Descriptivo exploratorio (no prerregistrado)

IoU mínimo entre semillas, en la caja de contacto, para `box+corrections`:

| Rama | IoU mínimo |
|---|---:|
| BASE | 0,135 (el `CONFLICT` de la corrida 1) |
| +POS_SLEEVE | 0,487 |
| +POS_HAIR | 0,791 |
| **+POS_HAIR+SLEEVE** | **0,919** (0,974–0,985 global) |

En `point+corrections` sigue siendo baja (≤ 0,45).

## 7. Cierre (ChatGPT 005)

ChatGPT revisó el desciegue (`dialogo/005_chatgpt_a_claude.md`) y cerró los puntos abiertos. El
registro está en `cierre_chatgpt005.json`; `doble_llave_v13.json` no se modifica.

- **C05 y C07 · O = TRUE:** aceptado. Las islas están en la corona de la chica, no en el moño. No
  hace falta tercera revisión con Codex. La corrección del núcleo hombro/blusa también se acepta.
- **Hipótesis:** aceptadas tal como se prerregistraron. H‑G3 se cumple **bajo `R_ref`**, pero eso no
  es una propiedad recíproca estable: `RECIPROCAL_OWNERSHIP_STABLE = FALSE`.
- **Nombre correcto del hallazgo:** `AEM1_POSTERIOR_PERSON_SEPARATION_SUBPROBLEM = DEMONSTRATED`
  para C01, C02, C10, C11 y C14, bajo este protocolo. `FULL_SUBJECT_SEGMENTATION = NOT_DEMONSTRATED`.
  El resumen de arriba («la separación de la persona posterior ya se consigue») se lee en ese
  sentido: es el subproblema de A‑E(−1), no PRAGMA.
- **v1.3:** `CLOSED_INCONCLUSIVE`.

**Corrección posterior de Claude sobre §1 y la carta 005:** C01 conserva la parte **alta** de la
franja. Su único agujero D es la parte **baja**, 2984–3025 × 842–997. El punto H2 = (2964, 672)
propuesto en la carta 005 cae en la parte alta, que solo falta en s0 y s2. v1.4 lo corrige; ver
`aem1/PRERREGISTRO_A-E-menos-1_v1_4.json`.

Archivos:

- `cierre_chatgpt005.json`: adjudicación final, hipótesis y alcance de lo demostrado;
- `mapeo_desciegado.json`: el mapeo sellado, SHA‑256 registrado en el paso 3;
- `doble_llave_v13.json`: comparación, mediciones y adjudicación;
- `aem1v13_analisis.json`: el análisis prerregistrado completo, más el descriptivo exploratorio marcado como tal.
