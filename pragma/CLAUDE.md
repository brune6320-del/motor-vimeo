# PRAGMA · reglas para agentes

- La fuente de verdad es `PROJECT_STATE.md`. Léelo antes de cambiar nada y actualízalo según su §29.
- **Cierra siempre cada respuesta con "Tus pasos"**: una lista numerada, explicada para alguien
  que no programa, con qué abrir, qué hacer clic, qué subir y **qué adjuntar de vuelta en el chat**
  (archivos exactos, capturas, texto de errores). Si no hay nada que hacer, dilo explícitamente.
- **La persona usuaria no fiscaliza (DEC‑018‑P).** Toda verificación que una IA pueda hacer la hace
  la IA, con evidencia y hashes: coordenadas, integridad de ZIPs, revisión visual de máscaras. A la
  persona solo se le piden pasos mecánicos y decisiones de producto; siempre puede vetar.
- **Ping‑pong con ChatGPT (DEC‑019‑P).** Tras cada avance significativo, escribe una carta
  `dialogo/NNN_claude_a_chatgpt.md` según `dialogo/README.md` y entrégala lista para pegar. Guarda las
  respuestas de ChatGPT tal cual como `dialogo/NNN_chatgpt_a_claude.md`, audítalas y respóndelas.
  Traspasar no es delegar: Claude audita y guía; ChatGPT desafía y contraaudita (doble llave).
- **Auditoría ciega con reglas previas** (protocolo vigente: `auditoria/PROTOCOLO_AUDITORIA_AEM1_v2.md`).
  - Antes de la corrida, congelar y publicar el protocolo y el prerregistro.
  - Juzgar con etiquetas anónimas.
  - **El paquete ciego va a ChatGPT antes que cualquier resultado:** ninguna carta previa dice si
    algo pasó, cuántas fallan, qué familia hizo qué ni cuál fue la mejor.
  - Los juicios crudos de Claude se comprometen en git **solo por SHA‑256**. El JSON se publica
    después de archivar la segunda llave; después se desciega (`work/blind_audit_aem1.py`,
    `work/double_key_aem1.py`).
  - Toda regla métrica nueva se decide con una prueba prerregistrada antes de ver datos reales.
- Para Colab, la guía vigente es `GUIA_COLAB_A-E-menos-1_v1_4.md` (un clic en L4, a ciegas; solo tras
  el `GO` de ChatGPT). Mantenla al día. El cuaderno v1.4 se genera desde el prerregistro con
  `work/build_pragma_aem1_v1_4.py`. Nunca se edita a mano, y se verifica con
  `work/verify_pragma_aem1_v1_4.py`. El prerregistro sale de `work/design_aem1_v1_4.py --check`.
- **Discrepancias entre llaves → adjudicación técnica** (protocolo v2 rev. 1 §5.2): primero la
  medición; si no basta, una tercera revisión ciega; si tampoco, adjudicación conjunta con regla
  conservadora. Nunca se pide a la persona usuaria arbitrar píxeles.
- Tras una corrida v1.4: `aem1_v14_audit.integrity` sin mirar resultados → referencia bit a bit (solo
  hashes) → paquete ciego de 6 láminas (va **solo** a ChatGPT) → juicio ciego propio, del que a git va
  solo el hash → desciegue y `aem1_v14_audit.analyze` cuando llegue la segunda llave. A‑E(−1) se
  cierra con v1.4 (regla de parada prerregistrada).
- A‑E0 se produce por doble llave de IA (DEC‑024): su referencia es `AI_CONSENSUS_REFERENCE`, nunca
  `HUMAN_GT`, y A‑E1 declara contra qué referencia mide.
- Nomenclatura de la persona usuaria: «Crear cuaderno Colab para SAM 2» es el hilo de **Codex** de
  PRAGMA/SAM 2. Las cartas para Claude se pegan en su sesión de Claude Code.
- El repositorio es público: nunca versionar `inputs/*`, `local/`, `ae0/gt/` ni nada derivado de la
  foto (DEC‑017). Lo que el usuario adjunte en el chat se audita en local; al repo solo van hashes y
  conclusiones.
- Invariantes: no tocar `pragma-extension.zip`; no FastAPI, localhost, YOLO‑seg ni BiRefNet; Fase B
  bloqueada; ninguna verificación estática o simulada se presenta como corrida GPU ni como aceptación.
