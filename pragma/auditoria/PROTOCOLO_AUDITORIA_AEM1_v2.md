# Protocolo de auditoría ciega · A‑E(−1) · v2 (para la corrida v1.3)

> **Escrito y congelado antes de la corrida v1.3** (2026‑09‑25), sin datos de esa corrida.
> **Revisión 1** (2026‑09‑25, también antes de cualquier corrida v1.3), tras la contraauditoría de
> ChatGPT 003 (`dialogo/003_chatgpt_a_claude.md`):
> - las discrepancias van a **adjudicación técnica**, no a la persona usuaria (§5.2);
> - BASE usa una **referencia normalizada**, no una doble llave heredada (§5.7).
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
| **(rev. 1)** Discrepancia → adjudicación técnica; la persona usuaria conserva el veto | ChatGPT 003: la persona usuaria no fiscaliza lo que una IA puede verificar (DEC‑018‑P) |
| **(rev. 1)** BASE bit a bit → `BASE_V2_REFERENCE`, no «doble llave heredada» | ChatGPT 003: una máscara idéntica no equivale a un juicio emitido con el protocolo nuevo |

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
2. **Discrepancia → adjudicación técnica** (rev. 1). Si las llaves difieren en un criterio de una
   candidata, se sigue este orden y se documenta cada paso:
   1. **Evidencia objetiva**, cuando el criterio es medible: agujeros numerados, sentinelas, área
      dentro de una referencia juzgada por ambas llaves, borde de ≤ 5 px. Si la medición decide,
      se aplica.
   2. **Tercera revisión independiente**, si no hay medición que decida. Otra IA sin contexto
      recibe solo la lámina y su `LEEME`, sin cartas ni juicios; por ejemplo, el hilo de Codex o
      una sesión nueva. Decide la mayoría de las tres.
   3. **Adjudicación conjunta documentada** Claude + ChatGPT, si la tercera revisión no es posible
      o responde `UNSURE`. Si siguen sin acuerdo, se aplica la regla conservadora: la celda cuenta
      como no `TRUE`, la candidata no pasa y queda `UNRESOLVED` con ambas posiciones escritas.

   Mientras la adjudicación no termina, la candidata no pasa. La persona usuaria conserva
   **siempre el veto** (`USER_VETO = TRUE`). Solo se le consultan cuestiones **semánticas
   irreducibles** (por ejemplo, qué cuenta como parte de la chica), nunca píxeles ni bordes, salvo
   que ella quiera.
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
7. **BASE y la corrida 1** (rev. 1):
   - Si una candidata BASE de v1.3 reproduce **bit a bit** su máscara de la corrida 1, su
     referencia es
     [`BASE_V2_REFERENCE.json`](aem1_20260925T062504Z_256dba9f/BASE_V2_REFERENCE.json).
   - Esa tabla es la adjudicación ya archivada, normalizada a las definiciones de §4: B y D pasan
     a `correct_subject = TRUE` porque el 100 % de su área cae dentro de A.
   - Se llama **referencia normalizada y adjudicada**, no doble llave v2.
   - Las preguntas auxiliares quedan `NO_JUZGADO_V1`.
   - Lo que no se reproduzca bit a bit vuelve al paquete ciego.

## 6. Perturbación y prompt recíproco

Solo informan y no pasan por las láminas ciegas. Sus métricas y etiquetas están en el prerregistro
(`STABLE`, `UNSTABLE`, `CONFLICT`, `NOT_EVALUABLE`; `DISJOINT`, `MARGINAL`, `SHARED`). **Se leen
después del desciegue** (paso 7), porque leerlas antes revelaría resultados.

Con cada etiqueta se archiva siempre el valor continuo (rev. 1):

- la cobertura de cada O* y su distancia al umbral 0,20, para distinguir un cruce marginal de un
  cambio masivo;
- las razones de propiedad `|T∩R|/|T|`, `|T∩R|/|R|` y `|T∩R|/min`;
- en las perturbaciones, el radio L∞ (15 px) y la distancia euclídea (15 px en las axiales y
  21,21 px en las diagonales).

## 7. Qué se archiva

- **En git, sin nada derivado de la foto:** este protocolo; el prerregistro; los hashes de los
  pasos 3 y 5; la carta de ChatGPT tal cual; los juicios crudos de las dos llaves; la tabla
  desciegada; las métricas automáticas; la comparación de llaves y el veredicto.
- **En local, y compartibles en privado:** las láminas, el mapeo y el ZIP.
- **Identidad de los auditores:** "Claude Code" (con el enlace de sesión de los commits) y "ChatGPT".
  El identificador exacto del modelo no se escribe en el repositorio.
