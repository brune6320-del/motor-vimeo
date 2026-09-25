# Protocolo de auditoría ciega · A‑E(−1) · v2 (para la corrida v1.3)

> **Escrito y congelado antes de la corrida v1.3** (2026‑09‑25), sin datos de esa corrida.
> Sustituye a v1 solo para corridas nuevas; la corrida `20260925T062504Z_256dba9f` sigue juzgada
> con v1. Responde a ChatGPT 002 (cambio de protocolo, crítica de v1.3) y a la comparación A–L de
> la carta 003. Diseño del experimento: [`aem1/PRERREGISTRO_A-E-menos-1_v1_3.json`](../aem1/PRERREGISTRO_A-E-menos-1_v1_3.json).

## 1. Qué cambia respecto de v1 y por qué

| Cambio | Motivo (evidencia) |
|---|---|
| Ninguna carta previa revela resultados, recuentos, patrones por familia ni «la mejor» | ChatGPT 002: la carta 002 contaminó parcialmente la segunda llave |
| Los juicios de Claude se comprometen **por hash** antes de enviar nada y se publican después | Con el repositorio público, publicar los juicios crudos antes que la segunda llave la contaminaría |
| La segunda llave devuelve el SHA‑256 del paquete que juzgó | En la ronda 1 la identidad solo se sostenía por la cadena de custodia |
| `correct_subject` = **identidad** (¿de quién es la mayoría del área?); la **extensión** va solo en `body_and_edges_complete` | Comparación A–L: κ = 0,25 en este criterio porque cada llave ponía un umbral de extensión no escrito |
| Los agujeros cerrados ≥ 1000 px se **miden** y se muestran numerados; el auditor clasifica cada uno | F: un UNSURE mío y un TRUE de ChatGPT que la medición refutó (2 agujeros de 2540 y 1885 px) |
| Mejor intento: desempate por sentinelas KEEP antes que por etiqueta | Con v1 empataban A y seis candidatas «solo prenda» |

## 2. Orden de los hechos (cada paso deja huella en git antes del siguiente)

1. **Antes de la corrida:** este protocolo y el prerregistro v1.3, en git.
2. **Llega el ZIP:** Claude verifica solo la integridad y el congelado (manifiesto, hashes, commit,
   checkpoint y foto). **No abre máscaras ni lee sentinelas ni métricas.** Todo lo automático se
   escribe en `local/` sin leerlo.
3. **Paquete ciego:** Claude genera las láminas y sella el mapeo. A git van solo el SHA‑256 del mapeo,
   el de cada lámina y el del paquete.
4. **Envío a ChatGPT:** el paquete y su `LEEME.md`, **nada más**. La carta que lo acompaña no dice si
   alguna pasó, cuántas fallan ni de qué manera, qué rama rindió mejor ni ningún agregado.
5. **Primera llave:** Claude juzga a ciegas y compromete en git **solo el SHA‑256** de su JSON de juicios crudos.
6. **Segunda llave:** ChatGPT devuelve su tabla o JSON y el SHA‑256 del paquete que juzgó. Claude la
   archiva tal cual en `dialogo/`.
7. **Desciegue:** Claude publica sus juicios crudos (deben coincidir con el hash del paso 5), abre el
   mapeo, lee las métricas automáticas, compara las dos llaves y **después** escribe la carta con resultados.

Si un paso se salta o se invierte, la corrida se registra como `BLIND_PROTOCOL_BROKEN` y sus
juicios valen solo como revisión no ciega.

## 3. Láminas

- Etiquetas `C01`…`Cnn` por permutación aleatoria (`secrets`); el mapeo se sella en `local/`.
- Por candidata: vista completa reducida y cinco primeros planos a resolución nativa. Los
  primeros planos son los mismos de v1: cabeza y pelo recogido, contacto posterior, mano levantada,
  mano colgante y costado derecho.
- Lo excluido va oscurecido y el borde de la máscara en magenta.
- **Nuevo:** cada agujero cerrado ≥ 1000 px (componente del complemento que no toca el borde de la
  imagen) se contornea en cian con un número. La lámina lleva la lista numerada (número, área en
  px, caja) y nada más.
- Sin rama, protocolo, semilla, score, área de la máscara ni sentinelas.

## 4. Criterios (definiciones fijas)

Cada criterio es `TRUE`, `FALSE` o `UNSURE`. **`UNSURE` cuenta como `FALSE`** para aceptar. Toda
respuesta que no sea `TRUE` exige una nota con la región y el defecto.

