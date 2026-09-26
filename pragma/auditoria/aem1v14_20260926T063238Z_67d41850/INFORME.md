# Auditoría A‑E(−1) v1.4 · corrida `20260926T063238Z_67d41850`

> **Veredicto (doble llave + adjudicación técnica ciega, protocolo v2 rev. 1):**
> `INCONCLUSIVE_SELECTED_OUTPUT_FAILED` → **`AEM1_CLOSED_INCONCLUSIVE`** (regla de parada
> prerregistrada). Ninguna candidata con H2 cumple los cuatro criterios.
>
> - **H2 hizo lo que se prerregistró.** Cierra el agujero de la franja en las **3 semillas**, sin
>   empeorar O. Es estable a ±15 px (IoU ≥ 0,998, cerrado en las 5 perturbaciones de cada semilla) y
>   cierra también el tramo alto de la franja en s0 y s2. **H‑C3 se cumple.**
> - **Lo que impide el PASS ya no es la franja:** es el **pelo lateral de la chica junto al mentón**.
>   Falta en las seis máscaras, H2 incluidas, y ya faltaba en el mejor intento de v1.3 (C01). Además,
>   en s0 persiste una isla de 3–5 px dentro del núcleo del moño.
> - **H‑G5:** `INDETERMINATE` (en s2 aparece un agujero D nuevo; en s0 y s1, no).
> - SAM 2 **no** es rechazable · proyecto `INCONCLUSIVE_A_E0_REQUIRED` · Fase B bloqueada.

## 1. Orden de los hechos (verificable en git)

| Paso | Commit | Qué fija |
|---|---|---|
| Prerregistro y contraauditoría (ChatGPT 006) con el parche `new_d` | `0717af7` | `content_sha256` `7048b9fa…0b5d` |
| `GO_TO_GPU` de ChatGPT (carta 007), archivado antes de correr | `02b9d63` | — |
| 2 · Integridad y 3 · paquete ciego sellado | `f2de121` | `INTEGRITY_PASS` · `REAL_GPU` · L4 · 22/22 · 24 máscaras · paquete `8f8df273…a17b` · mapeo `1a68b79e…1a66` |
| 5 · Juicios de Claude, solo el hash | `0a0e19c` | `6febe5d6…78d0` |
| 6 · Llave de ChatGPT (con el SHA‑256 del paquete) y apertura del compromiso | `0df03f5` | el hash coincide |
| 6b · Reglas de adjudicación, **antes de medir** | `751cbaa` | `work/adjudicate_aem1_v1_4.py` |
| 6c · Adjudicación técnica **a ciegas**, por etiqueta | `aa164e3` | N01 y N05 · O = FALSE; N04 · B = FALSE |
| 7 · Desciegue y análisis prerregistrado | este commit | `work/unblind_aem1_v1_4.py` |

## 2. Referencia

`BASE|box` y las tres semillas de referencia salieron **bit a bit** iguales a v1.3 (`BIT_EXACT`).
Por eso manda la doble llave congelada de v1.3 para la referencia, y el re‑juicio solo describe.

## 3. Mapeo y consenso

S = sujeto correcto · B = cuerpo y bordes completos · O = otra persona fuera · G = fondo fuera.

| Ciega | Candidata | S | B | O | G | Agujeros (D/L) |
|---|---|:-:|:-:|:-:|:-:|---|
| N01 | **H2 · s0** | ✓ | ✗ | ✗ᵃ | ✓ | #1 L · #2 D (2177 px, junto al mentón) |
| N02 | **H2 · s2** | ✓ | ✗ | ✓ | ✓ | #1 L · #2 D (10374 px, pelo lateral) |
| N03 | referencia s2 (= C10) | ✓ | ✗ | ✓ | ✓ | #1 L · #2 D · #3 D · #4 D |
| N04 | **H2 · s1** | ✓ | ✗ᵇ | ✓ | ✓ | #1 L |
| N05 | referencia s0 (= C03) | ✓ | ✗ | ✗ᵃ | ✓ | #1 L · #2 D · #3 D · #4 D |
| N06 | referencia s1 (= C01) | ✓ | ✗ | ✓ | ✓ | #1 L · #2 D (3011 px, franja) |

- ᵃ Adjudicado por medición, con la regla prerregistrada: una isla dentro del núcleo del moño,
  de 3 px en N01 (2616–2619 × 399–400) y de 5 px en N05 (2616–2620 × 399–401).
- ᵇ Adjudicado por medición, con una regla fijada antes de medir. N04 deja fuera **10 043 px**
  (9 704 abiertos al exterior) del material que las dos llaves marcaron D en las otras láminas.
  Cualquier agujero lateral acordado basta por sí solo: N01#2 2067 px, N05#4 2386, N03#2 7260,
  N02#2 9387 (`adjudicacion_robustez_ciega_v14.json`).
