# A‑E(−1) v1.3 · especificación cerrada

> **Estado:** `PREREGISTERED`: contraauditado por ChatGPT (carta 003), con sus cambios aplicados
> antes de correr.
> - **Cuaderno:** `outputs/PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_3.ipynb`, generado desde
>   el prerregistro y verificado 26/26 con SAM **simulado**.
> - **GPU:** todavía `NOT_RUN`.
> - **Cambios de ChatGPT 003:** BASE usa `BASE_V2_REFERENCE` (§4); las discrepancias van a
>   adjudicación técnica (§7); hay métricas continuas y razones direccionales (§6); se añaden
>   H‑G1–G4 (§8) y la descripción de P+1 pasa a ser «botón/overol en el torso de la chica».
> **Fuente de verdad:** [`PRERREGISTRO_A-E-menos-1_v1_3.json`](PRERREGISTRO_A-E-menos-1_v1_3.json),
> generado y comprobable con `python3 work/design_aem1_v1_3.py [--check]` (necesita la foto).
> Métricas: `pragma_ae/aem1_v13.py`. Tests: `tests/test_aem1_v13.py`.
> Auditoría ciega: [`auditoria/PROTOCOLO_AUDITORIA_AEM1_v2.md`](../auditoria/PROTOCOLO_AUDITORIA_AEM1_v2.md).
> Responde a ChatGPT 002: ramas independientes, región segura, perturbación exacta y recíproco sin reparación.

## 1. Pregunta

La corrida 1 mostró un conflicto de **textura**:

- los negativos sobre la persona posterior, que es pelo y tela oscuros, se llevan también el pelo
  y las mangas de la chica;
- sin negativos, lo oscuro entra entero con el moño.

v1.3 pregunta **qué intervención mueve esa frontera y cuánto depende de 15 px**. Lo pregunta con
una rama por intervención, para poder atribuir causas (ChatGPT 002 §1).

## 2. Congelado

- **Idéntico a la corrida 1:** SAM 2 `2b90b9f5…01a4`, `sam2.1_hiera_l.yaml`, checkpoint
  `2647878d…d318` (898 083 611 bytes), bf16 y la foto `8f6e3b…529d` a 4000×2248 tras EXIF.
- **Gate:** el cuaderno bloquea antes de generar si algo difiere.
- **Luma:** el cuaderno recalcula la luma de todos los prompts, base y perturbados, y bloquea si
  alguno se desvía más de 3,0 de lo registrado.

## 3. Prompts nuevos (región segura; ChatGPT 002 §2)

Ninguno se elige a mano. La regla es `select_safe_point`: dentro de una ventana declarada, el
centro del mayor cuadrado con ≥ 98 % de material oscuro, sujeto a estas condiciones:

- luma < 110 tras una media 9×9, el mismo umbral «dark» de la auditoría;
- margen L∞ ≥ 40 px a la caja de contacto `(2150, 250, 2900, 1300)`;
- ≥ 100 px de todo holdout y de todo prompt;
- cuadrado ≥ 43 px (semilado 21 = 15 de perturbación + 6 del parche).

La caja de contacto contiene toda la frontera visible chica↔persona posterior, así que su margen es
una **cota inferior de la distancia a la frontera**.

| ID | Propietario · material | (x, y) | Cuadrado seguro | Fracción oscura | Margen a la caja | Holdout más cercano | Prompt más cercano | Parche 13×13 (media / sd) |
|---|---|---|---:|---:|---:|---|---|---|
| **H1** | chica · pelo oscuro | (3072, 592) | 61 px | 0,982 | 173 px | K1 a 240,9 px | P‑2 a 461,4 px | 70,8 / 48,4 |
| **S1** | chica · manga oscura | (2230, 1686) | 171 px | 0,984 | 387 px | K6 a 249,1 px | P+1 a 371,4 px | 66,9 / 49,4 |

- **H1** está en el pelo del lado derecho de la cabeza, el opuesto al moño, entre el dedo índice y
  el cuadro de la pared. Ventana declarada: `(2940, 400, 3200, 900)`.
- **S1** está en la manga oscura del brazo que cuelga, unos 150 px por encima de la mano. Ventana
  declarada: `(2120, 1350, 2340, 1850)`.
- **Propietario:** Claude lo verificó en la lámina privada de diseño. La segunda llave de ChatGPT
  sobre esa misma lámina está pendiente.
- Todas las cifras llevan el hash de la imagen.

## 4. Ramas (independientes; cada una cambia una sola cosa)

Todas parten del mismo embedding de la imagen. Ninguna usa salidas de otra, salvo las semillas
de BASE, que se declaran explícitamente.

