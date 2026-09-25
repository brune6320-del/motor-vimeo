# Protocolo de auditoría ciega · A‑E(−1) · v1

> **Congelado antes de mirar ninguna máscara** (2026‑09‑25). Este archivo se publica en git
> antes de generar las vistas: el historial de commits es la prueba del orden.
> Responde a ChatGPT 001 (R2, R5, P3, P4) y a DEC‑018‑P/019‑P.

## 1. Alcance

- **Corrida:** `20260925T062504Z_256dba9f` · ZIP `PRAGMA_AEM1_20260925T062504Z_256dba9f_PENDING_EXTERNAL_AUDIT.zip` ·
  SHA‑256 `e6bb7a46dacced63f2735154fc2ac6f549a4aa25e0741f28a54d5723fc7d1976` · 4 702 312 bytes.
- **Qué puede producir (P4):** evidencia **de riesgo y de separación bajo un protocolo fijo** en un caso.
  **No** produce verdad de referencia, ni exactitud de segmentación, ni generalización. El proyecto sigue
  `INCONCLUSIVE_A_E0_REQUIRED`; Fase B bloqueada.

## 2. Congelado de SAM 2 (registrado por el propio cuaderno, verificado antes de mirar)

| Campo | Valor |
|---|---|
| `SAM2_GIT_COMMIT` | `2b90b9f5ceec907a1c18123530e92e794ad901a4` (igual que la corrida histórica v4) |
| `MODEL_CONFIG` | `configs/sam2.1/sam2.1_hiera_l.yaml` · `sam2.1_hiera_large` · 224 446 642 parámetros |
| `CHECKPOINT_SHA256` | `2647878d5dfa5098f2f8649825738a9345572bae2d4350a2468587ece47dd318` · 898 083 611 bytes (igual que v4) |
| `PYTORCH_VERSION` / CUDA | `2.11.0+cu128` (build CUDA 12.8) · Python 3.13.15 |
| GPU / dtype | NVIDIA L4 (CC 8.9) · `bfloat16` · pico 1,262 GiB |
| `IMAGE_SHA256` / tamaño | `8f6e3b…529d` · 4000 × 2248 tras EXIF (resolución canónica) |
| Preflight | desviación máxima de luma 0,0 en los 18 parches (tolerancia 3,0) |

Honestidad: esta corrida se ejecutó **antes** de que llegara la condición de ChatGPT
(`SAM2_REAL_RUN = HOLD` hasta congelar). Los campos no se prerregistraron, pero el cuaderno los
registró automáticamente y aquí se verifican **antes** de ver resultados. Las condiciones sobre el
sweep A‑E1 (DEC‑013‑Q, sweep prerregistrado) no aplican a A‑E(−1) y siguen abiertas.

## 3. Procedimiento ciego

1. Las 12 candidatas (3 `point`, 3 `box`, 3 `point+corrections`, 3 `box+corrections`) reciben
   etiquetas `A`–`L` mediante una permutación aleatoria (`secrets`). El mapeo se sella en
   `local/…/sealed_mapping.json` y solo se registra su SHA‑256. El auditor no lo imprime ni lo lee
   hasta guardar los juicios.
2. Por etiqueta se genera una lámina **sin protocolo, semilla, score, área ni sentinelas**:
   - vista completa del sujeto (reducida);
   - cinco primeros planos a resolución nativa (cabeza y pelo recogido, contacto posterior, mano
     levantada, mano colgante, costado derecho), con lo excluido oscurecido y el borde en magenta.
3. Se juzga en orden alfabético de etiqueta, que es aleatorio respecto de los protocolos.
4. Límite declarado: el auditor es el mismo agente que escribió el código (auto‑cegado). Algunas
   formas pueden delatar el protocolo (por ejemplo, un fragmento pequeño). Por eso existe la segunda llave.

## 4. Criterios (definiciones fijas)

Cada criterio es `TRUE`, `FALSE` o `UNSURE`. **`UNSURE` cuenta como `FALSE`** para aceptar.
Toda respuesta que no sea `TRUE` exige una nota con la región y el defecto.

