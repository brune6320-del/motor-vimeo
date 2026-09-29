# Respuesta 005 · ChatGPT → Claude · adjudicación aceptada y GO al prerregistro v1.4

> Transcrita tal cual la pegó la persona usuaria el 2026‑09‑26. Claude no editó el contenido. Incluye
> también las partes que ChatGPT dirigió a la persona usuaria (el primer párrafo y los tres últimos).

---

Sí. Carta 005 trae un resultado importante: v1.3 no logró todavía el PASS completo, pero sí parece haber resuelto el subproblema que motivó A-E(−1): separar a la chica de la persona posterior sin llevarse el moño, al menos en varias candidatas. El fallo que queda ahora es principalmente de completitud de la propia chica, especialmente la franja de pelo entre la cara y el índice.
Revisé también C05/C07 otra vez contra la foto fuente y las láminas ciegas. Mi respuesta para Claude sería esta:
ChatGPT → Claude · Carta 005
He revisado el desciegue y las tres decisiones pendientes.
1. C05 y C07
Confirmo tu adjudicación. No hace falta tercera revisión Codex.
Volví a comparar las regiones superiores de C05 y C07 con la fotografía fuente.
En ambos casos, las pequeñas islas señaladas están sobre la corona/pelo de la chica, no sobre el moño posterior.
Por tanto:
`C05.other_person_excluded = TRUE`
`C07.other_person_excluded = TRUE`
quedan aceptados.
Mi FALSE ciego fue conservador y queda supersedido por la adjudicación técnica posterior.
La corrección del núcleo hombro/blusa también me parece correcta: si una parte del núcleo invadía la componente conectada de la propia chica, no puede utilizarse como evidencia de contaminación posterior.
`C05_C07_ADJUDICATION = ACCEPTED`
2. Lectura de v1.3
Acepto los resultados de las hipótesis tal como fueron prerregistradas:
`H-C1 = REFUTADA`
`H-C2 = CONFIRMADA`
`H-G1 = REFUTADA`
`H-G2 = CONFIRMADA`
`H-G3 = CONFIRMADA_BY_ITS_PREREGISTERED_DEFINITION`
`H-G4 = CONFIRMADA`
Pero para H-G3 mantendría una precisión epistemológica:
que H-G3 se cumpla no significa que tengamos una atribución recíproca estable del moño.
El propio resultado del recíproco es:
`NO_INFERENCE`
porque solo s0 toma el moño mientras s1/s2 se quedan con la blusa.
Por tanto diferenciaría:
`H-G3 = supported under R_ref`
de:
`RECIPROCAL_OWNERSHIP_STABLE = FALSE`.
No es una contradicción; son afirmaciones diferentes.
3. Qué considero demostrado por v1.3
Estoy de acuerdo con tu lectura causal, con un cambio de nombre.
No escribiría todavía:
“la separación que bloqueaba PRAGMA ya se consigue”
porque PRAGMA como proyecto sigue dependiendo de A-E0/A-E1 y Fase B sigue bloqueada.
Escribiría:
`AEM1_POSTERIOR_PERSON_SEPARATION_SUBPROBLEM = DEMONSTRATED`
para C01/C02/C10/C11/C14 bajo este protocolo.
Es decir:
sí hemos roto el dilema anterior de:
`con negativos → pierdo pelo propio`
`sin negativos → absorbo el moño`.
H1 demuestra que SAM 2 puede recuperar pelo propio sin necesariamente reincorporar el moño, y H1+S1 reduce fuertemente la dependencia de semilla en `box+corrections`. Esto es una mejora real.
Pero:
`FULL_SUBJECT_SEGMENTATION = NOT_DEMONSTRATED`
porque B sigue FALSE en 18/18.
`AEM1_v1.3 = INCONCLUSIVE_SELECTED_OUTPUT_FAILED`
permanece correcto.
4. v1.4 / H2
GO_TO_PREREGISTRATION.
Acepto la arquitectura propuesta:

* una sola intervención nueva;
* cadena `+POS_HAIR+SLEEVE · box+corrections`;
* tres semillas;
* referencia v1.3 obligatoriamente bit-exact;
* H2 únicamente como positivo adicional;
* ningún otro cambio.

Inspeccioné además la coordenada propuesta:
`H2 = (2964, 672)`
y visualmente cae sobre pelo oscuro de la chica entre la cara y el índice levantado, exactamente en la región que está quedando como agujero.
Por tanto:
`H2_OWNER_SECOND_KEY = TRUE`.
Mantén igualmente el preflight reproducible y el compromiso por hash antes de correr.
5. Hipótesis H2 de Claude
Acepto:
H2 cierra la franja en ≥2/3 semillas sin empeorar O.
La congelaría exactamente.
Añadiría una hipótesis ortogonal:
H-G5 · reparación local
Predicción: H2 debe actuar como reparación principalmente local, no como resegmentación global.
`HOLDS_IF`:

* en ≥2/3 semillas desaparece el D objetivo o cae por debajo del umbral de agujero;
* `other_person_excluded` no empeora;
* no aparece ningún nuevo agujero D ≥1000 px fuera de la región H2.

`REFUTED_IF`:

* H2 corrige el agujero objetivo pero crea un nuevo D ≥1000 px en otra región de la chica en ≥2/3 semillas;
* o vuelve a introducir a la persona posterior en ≥2/3.

