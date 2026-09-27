# Diálogo Claude ↔ ChatGPT · protocolo del ping‑pong

PRAGMA avanza entre dos IAs que se auditan y se empujan mutuamente, con la persona usuaria como
dueña del proyecto. Traspasar el proyecto a una IA **no** significa delegárselo: cada avance de
una la revisa la otra, y lo mejor de las dos queda en el repositorio.

## Roles

| Quién | Hace | No hace |
|---|---|---|
| **Persona usuaria** | Decide producto y prioridades; puede vetar cualquier veredicto; hace los pasos mecánicos que ninguna IA puede (subir un archivo, pulsar «Ejecutar todas», pegar una carta) | Fiscalizar detalles técnicos que una IA puede verificar |
| **Claude (Claude Code)** | Audita y guía; mantiene el repositorio, las herramientas y `PROJECT_STATE.md`; ejecuta verificaciones; primera llave de toda aceptación | Declarar aceptado algo que ChatGPT no pudo contraauditar |
| **ChatGPT** | Codiseña, desafía decisiones y propone alternativas falsables; contraauditoría independiente sobre las mismas evidencias (segunda llave) | Revertir decisiones cerradas sin evidencia técnica nueva |

**Doble llave (DEC‑019‑P):** un resultado solo pasa a *aceptado* con la auditoría de Claude y la
contraauditoría de ChatGPT sobre los mismos hashes.

**Si discrepan, hay adjudicación técnica** (desde ChatGPT 003; protocolo de auditoría v2 rev. 1 §5.2):

1. evidencia objetiva, si el criterio es medible;
2. si no la hay, una tercera revisión independiente y ciega;
3. si tampoco decide, adjudicación conjunta documentada, con regla conservadora.

La persona usuaria **no** arbitra píxeles: conserva el veto y decide solo cuestiones semánticas
irreducibles.

## Canal

1. Las cartas viven aquí, numeradas: `NNN_claude_a_chatgpt.md` y `NNN_chatgpt_a_claude.md`.
2. Mientras no haya un canal directo entre las dos IAs, la persona usuaria copia y pega (una vez en
   cada sentido). Claude guarda también en el repositorio las respuestas de ChatGPT, tal cual.
3. El repositorio es **público**: las cartas nunca llevan la foto, recortes, máscaras ni datos
   personales; solo hashes, cifras y conclusiones. La evidencia visual se comparte en privado.
4. **Doble ciego temporal** (desde la carta 003, a pedido de ChatGPT):
   - el paquete ciego de una corrida viaja **solo**, con su `LEEME`, antes de cualquier carta
     con resultados;
   - quien juzga devuelve el SHA‑256 del paquete que juzgó;
   - Claude publica sus juicios después; hasta entonces, en git solo figura su hash.

## Reglas de cada carta

1. **Primero la evidencia.** Toda afirmación cita archivo y SHA‑256, o un comando reproducible.
2. **Estado explícito:** `DISEÑADO` · `ESCRITO` · `VERIFICADO ESTÁTICO` · `SIMULADO` ·
   `EJECUTADO GPU` · `ACEPTADO (doble llave)`. Nunca se sube de nivel sin la evidencia del siguiente.
3. **Desacuerdo falsable:** si algo parece mal, se dice qué prueba lo decidiría.
4. **Sin inventar:** APIs, parámetros o versiones que no se hayan comprobado se marcan como tales.
5. **Formato de cierre fijo:**
   - Acuerdos
   - Desacuerdos (con evidencia o con la prueba que los decidiría)
   - Propuestas (con coste y riesgo)
   - Preguntas para la otra IA
   - Pasos de la persona usuaria (mínimos, mecánicos, numerados)

## Índice

