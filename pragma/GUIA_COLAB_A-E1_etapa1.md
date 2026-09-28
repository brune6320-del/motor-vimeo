# Guía · A‑E1 etapa 1 · SAM 2 automático · un clic

> **Todavía NO se usa.** ChatGPT dejó la GPU en `HOLD` (respuestas 019 y 020). La 020 pidió dos
> parches, ya aplicados: la revisión exhaustiva de R1 y la compuerta de bfloat16. Falta que revise
> esta versión (carta 021, ORDEN 210) y dé el GO. Cuando llegue, esta guía dirá aquí «GO dado», con la
> carta y los hashes.

Protocolo: `ae1/AE1_STAGE1_READING_PROTOCOL.json`. Cuaderno: `outputs/PRAGMA_A-E1_etapa1_SAM2_AMG.ipynb`,
generado con `work/build_pragma_ae1_stage1.py` y verificado con `work/verify_pragma_ae1_stage1.py`.
Nunca se edita a mano.

El cuaderno ejecuta el generador automático de máscaras de SAM 2 con las **4 configuraciones
prerregistradas** sobre la foto y empaqueta todas las máscaras.

- **No te enseña ningún resultado:** el análisis es externo y está fijado antes.
- Esta etapa **nunca puede dar un «aprobado»**: solo puede detectar fallos claros pronto.

---

## Pasos (≈ 5 minutos tuyos, cero decisiones)

1. Descarga el cuaderno que te adjunto: `PRAGMA_A-E1_etapa1_SAM2_AMG.ipynb`.
2. En Colab: **Archivo → Subir cuaderno** → elige ese archivo. El título debe decir **«A‑E1 etapa 1»**.
3. **Entorno de ejecución → Cambiar tipo de entorno de ejecución → L4** → **Guardar**.
   - Tiene que ser **L4** (o A100/H100 si Colab te las ofrece). Con **T4** o sin GPU, la primera celda
     se detiene enseguida con `FAIL_ENVIRONMENT`, antes de instalar nada: vuelve a este paso, elige L4
     y repite el paso 5.
4. Abre el panel **Archivos** (icono de carpeta, a la izquierda) y **arrastra `P1070614.JPG`** dentro.
   Espera a que aparezca en la lista.
5. **Entorno de ejecución → Ejecutar todas.** Si Colab avisa de que el cuaderno no es de Google,
   pulsa **Ejecutar de todos modos**.
6. Espera. Instalar SAM 2 y descargar el modelo (unos 900 MB) lleva unos minutos, y las 4
   configuraciones otros tantos.
7. Al final se descarga `PRAGMA_AE1S1_…_PENDING_ANALYSIS.zip`.
   - Si la descarga no arranca: panel **Archivos → pragma_run →** clic derecho en el `.zip` →
     **Descargar**.
8. **Adjunta ese ZIP en el chat conmigo** (sesión de Claude Code). No se lo mandes a ChatGPT.

Si aparece un error en rojo, copia el texto completo y pégamelo. No cambies nada del cuaderno.

## Qué pasa después (lo hacen las IA)

1. Claude comprueba la integridad del ZIP sin mirar resultados.
2. Si algún objeto dispara el cribado de cajas (R1), Claude prepara un paquete ciego de triaje. Es lo
   único que recibe ChatGPT, sin carta. Si las dos IA no ven el objeto en él, sigue una revisión
   exhaustiva, también ciega, con todas las máscaras que tocan su caja. Te pediré llevar cada paquete.
3. Con las dos llaves, el lector calcula R2, R3 y R4 y decide la etapa: fallo del componente, o paso a
   la etapa 2.
