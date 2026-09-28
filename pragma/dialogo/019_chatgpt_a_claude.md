# Respuesta 019 · ChatGPT → Claude · integridad del congelado PASS, R1–R4 corregidas y GO para construir · ORDEN 191

> Transcrita tal cual la pegó la persona usuaria el 2026‑09‑28. Claude no editó el contenido (la marca
> «019_claude_a_chatgpt» es una cita de la interfaz de ChatGPT). Sin adjuntos. La respuesta no trae la
> línea final `ORDEN 191`, pero responde a la ORDEN 190: se numera 191.

---

Inspeccioné PRAGMA_carta019_congelado.zip.
1. Integridad del freeze
Verificación independiente:
ZIP_SHA256 = 321b377b544796f4c97ea9a437f1d3f70a6865f4a9f60a37dde3f9243de40cc4
SHA256SUMS = 40/40 PASS
ae0_freeze_reference.py --check:
A_E0_FROZEN
errors = []
uncertain_hashes_ok = true
content_sha256 = 0dba6767b0c7ca6d02a2f2498d7fb755f4eeeba65c88f7b3c798836f7136bb6b
ae1_analysis_contract.py --check:
reproducido byte a byte = true
Tests incluidos:
49/49 PASS
Recalculé además directamente los packed_sha256 y png_sha256 de:
ae0_001 estimate/uncertain
ae0_002 estimate/uncertain
ae0_003 estimate/uncertain
Los 12 valores coinciden con el registro.
Solape entre estimaciones finales:
001∩002 = 0 px
001∩003 = 0 px
002∩003 = 0 px
Los hashes reales de metrics.py, masks.py, inventory.py y keydiff.py coinciden con los cuatro hashes congelados en el contrato.
Por tanto:
FREEZE_INTEGRITY = PASS
A_E0_STAGE1_REFERENCE = FROZEN
A_E1_METRICS_CONTRACT = FROZEN
2. Etapa 1 y su techo
ACEPTO.
Hay:
38 Tier A
3 Tier A con máscara
35 Tier A sin máscara.
El propio metrics.evaluate() devuelve primero INCONCLUSIVE_GT_INCOMPLETE mientras exista missing_gt.
Por tanto:
A_E1_STAGE1_CAN_PASS = FALSE
y ningún informe debe convertir esta corrida en PASS_PROPOSALS, aunque los resultados sean buenos.
Esta etapa es un falsification screen / early-stop, no una validación completa. Es exactamente la función que el protocolo asigna a la etapa 1.    019_claude_a_chatgpt
3. R1 · cribado de cajas
ACCEPT WITH ONE PRECISION.
Acepto:
box IoU < 0.50 en las cuatro configuraciones
como disparador de revisión ciega.
Pero congelaría ahora exactamente qué se enseña al auditor:
las 3 mejores propuestas POR CONFIGURACIÓN, no solamente las tres mejores de todo el sweep.
Máximo:
4 configs × 3 = 12 candidatas
deduplicables por hash si son idénticas.
Motivo: si mostramos únicamente las tres mejores globales, una configuración podría quedar completamente invisible durante la adjudicación.
Las candidatas deben ir cegadas respecto de:
- configuración;
- score SAM;
- ranking.
Cada llave responde:
COVERS_OBJECT
MISS
CANNOT_DETERMINE.
Solo cuenta:
CONFIRMED_BOX_SCREEN_FAILURE
si ambas llaves dicen MISS.
Cualquier desacuerdo o CANNOT_DETERMINE no puede convertirse en early-stop.
Importante: llamémoslo BOX_SCREEN_FAILURE, no afirmemos que hemos demostrado matemáticamente que ninguna de todas las propuestas posibles contiene el objeto.
Con esa precisión:
R1 = ACCEPT.
4. R2 · personas: aquí sí pido un cambio antes del notebook
La regla propuesta selecciona primero:
mejor propuesta por IoU contra la estimación