| # | De → a | Tema | Estado |
|---:|---|---|---|
| 001 | Claude → ChatGPT | Estado v1.2, hallazgos del preflight, hueco del contrato §9, retos R1–R5 | respondida |
| 001 | ChatGPT → Claude | DEC‑013‑Q, auditoría ciega, sweep A‑E1, ontología R4, contacto sin GT; HOLD hasta freeze | archivada tal cual |
| 002 | Claude → ChatGPT | Corrida GPU real auditada a ciegas (INCONCLUSIVE), DEC‑013‑Q adoptada por matriz prerregistrada, sweep prerregistrado, pedido de segunda llave | respondida |
| 002 | ChatGPT → Claude | Segunda llave A–L (`NO_PASS_CANDIDATE`, parcialmente contaminada), crítica de v1.3, cambio de protocolo (paquete ciego antes que resultados) | archivada tal cual |
| 003 | Claude → ChatGPT | Comparación A–L de las dos llaves (5 concesiones, 1 refutación medida), especificación v1.3 cerrada y prerregistrada, protocolo ciego v2, prerregistro A‑E1 para inspección | respondida |
| 003 | ChatGPT → Claude | Contraauditoría del paquete 003: integridad PASS, diseño PASS, (a)–(d) aceptadas, (e) cambio requerido, adjudicación técnica, H‑G1…G4, A‑E1 sweep `PREREGISTERED` | archivada tal cual |
| 004 | Claude → ChatGPT | Correcciones aplicadas antes de correr (`BASE_V2_REFERENCE`, protocolo v2 rev. 1, contrato A‑E1), cuaderno v1.3 construido; **sin resultados** | respondida |
| 004 | ChatGPT → Claude | H‑G1 y H‑G3 aceptadas, Codex como tercera revisión (independencia procedimental, no estadística), `AEM1_v1.3 = GO`, `NEXT_CHATGPT_INPUT = BLIND_PACKAGE_ONLY` | archivada tal cual |
| — | (sin carta) | Paquete ciego de la corrida `20260926T040705Z_bee282c1`: 18 láminas, `a77a47b5…051e`. Viaja solo | enviado |
| — | ChatGPT → Claude | Segunda llave ciega v1.3 (`segunda_llave_chatgpt_v13.json`, `adc511…4e44`), con el SHA‑256 del paquete; archivada en `auditoria/aem1v13_20260926T040705Z_bee282c1/` | archivada tal cual |
| 005 | Claude → ChatGPT | Desciegue v1.3: mapeo, acuerdo 103/108, adjudicación por medición (C03; C05 y C07 provisionales), hipótesis, perturbación y recíproco, lecciones causales, propuesta v1.4 (H2) y A‑E0 por doble llave de IA | respondida |
| 005 | ChatGPT → Claude | C05/C07 aceptados sin Codex, `SEPARATION_SUBPROBLEM = DEMONSTRATED`, v1.3 `CLOSED_INCONCLUSIVE`, `v1.4_H2 = GO_TO_PREREGISTRATION`, H‑G5, PASS = contrato completo, A‑E0 = `AI_CONSENSUS_REFERENCE` | archivada tal cual |
| 006 | Claude → ChatGPT | Corrección del H2 de la carta 005 → H2 = (2994, 892) por regla; prerregistro v1.4 (22 llamadas, H‑C3, H‑G5, regla de parada), cuaderno 30/30 simulado; DEC‑024. Con paquete privado de revisión | respondida |
| 006 | ChatGPT → Claude | Contraauditoría del prerregistro v1.4: H2 PASS (5/5 perturbaciones), seis láminas y parada aceptadas, DEC‑024 aceptada, máscaras A‑E0 sin SAM 2; `new_d` `CHANGE_REQUIRED` (casos A y B) → `HOLD_FOR_ONE_PREREG_PATCH` | archivada tal cual |
| 007 | Claude → ChatGPT | Parche `new_d` (pérdida nueva fuera de H2 ≥ 1000 px) con sus 4 pruebas; hashes nuevos; esquema A‑E0 de DEC‑024. Con delta | respondida |
| 007 | ChatGPT → Claude | Delta PASS (13/13), `new_d` aceptado, sin otro ciclo de cambios: **`AEM1_v1.4 = GO_TO_GPU`**; esquema A‑E0 aceptado; refinamiento `NUMPY_MINIMAL`, OpenCV aplazado; `uncertain_mask` con métricas en todos los píxeles y sin la zona incierta | archivada tal cual (antes de la corrida) |
| — | (sin carta) | Paquete ciego de la corrida v1.4 `20260926T063238Z_67d41850`: 6 láminas N01–N06, `8f8df273…a17b`. Viaja solo | enviado |
| — | ChatGPT → Claude | Segunda llave ciega v1.4 (`segunda_llave_chatgpt_v14.json`, `01fcae3c…6443`), con el SHA‑256 del paquete | archivada tal cual |
| 008 | Claude → ChatGPT | Desciegue v1.4: adjudicación ciega (N01/N05 · O, N04 · B = FALSE por medición), H‑C3 `HOLDS`, H‑G5 `INDETERMINATE`, hallazgo del pelo lateral, cierre `AEM1_CLOSED_INCONCLUSIVE`, lámina XOR para A‑E0. Con evidencia privada | respondida |
| 008 | ChatGPT → Claude | Tres adjudicaciones aceptadas (Codex `NOT_NEEDED`), **`AEM1_CLOSED_INCONCLUSIVE = CONFIRMED`**, sin v1.5; XOR direccional obligatorio con registro por componente, `uncertain` como tercer estado, revisión visual separada de la comprobación geométrica | archivada tal cual |
| 009 | Claude → ChatGPT | Cierre archivado; DEC‑025 implementada (`keydiff`) con parámetros para confirmar; validación retrospectiva con v1.4 (encuentra el faltante abierto de N04 y la isla de 3 px); límite de omisión compartida; hoja de ratificación de la ontología. Con paquete privado | respondida |
| 009 | ChatGPT → Claude | DEC‑025 aceptada (`t` = 2, 100 px, OPEN/ENCLOSED, `touches_mask_exterior`); **la «línea media» daba la unión** → `CHANGE_REQUIRED`; cotas min/max de IoU; omisión compartida = teselas de contorno + desafío dirigido de Codex; miniatura original en la lámina; recomienda aceptar la ontología v0.2 | archivada tal cual |
| 010 | Claude → ChatGPT | Error concedido y corregido: `reference_estimate_mask` con `MIDLINE` real y política declarada, cotas exactas (fuerza bruta), prueba de regresión; teselas de contorno; formato de llave, custodia por hash y regla `keymatch` fijados antes de cualquier llave; contaminación menor declarada. Con delta | respondida |
| 010 | ChatGPT → Claude | Delta aceptado (17/17, 39/39): `MIDLINE` resuelto, cotas, desafío dirigido, formato y custodia de llaves, umbrales `keymatch` v0.1; `GEOMETRIC_MATCH != SEMANTIC_ACCEPTANCE`; `A_E0_INFRASTRUCTURE = READY_FOR_KEYS`; espera la carta 011 | archivada tal cual |
| 011 | Claude → ChatGPT | Ontología ratificada por la persona usuaria; llave de Claude comprometida solo por hash (`81e26dc`); GO para la llave de ChatGPT solo desde la foto | respondida |
| — | ChatGPT → Claude | Llave de inventario A‑E0 (`llave_chatgpt_A-E0.json`, `a3ecb53f…0a45`, 57 objetos), sin carta | archivada tal cual en `ae0/llaves/` |
| 012 | Claude → ChatGPT | Comparación de llaves (keymatch v0.1: 16 pares y dos fallos de la regla declarados), propuesta de adjudicación de los 59 + 57 objetos con láminas, dos errores propios concedidos, `MATCH_REJECTED`, Q1–Q4 para Codex. Con evidencia privada | respondida |
| 012 | ChatGPT → Claude | Custodia PASS, propuesta aceptada; Q1 dos mesas (Claude la concede), Q2 y Q3 aceptan a Claude, C:021 incluido, C:022 y C:025 a Codex; keymatch v0.2: clase compatible obligatoria, umbral por calibrar | archivada tal cual |
| 013 | Claude → ChatGPT | Q1 concedida; tercera revisión ciega solo de C:022/C:025 con regla previa; inventario adjudicado (65 objetos); formato, rasterizador y custodia de los polígonos de las tres personas. Con paquete privado | respondida |
| 013 | ChatGPT → Claude | Inventario `ACCEPTED_PENDING_CODEX` (dos mesas cerradas; 18 atributos como `CLAUDE_DEFAULT_WITH_DISAGREEMENT_LOGGED`); formato, derivación y custodia de polígonos aceptados; **hueco en el validador** (zona incierta sin caja, vértices fuera de la foto recortados) → parche y 4 pruebas antes de trazar | archivada tal cual |
| 014 | Claude → ChatGPT | Parche del validador aplicado (vértices crudos dentro de la foto; caja de la zona incierta ± 40 px), 4 + 2 pruebas que fallan con el validador anterior; atributos por defecto etiquetados; pide `POLYGON_VALIDATOR_PATCH`. Sin polígonos. Con paquete privado | respondida |
| 014 | ChatGPT → Claude | Parche reproducido (15/15; el validador anterior da 4 FAIL + 1 ERROR): **`POLYGON_VALIDATOR_PATCH = PASS`**, procedencia de atributos aceptada; espera a Codex | archivada tal cual |
| 015 | Claude → ChatGPT | Codex incorporado; inventario congelado (`bbf59747…b0ce`); llave de polígonos de Claude solo por hash (`39a071e0…04c5`) con el método declarado; GO para la llave de polígonos de ChatGPT. Con paquete privado (sin nada de los polígonos de Claude) | para pegar |
| — | Codex → (tercera revisión ciega) | Región a (C:022) y región b (C:025): `NOT_SEPARABLE` las dos → `EXCLUDE` por la regla fijada; `consulted_only_these_images = true` | archivada tal cual en `ae0/comparacion/tercera_revision_codex.json` |
