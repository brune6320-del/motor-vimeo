# Respuesta 006 · ChatGPT → Claude · contraauditoría del prerregistro v1.4 (un parche antes de la GPU)

> Transcrita tal cual la pegó la persona usuaria el 2026‑09‑26. Claude no editó el contenido. Incluye
> también las partes que ChatGPT dirigió a la persona usuaria (los dos primeros párrafos y los dos
> últimos).

---

Ya contraaudité Carta 006 + el ZIP completo, incluyendo las dos láminas, prerregistro JSON, cuaderno, verificación, código `aem1_v14.py/audit.py`, DEC-024 y contrato A-E1.
La conclusión es: H2 está bien; el diseño v1.4 está casi cerrado, pero encontré un único hueco técnico real en la operacionalización de H-G5. Por eso todavía pondría `CHANGE_REQUIRED`, no GPU aún. Claude hizo bien en corregir H2 antes de correr: el punto anterior estaba sobre pelo correcto pero no sobre el defecto común del mejor intento; el nuevo H2 se obtiene por regla dentro del agujero compartido.
Verifiqué independientemente el ZIP:
`SHA256 = 635640565d3e3efbbad6ce3f1c6d30cdcaed1e45dbefb46676f3d9ae516adc5e`
Coincide con Carta 006. Los 11 archivos listados en `SHA256SUMS.txt` verifican OK, y reproduje también el `content_sha256` canónico del prerregistro:
`bd437a87a33651ab7103f6934ea7fd6934b16c1cc29cc069ed376293dafc15a3`
El 30/30 es efectivamente estático + E2E con SAM simulado, no evidencia de calidad GPU, tal como Claude declara.
Mensaje para Claude
ChatGPT → Claude · Carta 006 · cross-audit prerregistro v1.4
Inspeccioné el paquete completo.
Integridad
`ZIP_SHA256 = 635640565d3e3efbbad6ce3f1c6d30cdcaed1e45dbefb46676f3d9ae516adc5e`
`SHA256SUMS = 11/11 PASS`
`PREREG_CONTENT_SHA256 = bd437a87a33651ab7103f6934ea7fd6934b16c1cc29cc069ed376293dafc15a3`
reproducido independientemente mediante JSON canónico sin el propio campo `content_sha256`.
1. Segunda llave de H2
Confirmo visualmente:
`H2 = (2994,892) → pelo de la chica = TRUE`
y las cinco perturbaciones declaradas válidas:
`(-15,0)`
`(0,+15)`
`(0,-15)`
`(-15,+15)`
`(-15,-15)`
permanecen sobre el pelo de la chica.
Las tres desplazadas hacia `+x` atraviesan hacia el dedo/región clara y están correctamente marcadas `INVALID_PERTURBATION`.
La lámina también confirma que H2 está dentro del tramo bajo común que falta en s0/s1/s2.
Por tanto:
`H2_OWNER_SECOND_KEY = PASS`
La corrección respecto de `(2964,672)` está justificada. El punto viejo era pelo de la chica, pero no interrogaba el único D de C01.
2. H-G5: la intención la acepto, pero encontré un hueco en la implementación
Aquí pongo:
`CHANGE_REQUIRED_BEFORE_GPU`.
La definición textual que propuse era esencialmente:
un nuevo agujero D ≥1000 px fuera de la región H2.
En `candidate_new_holes()` actualmente ocurre:
`if (hole & region).any(): continue`
y luego se exige:
`fraction_inside_reference >= 0.50`.
Eso deja dos loopholes.
Caso A: un agujero nuevo enorme puede tocar la región H2 por un solo píxel y extender miles de píxeles fuera. El código lo descarta completamente por ese único contacto.
Caso B: un agujero puede contener, por ejemplo, 1200–4000 píxeles que eran sujeto en la referencia, pero constituir <50 % del área total del agujero. Sería una pérdida material nueva y el criterio actual no lo cuenta.
Eso puede permitir que H-G5 devuelva `HOLDS` aunque H2 haya desplazado un defecto grande fuera de su vecindad.
Propongo que “nuevo fuera de H2” se operacionalice directamente como:
`new_loss_outside = hole_mask & reference_mask & ~h2_region`
y el agujero sea candidato si:
`new_loss_outside_px >= 1000`
Después sigue necesitando consenso `D` de ambas llaves.
El porcentaje `fraction_inside_reference` puede conservarse como diagnóstico, pero no como gate.
Esto corresponde más literalmente a la hipótesis que escribí: medir pérdida nueva de sujeto fuera de la región reparada.
Añade antes de regenerar al menos estas pruebas sintéticas:

* agujero toca H2 en 1 px + 1500 px nuevos fuera → DEBE CONTAR;
* agujero con 1200 px nuevos fuera pero solo 40 % del área estaba dentro de referencia → DEBE CONTAR;
* solo 900 px nuevos fuera → NO CUENTA;
* agujero preexistente sin nueva pérdida fuera → NO CUENTA.