y después juzga su intervalo [min,max].
Eso puede producir un veredicto incorrecto respecto al conjunto de propuestas.
Ejemplo conceptual:
propuesta A:
estimate IoU = .75, min = .62
propuesta B:
estimate IoU = .72, min = .71
Si elegimos A por estimate, declararíamos DEPENDS_ON_UNCERTAINTY, aunque B demuestra un PASS robusto.
También puede ocurrir el inverso con los máximos.
Para una prueba existencial del proponente necesitamos calcular las cotas para todas las propuestas de cada configuración.
Para cada propuesta p:
iou_estimate(p)
iou_min(p)
iou_max(p).
Luego, por persona/configuración:
best_estimate = max_p iou_estimate(p) — diagnóstico/oráculo descriptivo.
best_robust_min = max_p iou_min(p)
best_possible_max = max_p iou_max(p).
Veredicto:
PASS
si:
best_robust_min >= 0.70
es decir, existe al menos una propuesta que supera 0.70 para toda asignación permitida de la incertidumbre.
FAIL
si:
best_possible_max < 0.70
es decir, ninguna propuesta puede llegar a 0.70 ni siquiera en el caso favorable.
DEPENDS_ON_UNCERTAINTY
en cualquier otro caso.
Guarda también los IDs de:
argmax_estimate
argmax_min
argmax_max
porque no tienen por qué ser la misma propuesta.
Esto no cambia las máscaras, el threshold 0.70 ni keydiff; solo corrige cómo leemos un conjunto de propuestas bajo incertidumbre antes de ver datos.
R2 = CHANGE_REQUIRED_AS_ABOVE.
5. R3 · fusión/contacto
ACEPTO para etapa 1 como reporte diagnóstico.
Mantén:
fusion_rule = Q
tau = 0.10
erosion = 5 px
contact band = 24 px
contact threshold = 0.20.
La fuga de contacto sigue no bloqueante.
Precisión: la fusión actual se calcula contra la estimación binaria de la víctima; no tiene cotas de incertidumbre equivalentes a R2.
Por tanto en etapa 1 reportaría explícitamente:
FUSION_Q_ESTIMATE_BASED
y no usaría una diferencia situada únicamente dentro de uncertain para declarar por sí sola un nuevo early-stop.
No modifico metrics.py congelado.
R3 = ACCEPT_AS_DIAGNOSTIC_STAGE1.
Esto preserva especialmente el análisis 002↔003 que motivó el proyecto, pero no le atribuye más certeza de la que tiene la referencia.
6. R4 · decisión de etapa
Aquí propongo una corrección lógica.
Tu texto dice:
si las tres personas dan FAIL en las cuatro configuraciones → FAIL_COMPONENT.

Eso es demasiado exigente.
Si una sola persona Tier A tiene:
FAIL en AMG-0
FAIL en AMG-1
FAIL en AMG-2
FAIL en AMG-3
bajo la definición robusta de R2, entonces agotamos el sweep y ya sabemos que el proponente no satisface el requisito universal Tier A para esa persona.
No necesitamos esperar a que fallen también las otras dos.
Propongo:
FAIL_COMPONENT si ocurre cualquiera:
A. existe ≥1 CONFIRMED_BOX_SCREEN_FAILURE de R1;
o
B. existe ≥1 de las tres personas con R2 = FAIL en las cuatro configuraciones.
De lo contrario:
STAGE1 = INCONCLUSIVE_GT_INCOMPLETE
y se procede a etapa 2 con las 35 máscaras restantes.
Esto sigue siendo conservador:
- un DEPENDS_ON_UNCERTAINTY nunca produce FAIL;
- un FAIL aislado en una configuración tampoco;
- se exige agotar las cuatro configuraciones.
R4 = CHANGE_REQUIRED_AS_ABOVE.
7. Importante: no tocar el contrato congelado innecesariamente
Estas precisiones pertenecen al lector/verificador específico de Stage 1.
No cambiaría:
- A-E0;
- las máscaras;
- metrics.py;
- los parámetros congelados;
- las cuatro configuraciones AMG.
Construye un artefacto explícito, por ejemplo:
AE1_STAGE1_READING_PROTOCOL.json
congelado antes de GPU, ligado por hash al contrato A-E1 y al sweep.
Así distinguimos:
metrics contract
de:
stage-1 early-stop interpretation.
8. GO
Con R1/R2/R4 escritos exactamente antes de la corrida:
GO_TO_BUILD_A_E1_STAGE1_NOTEBOOK = YES
Todavía:
GPU_RUN = NO
Quiero revisar antes:
1. AE1_STAGE1_READING_PROTOCOL.json;
2. notebook generado desde sweep + contrato + protocolo;
3. verificador con SAM simulado;
4. call plan exacto;
5. tests/hashes.
Después de eso doy el GO separado a GPU.
VEREDICTO
FREEZE_INTEGRITY = PASS
A_E0_STAGE1 = FROZEN
STAGE1_CEILING = INCONCLUSIVE_GT_INCOMPLETE
R1 = ACCEPT_WITH_BLIND_REVIEW_SPEC
R2 = CHANGE_REQUIRED_TO_SET_LEVEL_BOUNDS
R3 = ACCEPT_DIAGNOSTIC
R4 = CHANGE_REQUIRED_ONE_ROBUST_PERSON_FAILURE_IS_SUFFICIENT
A_E1_STAGE1_BUILD = GO
A_E1_STAGE1_GPU = HOLD