| Criterio | `TRUE` solo si |
|---|---|
| `correct_subject` | la componente principal es la chica del frente (no la persona posterior, ni el señor, ni fondo) |
| `body_and_edges_complete` | incluye la cabeza y el pelo visibles de la chica, la cara, la mano en V con sus dedos, ambos brazos o mangas, la mano que cuelga y el torso hasta el borde inferior; sin agujeros ni faltantes visibles del tamaño de una yema de dedo (≈ 1 000 px) o mayores |
| `other_person_excluded` | no incluye pelo recogido, pelo, blusa floral ni hombro oscuro de la persona posterior, salvo el borde ambiguo de ≤ 5 px |
| `background_excluded` | no incluye pared, cuadros, mesa, vasitos ni silla, salvo el borde de ≤ 5 px; sin islas de fondo ≥ 500 px |

**Conciliación con evidencia automática, tras el juicio visual:** si un sentinela KEEP falla,
`body_and_edges_complete` no puede ser `TRUE`; si falla un O*, `other_person_excluded` no puede
ser `TRUE`; si falla un B*, `background_excluded` no puede ser `TRUE`. Cualquier corrección que
provoque la conciliación queda anotada.

## 5. Sonda de riesgo de contacto (R5, solo se reporta y nunca decide)

- Región de contacto: caja `(2150, 250, 2900, 1300)`, que cubre pelo recogido, coronilla, hombro y blusa posterior.
- Dentro de la caja, IoU entre pares de candidatas:
  - (a) las 3 semillas corregidas de `point`;
  - (b) las 3 de `box`;
  - (c) cada `point+corrections` frente a cada `box+corrections`.
- Etiquetas prerregistradas por grupo, según el IoU mínimo:
  - `STABLE` si ≥ 0,90;
  - `UNSTABLE` si < 0,90;
  - `CONFLICT` si dos candidatas con `other_person_excluded = TRUE` difieren con IoU < 0,75;
  - `NOT_EVALUABLE` si alguna está vacía en la caja.
- Nunca se usa la etiqueta `CORRECT`.
- Pruebas que requieren GPU nueva y quedan pendientes: perturbación del prompt (R5‑3) y prompt recíproco a la persona posterior (R5‑4).

## 6. Reglas de decisión

1. Una candidata **pasa** si el ZIP es íntegro, la corrida es `REAL_GPU` y los cuatro criterios son
   `TRUE` tras la conciliación.
2. **Si al menos una pasa:** `SEPARATION_DEMONSTRATED_UNDER_FIXED_AEM1_PROTOCOL`, indicando qué
   candidatas y qué protocolos pasan. Se registra la que tenga menos defectos anotados; en caso de
   empate, la primera etiqueta alfabética (la permutación es aleatoria y está sellada).
   **Nunca se usa el score.**
3. **Si ninguna pasa:** `INCONCLUSIVE_SELECTED_OUTPUT_FAILED`. Se registra como "mejor intento" la
   de menos criterios `FALSE`; los empates se resuelven igual que en la regla 2. No es un rechazo
   de SAM 2 (`sam2_rejectable = false`).
4. Toda conclusión queda `PENDIENTE DE CONTRAAUDITORÍA` hasta que ChatGPT emita sus propios juicios
   sobre las mismas láminas ciegas (doble llave). Si hay discrepancia, se documenta y decide la
   persona usuaria.

## 7. Qué se archiva

- En git (sin derivados de la foto):
  - este protocolo;
  - el SHA‑256 del mapeo sellado;
  - los juicios crudos por etiqueta, antes de desciegar;
  - las métricas automáticas por etiqueta;
  - la tabla desciegada;
  - la sonda de contacto;
  - el veredicto (`aem1_audit_verdict.json`).
- En local y compartible en privado: las láminas ciegas y el mapeo.
- Identidad del auditor: "Claude Code", con el enlace de sesión de los commits. El identificador
  exacto del modelo no se escribe en el repositorio por política del entorno.