| Rama | Qué cambia frente a BASE | Protocolos | Máscaras |
|---|---|---|---:|
| **BASE** | nada: réplica exacta de la corrida 1 | `point`, `box`, `point+corrections:s0–s2`, `box+corrections:s0–s2` | 12 |
| **+POS_HAIR** | H1 con etiqueta 1 **solo en la llamada de corrección** | `point+corrections`, `box+corrections` × 3 semillas de BASE | 6 |
| **+POS_SLEEVE** | S1, igual | ídem | 6 |
| **+POS_HAIR+SLEEVE** | H1 y S1, igual | ídem | 6 |
| **RECIPROCAL_POSTERIOR** | se pide a la persona posterior | `R-point` = P‑1 positivo con 3 salidas; `R-corrections:s0–s2` = positivos P‑1, P‑2, P‑3 y negativos P+1, H1, S1 | 6 |
| **PERTURB_POINT** | un punto desplazado cada vez | P+1 en `point` y `point+corrections` (toda la cadena); H1 o S1 en `+POS_HAIR+SLEEVE` | 144 |
| **PERTURB_BOX** | la caja perturbada | `box` y `box+corrections` (toda la cadena) | 30 |

- **Combinación final:** **ninguna** en v1.3, porque no se prerregistra (ChatGPT 002 §1).
- **Por qué +POS solo en las correcciones:** los positivos nuevos existen para contrarrestar a los
  negativos. En la corrida 1, `box` sin negativos ya incluía todo lo oscuro y `point` no lleva
  negativos. Las semillas son las de BASE, así que la **única** diferencia frente a BASE es el
  positivo añadido.
- **Reproducción de BASE:** se comparan los `packed_mask_sha256` con los de la corrida 1.
  - `BIT_EXACT`: su referencia es `auditoria/aem1_20260925T062504Z_256dba9f/BASE_V2_REFERENCE.json`.
    Es la adjudicación de la corrida 1 normalizada a las definiciones v2; **no** es una doble llave
    v2 heredada (ChatGPT 003 e).
  - `NOT_BIT_EXACT`: las que difieran vuelven al paquete ciego.

## 5. Perturbaciones (definición exacta; ChatGPT 002 §3)

**Punto:**

- anillo L∞ de radio 15, determinista, con las axiales primero: `(+15,0) (−15,0) (0,+15) (0,−15)`;
- después las diagonales: `(+15,+15) (+15,−15) (−15,+15) (−15,−15)`;
- se perturba un solo punto cada vez.

Un punto perturbado es `INVALID_PERTURBATION`, y **no se ejecuta ni cuenta contra SAM 2**, si:

- sale de la imagen;
- queda a < 25 px L∞ de la caja de contacto;
- queda a < 78 px de un holdout;
- o, para H1 y S1, su parche deja de ser oscuro (< 90 %).

**Resultado del diseño: 24/24 válidas.**

- Las 8 de P+1 caen sobre el overol. Tres de ellas, `(0,+15)`, `(+15,+15)` y `(−15,+15)`, caen
  dentro de la caja del botón que `point#0` devolvió en la corrida 1 (2555–2604 × 1785–1824),
  justo debajo de P+1: luma 231, 246 y 220 frente a 249 en P+1.
- Las 16 de H1 y S1 siguen sobre pelo o manga, con luma entre 41 y 92.

**Caja** base `(2100, 300, 3500, 2247)`, con coordenadas inclusivas (y = 2247 es la última fila).
Tres familias separadas:

| ID | Familia | Caja | Válida |
|---|---|---|---|
| `T+15+0` | traslación | (2115, 300, 3515, 2247) | sí |
| `T-15+0` | traslación | (2085, 300, 3485, 2247) | sí |
| `T+0-15` | traslación | (2100, 285, 3500, 2232) | sí |
| `T+0+15` | traslación | (2100, 315, 3500, 2262) | **no**: sale de la imagen; nunca se recorta, porque recortar mezclaría traslación y contracción |
| `E15` | expansión | (2085, 285, 3515, 2247) | sí; `y2` queda fijo porque ya toca el borde (anotado) |
| `C15` | contracción | (2115, 315, 3485, 2232) | sí |

## 6. Métricas (solo informan; se leen después del desciegue)

- **Estabilidad bajo perturbación.** Por candidata (protocolo, índice), frente a la misma
  candidata perturbada. Etiquetas, en orden de prioridad:
  - `NOT_EVALUABLE`: ninguna perturbación válida;
  - `CONFLICT`: el cribado O* cambia, es decir, quién entra depende de 15 px;
  - `UNSTABLE`: IoU global mínimo < 0,90;
  - `STABLE`: en otro caso.

  Resumen por familia: la peor etiqueta. Secundaria: el IoU dentro de la caja de contacto.