- Las auxiliares (pelo y mangas) son TRUE en las seis, en ambas llaves.

**Acuerdo entre llaves:** criterios 21/24, auxiliares 12/12, agujeros 15/15. Discrepancias:

- N01 y N05 · O: Claude FALSE (vio la isla dentro del moño) y ChatGPT TRUE. Medición → FALSE.
- N04 · B: Claude FALSE (faltante abierto de pelo lateral) y ChatGPT TRUE («no observo faltantes de
  contorno ≥ ~1000 px»). Medición → FALSE.

**Mejor intento** (§5.4): N04 = H2 · s1. Tiene 1 celda no TRUE sumando llaves, 7/7 KEEP y ningún
agujero D cerrado; su defecto es el faltante abierto de pelo lateral.

## 4. Medidas prerregistradas por semilla

| Semilla | Agujero objetivo (referencia) | Sin cubrir con H2 | Cerrado | D nuevo fuera de H2 | O peor |
|---|---|---:|:-:|:-:|:-:|
| s0 | #2, 7575 px | 406 px (95 % cubierto) | sí | no | no (núcleo 5 → 3 px) |
| s1 | #2, 3011 px | 339 px (89 %) | sí | no | no |
| s2 | #3, 8120 px | 488 px (94 %) | sí | **sí**: #2 lateral, 1883 px de pérdida nueva, D en ambas llaves | no |

- **H‑C3 (Claude) · `HOLDS`:** 3 de 3 semillas cierran el objetivo sin empeorar O.
- **H‑G5 (ChatGPT) · `INDETERMINATE`:** 3 semillas cerradas y ninguna con O peor, pero s2 tiene un D
  nuevo. `HOLDS` exige que no haya ninguno y `REFUTED` exige al menos 2.
- **Perturbación de H2:** `STABLE` en las 3 semillas (IoU mínimo 0,998–0,999; en la caja de contacto,
  0,994–0,997), sin cruces de O. El agujero objetivo sigue cerrado en las 15 perturbaciones.
- **Descriptivo prerregistrado:**
  - el tramo alto de la franja también se cierra en s0 (quedan 12 px) y s2 (30 px);
  - cambio global: IoU 0,984–0,993;
  - píxeles perdidos fuera de la región de H2: 2626, 3589 y 5362.
- **Retest** (misma máscara que en v1.3): en s1 y s2 las dos llaves repiten los 8 juicios. En s0,
  **las dos cambiaron O en sentidos opuestos**: Claude TRUE → FALSE, ahora igual que la medición;
  ChatGPT FALSE → TRUE. Resultado: cada llave repite 11 de 12.

## 5. Hallazgo exploratorio (después del desciegue)

`hallazgo_pelo_lateral_v14.json`. El pelo lateral de la chica junto al mentón (región D acordada,
13 944 px) falta en **las seis** máscaras:

- en s0 y s2 como agujero cerrado (2991, 10 404, 12 034 y 4420 px);
- en s1 abierto al exterior (N04: 9704 px; N06 = C01: 9803 px).

N04 y N06 difieren en menos de 500 px en esa región: **H2 no causó el defecto; ya estaba en el
mejor intento de v1.3.** Nadie lo señaló entonces porque C01 ya fallaba por la franja y las láminas
solo contornean los agujeros cerrados. Claude sí anotó en v1.3 «pelo del lado izquierdo fragmentado
junto al hombro», pero no lo midió.

## 6. Lo que A‑E(−1) deja demostrado (para el cierre)

1. **Separación de la persona posterior:** demostrada en v1.3 (subproblema).
2. **Completitud de la franja entre la cara y el índice:** un positivo H2 la repara de forma local y
   estable en las 3 semillas (H‑C3).
3. **Segmentación completa de la chica:** **no** demostrada. Quedan el pelo lateral junto al mentón
   (todas las cadenas) y, en s0, una isla diminuta en el moño.
4. **Método:** las dos llaves visuales fallan de forma reproducible con islas de 3–5 px y con
   faltantes abiertos. Las mediciones con reglas fijadas antes de medir los resolvieron las dos veces.

## Archivos

- `mapeo_desciegado.json`: el mapeo sellado, con el SHA‑256 del paso 3.
- `doble_llave_v14.json`: la comparación, la adjudicación y el mapeo.
- `adjudicacion_tecnica_ciega_v14.json` y `adjudicacion_robustez_ciega_v14.json`: la adjudicación,
  hecha antes del desciegue.
- `aem1v14_analisis.json`: el análisis prerregistrado completo.
- `hallazgo_pelo_lateral_v14.json`: exploratorio.