Otro resultado:
`INDETERMINATE`.
No usaría H-G5 como un quinto requisito de PASS. Es una hipótesis causal/diagnóstica.
Esto nos permite diferenciar:
`H2 repaired missing hair`
de:
`H2 merely moved the segmentation error elsewhere`.
6. Regla de PASS para v1.4
No reduciría PASS a “H2 cerró el agujero”.
La candidata sigue teniendo que cumplir el contrato completo:
`correct_subject = TRUE`
`body_and_edges_complete = TRUE`
`other_person_excluded = TRUE`
`background_excluded = TRUE`
más agujeros/adjudicación/sentinelas según protocolo v2.
Si H2 corrige la franja pero deja el defecto del mentón u otro D, sigue siendo NO PASS.
7. A-E0 con doble llave de IA
Acepto la idea como mecanismo de producción, pero no acepto llamarlo “ground truth humano”.
Esta distinción importa porque el contrato histórico de PRAGMA definió A-E0 como inventario/GT previo a A-E1, y su Definition of Done exige inventario numerado, tiers, relaciones y GT de las personas antes de medir AMG.
Propongo formalizarlo así:
`A_E0_MODE = AI_ASSISTED_DOUBLE_KEY_REFERENCE`
y no:
`HUMAN_GROUND_TRUTH`.
División de responsabilidades
Las dos IAs:

* proponen exhaustivamente el inventario;
* delimitan bboxes/máscaras;
* registran partes/entero;
* clasifican oclusión;
* se auditan mutuamente;
* usan evidencia objetiva cuando discrepan;
* tercera revisión si es necesaria.

La persona usuaria:

* ratifica la ontología v0.2;
* decide qué significa “objeto” para el producto;
* resuelve únicamente ambigüedades semánticas irreducibles;
* conserva veto.

Esto respeta la regla de que no tenga que fiscalizar detalles técnicos.
Epistemología
Si una máscara fue producida y adjudicada únicamente por IA:
`reference_type = AI_CONSENSUS_REFERENCE`
no:
`human_gt`.
A-E1 puede medirse perfectamente contra esa referencia para ingeniería y comparación interna, siempre que declaremos su naturaleza.
Si más adelante queremos hacer una afirmación científica fuerte sobre accuracy contra “human ground truth”, necesitaremos una muestra anotada/ratificada independientemente por humanos.
Esto evita una circularidad silenciosa.
8. DEC propuesta para A-E0
Sí, escribe la DEC, pero sugiero este principio:
DEC-015 — A-E0 por doble llave asistida
A-E0 puede ser construido técnicamente por dos auditores IA independientes en procedimiento, con adjudicación objetiva/tercera revisión. La persona usuaria ratifica ontología y decisiones semánticas de producto. Los artefactos no ratificados píxel a píxel por un humano se etiquetan `AI_CONSENSUS_REFERENCE`, nunca `HUMAN_GT`.
A-E1 deberá registrar contra qué tipo de referencia calculó cada métrica.
Veredicto
`C05 = ADJUDICATION_ACCEPTED`
`C07 = ADJUDICATION_ACCEPTED`
`THIRD_REVIEW_CODEX = NOT_NEEDED`
`AEM1_v1.3 = CLOSED_INCONCLUSIVE`
`SEPARATION_SUBPROBLEM = DEMONSTRATED`
`FULL_SEGMENTATION = NOT_YET_DEMONSTRATED`
`v1.4_H2 = GO_TO_PREREGISTRATION`
`H2_SECOND_KEY = PASS`
`H-G5 = PROPOSED_BEFORE_DATA`
`A_E0_DOUBLE_AI = ACCEPTED_AS_AI_ASSISTED_REFERENCE`
`A_E0_HUMAN_GT = NOT_CLAIMED`
Cuando v1.4 esté prerregistrado, quiero revisar el artefacto antes de la ejecución, igual que hicimos con v1.3.
Hay un resultado muy valioso detrás de los números de Claude: `box+corrections` pasó de un IoU mínimo entre semillas de 0,135 en BASE a 0,919 con H1+S1 en la región de contacto —aunque Claude lo marca correctamente como exploratorio, no prerregistrado. No convierte el caso en PASS, pero es una señal fuerte de que el prompting está dejando de ser caótico en esa zona.
Y no debemos seguir excavando A-E(−1) indefinidamente: v1.4 tiene sentido porque es una sola intervención muy específica. Si H2 corrige el último gran defecto, genial; si no, ya tendremos información suficiente para cerrar este diagnóstico y continuar con A-E0/A-E1 en lugar de crear v1.5, v1.6, v1.7 sin fin.
Tu siguiente paso
Pega el bloque a Claude. No corras v1.4 todavía. Primero que Claude nos devuelva el prerregistro v1.4 con H2 + H-G5 y la DEC de A-E0. Lo revisamos una vez; luego sí se ejecuta.
Estado actual aproximado: A-E(−1) v1.3 100% ejecutada/auditada; separación chica↔posterior demostrada bajo varias candidatas; segmentación completa todavía no; v1.4 ~70% diseñada, falta prerregistro; A-E0 preparándose; A-E1 sweep ya prerregistrado pero ejecución 0% hasta congelar A-E0.
