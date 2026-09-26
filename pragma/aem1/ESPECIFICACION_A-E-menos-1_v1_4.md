# A‑E(−1) v1.4 · especificación legible

> Fuente de verdad: `aem1/PRERREGISTRO_A-E-menos-1_v1_4.json`, generado por
> `work/design_aem1_v1_4.py` y reproducible byte a byte con `--check`. Este texto lo resume. Si
> discrepan, manda el JSON.

## 1. Por qué existe

v1.3 cerró con `INCONCLUSIVE_SELECTED_OUTPUT_FAILED` y con
`AEM1_POSTERIOR_PERSON_SEPARATION_SUBPROBLEM = DEMONSTRATED`, ambos aceptados por doble llave
(ChatGPT 005). Con H1 y S1 en `box+corrections`, la persona posterior queda fuera. Lo que impide el
PASS es la **completitud**: falta una franja de pelo oscuro entre la cara de la chica y su índice
levantado.

v1.4 hace **una sola intervención**: añade el positivo H2 en esa franja, en la cadena ganadora
`+POS_HAIR+SLEEVE|box+corrections`, con sus tres semillas. Nada más cambia (ChatGPT 005 §4).

## 2. Corrección de la carta 005

La carta 005 propuso H2 = (2964, 672). Al preparar este prerregistro se midió dónde está el agujero
de cada semilla de referencia:

| Semilla (v1.3) | Parte alta de la franja (y ≈ 636–781) | Parte baja (y ≈ 785–1000) |
|---|---|---|
| s0 (C03) | agujero D, 4176 px | agujero D, 7575 px |
| s1 (C01, mejor intento) | **cubierta** | agujero D, **3011 px** (su único D) |
| s2 (C10) | agujero D, 5027 px | agujero D, 8120 px |

(2964, 672) está en la parte **alta**, que C01 ya cubre. Con ese punto, la hipótesis no podía
probarse en el mejor intento. v1.4 elige H2 por regla dentro de lo que falta en **las tres**
semillas, que es la parte baja. El punto viejo queda solo como sonda descriptiva.

## 3. H2: región y regla

- **Región:** los píxeles que las dos llaves de v1.3 marcaron como agujero D en las tres semillas de
  referencia. Son 2973 px en 2984–3025 × 842–997.
- **Regla:** la misma de H1 y S1, restringida a la región. Se toma el mayor cuadrado con ≥ 98 % de
  material oscuro, en rejilla par, con estas restricciones:
  - margen L∞ ≥ 40 px a la caja de contacto;
  - ≥ 100 px a todo holdout y a todo prompt.
- **Resultado:** **H2 = (2994, 892)**.
  - Cuadrado seguro de 31 px (99,1 % oscuro).
  - Margen de 95 px a la caja de contacto; el holdout más cercano es K4, a 212 px.
  - Luma 97,8. Está dentro del agujero objetivo de las tres semillas.
- **Diferencia declarada con H1 y S1:** la franja mide unos 40 px de ancho, así que el cuadrado
  seguro no llega a los 43 px de H1 y S1. El mínimo para H2 es que quepa el parche de luma de 13 px.
  Por eso 3 de las 8 perturbaciones (las que se mueven 15 px hacia el dedo) salen del pelo. Son
  `INVALID_PERTURBATION` y no se ejecutan.
- **Propietario:** Claude lo verificó en la lámina privada. ChatGPT dio su segunda llave en la carta
  006: H2 y sus 5 perturbaciones válidas son pelo de la chica.

## 4. Plan: 22 llamadas, 24 máscaras

| Rama | Llamadas | Máscaras | Qué es |
|---|---:|---:|---|
| `BASE|box` | 1 | 3 | las semillas (misma llamada que v1.3) |
| `+POS_HAIR+SLEEVE` (referencia) | 3 | 3 | la cadena ganadora de v1.3, llamada a llamada idéntica |
| `+POS_HAIR+SLEEVE+H2` | 3 | 3 | lo mismo + H2 como cuarto positivo |
| `PERTURB_POINT|H2` | 15 | 15 | 5 perturbaciones válidas × 3 semillas |

- **Referencia bit a bit:** las 3 semillas y las 3 máscaras de referencia deben salir idénticas a
  las de v1.3; sus hashes están en el prerregistro. Si alguna no lo es, esa semilla se compara con la
  referencia de esta corrida y su consenso ciego. Por eso el cuaderno pide **L4**.
- **Se prohíbe:** elegir por score; reparar máscaras; cambiar H2 o cualquier umbral después de ver
  datos; ejecutar perturbaciones inválidas.