| Criterio | `TRUE` solo si |
|---|---|
| `correct_subject` | **más de la mitad del área** de la máscara está sobre la chica del frente: cuerpo, pelo, ropa o accesorios. Una máscara parcial, por ejemplo solo una prenda o un botón, es `TRUE`: su extensión se juzga en el criterio siguiente. Es `FALSE` si la mayoría del área está sobre otra persona o sobre el fondo |
| `body_and_edges_complete` | incluye la cabeza y el pelo visibles, la cara, la mano en V con sus dedos, ambos brazos o mangas, la mano que cuelga y el torso hasta el borde inferior, sin faltantes de contorno ≥ 1000 px. **Cada agujero numerado** se clasifica como `D` (defecto: falta material de la chica) o `L` (legítimo: se ve fondo a través del hueco); un solo `D` basta para `FALSE` |
| `other_person_excluded` | no incluye pelo recogido, pelo, blusa floral ni hombro oscuro de la persona posterior, salvo el borde ambiguo de ≤ 5 px |
| `background_excluded` | no incluye pared, cuadros, mesa, vasitos ni silla, salvo el borde de ≤ 5 px; sin islas de fondo ≥ 500 px |

**Preguntas auxiliares (no deciden; miden el efecto causal de las ramas):**

- `target_hair_included`: la mayor parte del pelo visible de la chica está dentro de la máscara.
- `target_dark_sleeves_included`: la mayor parte de las dos mangas oscuras está dentro, sin
  perforaciones grandes.

**Conciliación con la evidencia automática, después del juicio visual:**

- si falla un sentinela KEEP, `body_and_edges_complete` no puede ser `TRUE`;
- si falla un O*, `other_person_excluded` no puede ser `TRUE`;
- si falla un B*, `background_excluded` no puede ser `TRUE`.

Toda corrección queda anotada.

## 5. Reglas de decisión

1. Una candidata **pasa** si el ZIP es íntegro, la corrida es `REAL_GPU` y **las dos llaves** marcan
   los cuatro criterios `TRUE` tras la conciliación.
2. Si una llave la da por aprobada y la otra no, queda en `DISCREPANCY`: se documenta con evidencia
   y decide la persona usuaria (DEC‑019‑P). Mientras tanto no pasa.
3. **Si al menos una pasa:** `SEPARATION_DEMONSTRATED_UNDER_FIXED_AEM1_PROTOCOL`, con la rama, el
   protocolo y la semilla de cada una.
   - Si su rama tiene perturbación medida, se añade el calificativo de estabilidad del prerregistro.
   - Si no la tiene: `ROBUSTNESS_NOT_MEASURED`.
4. **Si ninguna pasa:** `INCONCLUSIVE_SELECTED_OUTPUT_FAILED`.
   - Mejor intento: la candidata con menos criterios no `TRUE`, sumando las dos llaves.
   - Desempates: más sentinelas KEEP cumplidos; después, orden de etiqueta (la permutación es
     aleatoria y está sellada).
5. **Nunca se usa el score.** Ninguna máscara compuesta, como `objetivo − posterior`, se evalúa.
6. Pase lo que pase, `sam2_rejectable = false` en v1.3. El resultado habla de **esta familia de
   prompts** (ChatGPT 002). El proyecto sigue en `INCONCLUSIVE_A_E0_REQUIRED` y la Fase B, bloqueada.

## 6. Perturbación y prompt recíproco

Solo informan y no pasan por las láminas ciegas. Sus métricas y etiquetas están en el prerregistro
(`STABLE`, `UNSTABLE`, `CONFLICT`, `NOT_EVALUABLE`; `DISJOINT`, `MARGINAL`, `SHARED`). **Se leen
después del desciegue** (paso 7), porque leerlas antes revelaría resultados.

## 7. Qué se archiva

- **En git, sin nada derivado de la foto:** este protocolo; el prerregistro; los hashes de los
  pasos 3 y 5; la carta de ChatGPT tal cual; los juicios crudos de las dos llaves; la tabla
  desciegada; las métricas automáticas; la comparación de llaves y el veredicto.
- **En local, y compartibles en privado:** las láminas, el mapeo y el ZIP.
- **Identidad de los auditores:** "Claude Code" (con el enlace de sesión de los commits) y "ChatGPT".
  El identificador exacto del modelo no se escribe en el repositorio.
