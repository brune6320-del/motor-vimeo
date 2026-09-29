# PRAGMA — Inicio en ChatGPT 6 Sol

## Qué abrir

Usa la aplicación de ChatGPT. Si aparece **Work locally**, selecciónalo para trabajar con archivos locales; si no aparece, usa Work y adjunta el paquete manualmente. En el selector elige **6 Sol** y el razonamiento más alto disponible si esas opciones están visibles. Registra siempre las opciones reales y no afirmes que se usó 6 Sol si la interfaz muestra otro modelo.

## Qué adjuntar

Adjunta `PRAGMA_ChatGPT_6_Sol_Handoff.zip` y `PRAGMA_ChatGPT_6_Sol_Handoff.zip.sha256`. Si ChatGPT no puede leer el ZIP, descomprímelo y adjunta primero:

1. `PROJECT_STATE.md`;
2. `HANDOFF_MANIFEST_SHA256.txt`;
3. `inputs/P1070614.JPG`;
4. `outputs/PRAGMA_A-E-menos-1_diagnostico_caso_chica_Codex.ipynb`;
5. `outputs/PRAGMA_A-E-menos-1_Codex_verificacion.json`;
6. `outputs/PRAGMA-ESTADO-FASE-A-E-INVENTARIO-ESCENA.md`;
7. `outputs/PRAGMA-ESTADO-TRASPASO-CLAUDE-A-CODEX.md`;
8. `inputs/pragma-extension.zip` (solo como referencia; no modificar).

## Primer mensaje

```text
Estoy transfiriendo el proyecto PRAGMA desde Codex a ChatGPT 6 Sol.

Lee completamente PROJECT_STATE.md antes de proponer cambios. Después verifica HANDOFF_MANIFEST_SHA256.txt y todos los archivos adjuntos. Trata PROJECT_STATE.md como la fuente de verdad operativa, pero prioriza cualquier evidencia nueva y actualiza posteriormente el state file si existe una contradicción.

No confundas: diseño, código escrito, verificación estática, ejecución GPU y aceptación visual. Estado obligatorio de partida: v4 histórico = INCONCLUSIVE; A-E(−1) = 68/68 verificación estática y NOT_RUN; Fase B = BLOQUEADA; SAM 2 todavía no es rechazable. No modifiques pragma-extension.zip. No integres FastAPI, localhost, YOLO-seg ni BiRefNet.

En tu primera respuesta no escribas ni ejecutes cambios. Responde solo con:
1) archivos recibidos y hashes que pudiste verificar;
2) faltantes o contradicciones;
3) estado actual en cinco líneas;
4) la única próxima acción tomada de “Punto Exacto de Reanudación”.

Espera mi confirmación antes de continuar. Después guía la ejecución de PRAGMA_A-E-menos-1_diagnostico_caso_chica_Codex.ipynb en Colab. No reinicies el diseño ni reviertas decisiones cerradas sin evidencia técnica nueva.
```

## Después de que confirme la lectura

Responde:

```text
Confirmo el estado. Continúa con la ejecución A‑E(−1) en Colab paso a paso. Detente en cada decisión humana: confirmar overlay, elegir semillas, elegir candidata y completar revisión. No declares PASS basándote solo en el texto del notebook; al terminar audita el ZIP y las capturas.
```

## Resultado que debes conservar

- `.ipynb` ejecutado;
- ZIP generado por A‑E(−1);
- cualquier traceback completo;
- capturas si las coordenadas o máscaras se ven incorrectas.

Después de auditar A‑E(−1), el siguiente trabajo es A‑E0. No Fase B.