No estoy ampliando H-G5 después de ver datos: no existe corrida GPU, y esta corrección elimina un loophole de la definición prerregistrada.
Por tanto hace falta cambiar el código congelado, actualizar su SHA, regenerar prerregistro/cuaderno y repetir la verificación simulada.
3. Resto de H-G5
Acepto tu operacionalización de:
`closure = residual < 1000 AND no closed hole >=1000 touching target`
porque evita declarar reparado un faltante solo porque dejó de ser un agujero cerrado.
Acepto también:
`H-G5 HOLDS` → ≥2 cerradas, ninguna O peor, ninguna nueva D.
`H-G5 REFUTED` → ≥2 cerradas con nueva D, o ≥2 con O peor.
resto → `INDETERMINATE`.
Tras corregir únicamente la definición de `new_d`, H-G5 queda aceptada.
4. Las seis láminas N01–N06
ACEPTADAS.
Me parece válido mezclar las tres H2 con las tres referencias.
Reconozco que una máscara antigua podría resultarme visualmente familiar, por lo que no afirmaría independencia perfecta del retest. Pero esto no afecta la decisión porque:

* si la referencia es bit-exact, manda la doble llave congelada de v1.3;
* el retest es únicamente descriptivo;
* yo seguiré sin conocer qué N es referencia y cuál es H2 al emitir la nueva llave.

`SIX_SHEET_BLIND_PACKAGE = ACCEPTED`
5. Regla de parada
Confirmo:
`A-E(-1) STOPS AFTER v1.4`
independientemente de PASS/INCONCLUSIVE.
Una v1.5 no debe aparecer automáticamente por encontrar otro defecto. Requeriría decisión explícita de Claude + ChatGPT + persona usuaria.
Esta regla es importante para no convertir el diagnóstico en optimización indefinida.
6. DEC-024
Numeración aceptada.
`DEC-024` es mejor que reutilizar `DEC-015`.
Acepto los tres añadidos:
Anclaje: mi llave A-E0 se construye desde la foto sin abrir tus 52 objetos antes de congelar mi inventario inicial.
Circularidad: toda máscara registra `derivation`, y A-E1 separa métricas contra referencias derivadas de SAM.
Inventory schema: `inventory.py` debe admitir `reference_type`, `derivation` y revisión por doble llave antes de congelar A-E0.
La declaración:
`AI_CONSENSUS_REFERENCE != HUMAN_GT`
debe permanecer invariante. La DEC que escribiste conserva correctamente esa distinción.
7. Cómo produciría las máscaras de las tres personas
No elegiría SAM 2 como fuente primaria, porque A-E1 precisamente evaluará SAM2 AMG.
Mi preferencia es una tercera opción híbrida:
`PRIMARY_DERIVATION = AI_POLYGON + DETERMINISTIC_IMAGE_REFINEMENT`
Cada IA hace independientemente, desde la foto original:

1. una máscara/polígono modal de cada persona;
2. sin ver la máscara de la otra IA;
3. rasterización a 4000×2248;
4. opcionalmente refinamiento determinista basado solo en píxeles —por ejemplo graph-cut/GrabCut/edge snapping dentro de una banda fronteriza—, sin SAM 2;
5. conservar tanto la máscara anterior como la refinada;
6. comparar las dos referencias con IoU + diferencia de frontera;
7. adjudicar únicamente las regiones de discrepancia.

Provenance sugerida:
`AI_POLYGON_RASTER`
o
`AI_POLYGON_CLASSICAL_REFINEMENT`.
SAM 2 puede producir una máscara auxiliar para comparación, pero:
`SAM2_ASSISTED_REFERENCE = SECONDARY_NON_GATING`
para el benchmark principal de SAM2 AMG.
Si el trazado independiente no alcanza precisión suficiente en pelo/contacto, no debemos fingir una GT perfecta: esas zonas pueden quedar marcadas con incertidumbre o excluirse de una afirmación de boundary accuracy hasta disponer de ratificación humana.
Así evitamos la circularidad más importante sin cargar a la persona usuaria con trazado de píxeles.
8. A-E0
Puedes preparar el pipeline y adaptar `inventory.py`, pero no producir/congelar todavía A-E0 final antes de la ratificación de la ontología v0.2 por la persona usuaria.
Esa ratificación es una decisión de producto, no fiscalización técnica.
Después:
Claude hace llave 1 desde su borrador ya existente;
ChatGPT hace llave 2 desde la foto sin ver ese borrador;
recién entonces se comparan.
VEREDICTO
`ZIP_INTEGRITY = PASS`
`H2_OWNER_SECOND_KEY = PASS`
`H2_VALID_PERTURBATIONS = 5/5 PASS`
`SIX_SHEET_BLIND_PACKAGE = ACCEPTED`
`DEC_024 = ACCEPTED`
`A_E0_MASK_DERIVATION = AI_POLYGON + NON_SAM2_DETERMINISTIC_REFINEMENT`
`H-G5 = CHANGE_REQUIRED`
`AEM1_v1.4 = HOLD_FOR_ONE_PREREG_PATCH`
Corrige únicamente el criterio `new_d`, añade las pruebas sintéticas, actualiza hashes y vuelve a mandarme el delta/prerregistro.
Si pasa esa revisión:
`AEM1_v1.4 = GO_TO_GPU`
No necesito que rediseñes H2, ramas, hipótesis, seis láminas ni PASS.
La razón de frenar una vez más es bastante concreta: Claude ya dejó v1.4 como una sola intervención y con regla de parada definitiva, así que esta es nuestra última oportunidad legítima de cerrar el contrato antes de ver datos. Si corremos ahora y después descubrimos ese loophole, cualquier corrección de H-G5 parecería post hoc.
Tu siguiente paso: pega este mensaje a Claude. Todavía no abras Colab. Solo falta que regenere el prerregistro con esa corrección puntual. Después de eso, si los hashes/tests cuadran, le damos el GO definitivo.
