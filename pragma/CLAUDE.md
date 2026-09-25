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
- **Auditoría ciega con reglas previas.** Antes de mirar resultados de una corrida real: congelar y
  publicar el protocolo (criterios, reglas de decisión); juzgar con etiquetas anónimas; publicar los
  juicios crudos antes de desciegar (`work/blind_audit_aem1.py`). Toda regla métrica nueva se decide
  con una prueba prerregistrada antes de ver datos reales.
- Para Colab, la guía vigente es `GUIA_COLAB_A-E-menos-1_v1_2.md` (modo un clic o modo delegado con
  Colab CLI). Mantenla al día.
- El repositorio es público: nunca versionar `inputs/*`, `local/`, `ae0/gt/` ni nada derivado de la
  foto (DEC‑017). Lo que el usuario adjunte en el chat se audita en local; al repo solo van hashes y
  conclusiones.
- Invariantes: no tocar `pragma-extension.zip`; no FastAPI, localhost, YOLO‑seg ni BiRefNet; Fase B
  bloqueada; ninguna verificación estática o simulada se presenta como corrida GPU ni como aceptación.