- **Estabilidad del recíproco.** Entre las 3 semillas `R-corrections`, con la misma regla de la
  sonda v1; `CONFLICT` si cambia el cribado K*, es decir, si la chica entra en R. Se usan los
  sentinelas invertidos: O* se conservan, y K* y B* se excluyen.
- **Propiedad (ChatGPT 002 §4).** Por cada candidata T de la chica frente a `R_ref`, dentro de la
  caja de contacto. `R_ref` es la semilla R con más O* cubiertos; en empate, el menor índice.
  - Razón: `|T∩R| / min(|T|, |R|)`.
  - `DISJOINT` ≤ 0,02 · `MARGINAL` · `SHARED` ≥ 0,10 · `NOT_EVALUABLE` si alguna está vacía.
  - También se reporta si T filtra O2/O3 y si R cubre el moño.
  - **Nunca** se usa `T − R` para reparar nada.
- **Tabla de interpretación prerregistrada:**
  - `OWNERSHIP_AMBIGUOUS`: T arrastra el moño y las dos consultas lo reclaman.
  - `BUN_ATTRIBUTED_TO_TARGET_BY_BOTH`: T arrastra el moño y ni pidiendo a la posterior se lo lleva R.
  - `SEPARATION_CONSISTENT_BOTH_WAYS`: T no arrastra el moño y T, R son disjuntas.
  - `NO_INFERENCE`: R no es estable.
  - `MIXED`: cualquier otro caso.

  Es un diagnóstico del prompting y nunca rechaza SAM 2.

## 7. Auditoría ciega y decisión

- **Candidatas ciegas:** las 18 de las ramas +POS, más las de BASE que no se reproduzcan bit a bit.
- **Protocolo:** auditoría v2:
  - el paquete va a ChatGPT **antes** que cualquier resultado;
  - los juicios de Claude se comprometen por hash;
  - `correct_subject` significa identidad por mayoría del área;
  - los agujeros ≥ 1000 px se miden y se clasifican;
  - hay dos preguntas auxiliares: `target_hair_included` y `target_dark_sleeves_included`.
- **Pasa** solo con los cuatro criterios `TRUE` en **las dos llaves**; si discrepan, decide la persona usuaria.
- **Pase lo que pase:**
  - `sam2_rejectable = false`;
  - el resultado habla de esta familia de prompts (ChatGPT 002);
  - el proyecto sigue en `INCONCLUSIVE_A_E0_REQUIRED` y la Fase B, bloqueada.

## 8. Hipótesis prerregistradas

| ID | De | Enunciado | Se cumple si | Se refuta si |
|---|---|---|---|---|
| H‑C1 | Claude (carta 002) | +POS_HAIR recupera el pelo pero vuelve a arrastrar el moño | ≥ 4 de 6 con pelo incluido (ambas llaves) y moño dentro | ≥ 4 de 6 con pelo incluido, `other_person_excluded` TRUE en ambas y sin O2/O3 |
| H‑C2 | Claude (carta 003) | P+1 perturbado **no** es `STABLE` en `point` | alguna de las 3 salidas es `UNSTABLE` o `CONFLICT` | las 3 son `STABLE` |
| H‑G1 | ChatGPT (003) | S1 recupera mangas de forma local, sin tocar la propiedad del moño | ≥ 4/6 con mangas (ambas llaves) y ≤ 2/6 empeoran O frente a su BASE | ≥ 4 sin mangas o ≥ 4 con fuga nueva |
| H‑G2 | ChatGPT (003) | el recíproco no cambia de propietario grueso entre semillas | `STABLE` o `UNSTABLE` | `CONFLICT` (`NOT_EVALUABLE`: indeterminada) |
| H‑G3 | ChatGPT (003) | el moño se reclama desde las dos consultas | alguna T con fuga O2/O3, R cubre O2/O3 y `SHARED` | R cubre O2/O3 y todas las T con fuga son `DISJOINT` |
| H‑G4 | ChatGPT (003) | +POS_HAIR+SLEEVE recupera pelo y mangas a la vez en ≥ 1 | ≥ 1/6 (ambas llaves) | 0/6 |

Límite (ChatGPT 002): aunque H‑C1 se cumpla, solo muestra que esta familia de prompts no resuelve
la ambigüedad. No distingue entre prompting, representación de SAM 2, ambigüedad de la imagen o
su interacción.

## 9. Salida esperada del cuaderno (cuando exista)

Un ZIP `PRAGMA_AEM1v13_<run_id>_PENDING_EXTERNAL_AUDIT.zip` con:

- la configuración, con el SHA‑256 de este prerregistro;
- el manifiesto y el informe;
- 36 PNG alfa (BASE, +POS y RECIPROCAL);
- `aem1_perturbaciones.npz`, con 174 máscaras en *packbits* y un SHA‑256 por máscara en el manifiesto.

Ninguna máscara compuesta.
