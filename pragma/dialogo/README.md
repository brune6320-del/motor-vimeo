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
| — | (sin carta) | Paquete ciego de la corrida v1.4 `20260926T063238Z_67d41850`: 6 láminas N01–N06, `8f8df273…a17b`. Viaja solo | para enviar |
