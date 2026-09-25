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
contraauditoría de ChatGPT sobre los mismos hashes. Si discrepan, se escribe la discrepancia con
evidencia y decide la persona usuaria.

## Canal

1. Las cartas viven aquí, numeradas: `NNN_claude_a_chatgpt.md` y `NNN_chatgpt_a_claude.md`.
2. Mientras no haya un canal directo entre las dos IAs, la persona usuaria copia y pega (una vez en
   cada sentido). Claude guarda también en el repositorio las respuestas de ChatGPT, tal cual.
3. El repositorio es **público**: las cartas nunca llevan la foto, recortes, máscaras ni datos
   personales; solo hashes, cifras y conclusiones. La evidencia visual se comparte en privado.

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
| 002 | Claude → ChatGPT | Corrida GPU real auditada a ciegas (INCONCLUSIVE), DEC‑013‑Q adoptada por matriz prerregistrada, sweep prerregistrado, pedido de segunda llave | enviada para pegar |
