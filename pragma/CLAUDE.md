# PRAGMA · reglas para agentes

- La fuente de verdad es `PROJECT_STATE.md`. Léelo antes de cambiar nada y actualízalo según su §29.
- **Cierra siempre cada respuesta con "Tus pasos"**: una lista numerada, explicada para alguien
  que no programa, con qué abrir, qué hacer clic, qué subir, qué decisión humana tomar y **qué
  adjuntar de vuelta en el chat** (archivos exactos, capturas, texto de errores). Si no hay nada
  que hacer, dilo explícitamente.
- Para ejecuciones en Colab, la guía vigente es `GUIA_COLAB_A-E-menos-1_v1_1.md`; mantenla al día.
- El repositorio es público: nunca versionar `inputs/*`, `local/`, `ae0/gt/` ni nada derivado de la
  foto (DEC‑017). Lo que el usuario adjunte en el chat se audita en local; al repo solo van hashes y
  conclusiones.
- Invariantes: no tocar `pragma-extension.zip`; no FastAPI, localhost, YOLO‑seg ni BiRefNet; Fase B
  bloqueada; ninguna verificación estática se presenta como corrida GPU ni como aceptación visual.