## 5. Auditoría ciega (protocolo v2 rev. 1)

- **Paquete:** 6 láminas, `N01`–`N06`. Son las 3 candidatas con H2 y las 3 de referencia, mezcladas.
  La referencia sirve de señuelo y de **retest**: mide si cada llave repite su juicio de v1.3 sobre
  la misma máscara. Si la referencia es bit a bit, el juicio que cuenta es el de v1.3.
- **Orden:** el paquete va solo a ChatGPT; los juicios de Claude se comprometen por hash; después se
  desciega.
- **Adjudicación prerregistrada:**
  - **O:** se decide por medición. Es FALSE si hay píxeles de máscara en el núcleo oscuro del moño o
    islas separadas en el núcleo hombro/blusa. Si una llave cita material posterior fuera de los
    núcleos, con coordenadas, va a tercera revisión ciega.
  - **Auxiliares:** sin consenso, y no deciden nada.
  - **Resto de criterios:** §5.2 del protocolo.
  - **D/L de un agujero:** solo se adjudica si cuenta para H‑G5.

## 6. Medidas (informan; no aceptan)

- **Agujero objetivo** de cada semilla: el agujero ≥ 1000 px de la referencia que contiene H2. Es
  evaluable si fue D en las dos llaves.
- **Cierre:** quedan menos de 1000 px del objetivo sin cubrir, **y** ningún agujero ≥ 1000 px de la
  candidata lo toca. Lo primero impide llamar cerrado a un faltante que solo dejó de estar encerrado.
- **Región de H2:** el objetivo dilatado 15 px.
- **Agujero D nuevo** (corregido por ChatGPT 006 antes de correr): un agujero ≥ 1000 px de la
  candidata que cumple las dos condiciones:
  - su **pérdida nueva fuera de H2** (agujero ∩ máscara de referencia ∩ ¬región de H2) es ≥ 1000 px;
  - es D en las dos llaves.

  Da igual que el agujero toque la región de H2 o que parte de él ya faltara. La fracción que estaba
  dentro de la referencia solo se reporta. Antes, un contacto de 1 px con la región o menos del 50 %
  dentro de la referencia lo descartaban. Esos eran dos huecos, los casos A y B de ChatGPT 006.
- **O empeora:** la referencia tenía O TRUE y la candidata no. Si la referencia ya era FALSE (s0, con
  una isla de 5 px en el moño), empeora cuando hay más píxeles en los núcleos.
- **Perturbación de H2:** estabilidad (como en v1.3) y si el agujero sigue cerrado con cada
  perturbación.
- **Solo descriptivo:**
  - IoU global y fuera de la región, y píxeles perdidos o ganados fuera;
  - cierre de la parte alta en s0 y s2;
  - retest de las llaves.

## 7. Hipótesis (congeladas antes de los datos)

| ID | De | Se cumple si | Se refuta si |
|---|---|---|---|
| H‑C3 | Claude (carta 005) | ≥ 2 semillas cierran el objetivo sin empeorar O | ni contando como éxito las no evaluables se llega a 2 |
| H‑G5 | ChatGPT (cartas 005 y 006) | ≥ 2 cierran, ninguna empeora O y ninguna tiene un D nuevo (≥ 1000 px de pérdida nueva fuera de la región) | ≥ 2 cierran **con** un D nuevo, o ≥ 2 empeoran O |

En cualquier otro caso, `INDETERMINATE`. H‑G5 es diagnóstica: **no** es un quinto requisito de PASS.

## 8. Decisión y cierre

- **PASS:** solo lo da una candidata con H2 que cumpla el contrato completo en el consenso de las dos
  llaves: los cuatro criterios, agujeros, sentinelas y adjudicación. Cerrar la franja no basta: si
  queda el mentón u otro D, es NO PASS.
- **Etiquetas:** `PASS_FULL_SUBJECT_UNDER_FIXED_AEM1_PROTOCOL` o `INCONCLUSIVE_SELECTED_OUTPUT_FAILED`.
- **Regla de parada:** A‑E(−1) **se cierra con v1.4**, como `AEM1_CLOSED_DEMONSTRATED` o
  `AEM1_CLOSED_INCONCLUSIVE`. Otra iteración exige una decisión explícita de las dos IAs y de la
  persona usuaria.
- **Alcance de un PASS:** una foto, un caso, un protocolo fijo. No demuestra A‑E1 ni generaliza.
- **Lo que no cambia:** SAM 2 no es rechazable; el proyecto sigue en `INCONCLUSIVE_A_E0_REQUIRED`; la
  Fase B sigue bloqueada.
