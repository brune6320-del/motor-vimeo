# Guía · A‑E(−1) v1.3 · un clic, a ciegas

El cuaderno v1.3 ejecuta exactamente lo prerregistrado y contraauditado por ChatGPT (carta 003):
178 llamadas y 210 máscaras. **No te enseña ningún resultado**, a propósito: la auditoría es ciega
y a doble llave, y nadie debe ver una máscara antes que las dos IAs.

---

## Modo A · Un clic en el navegador (≈ 5 minutos tuyos, cero decisiones)

1. Descarga el cuaderno que te adjunto: `PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_3.ipynb`.
2. En Colab: **Archivo → Subir cuaderno** → elige ese archivo. El título debe decir **«v1.3 … un clic»**.
3. **Entorno de ejecución → Cambiar tipo de entorno de ejecución → L4** (o A100) → **Guardar**.
4. Abre el panel **Archivos** (icono de carpeta, a la izquierda) y **arrastra `P1070614.JPG`** dentro.
   Espera a que aparezca en la lista.
5. **Entorno de ejecución → Ejecutar todas.** Si Colab avisa de que el cuaderno no es de Google,
   pulsa **Ejecutar de todos modos**.
6. Espera. Instalar SAM 2 y descargar el modelo (unos 900 MB) es lo que más tarda.
7. Al final se descarga `PRAGMA_AEM1v13_…_PENDING_EXTERNAL_AUDIT.zip`. Si la descarga no arranca:
   panel **Archivos → pragma_run →** clic derecho en el `.zip` → **Descargar**.
8. **Adjunta ese ZIP en el chat conmigo** (sesión de Claude Code).

**Tres reglas de la auditoría ciega:**

- **No le mandes el ZIP ni capturas de Colab a ChatGPT.**
- **No le cuentes cómo fue.** Lo único que recibirá es el paquete ciego que te prepararé.
- **No cambies nada del cuaderno.** Si lo cambias, deja de ser el prerregistrado.

**Si aparece algo en rojo:** no intentes arreglarlo. Copia el texto completo del error y pégamelo.

- `FAIL_FREEZE` significa que el commit de SAM 2 o el checkpoint no son los congelados, y el
  cuaderno se detuvo antes de generar nada. Es la protección funcionando.
- `FAIL_CONFIG` significa que la foto no da la luma registrada.

**`PENDING_EXTERNAL_AUDIT` no es un error.** Significa «terminó bien; falta la auditoría».

---

## Modo B · Me lo delegas con Colab CLI

El procedimiento es el mismo de la guía v1.2 (§ Modo B), con el cuaderno v1.3 y
`PRAGMA_HEADLESS=1`. Necesita que abras la red del entorno a `colab.research.google.com` y me
pegues un código de autorización de Google una vez.

---

## Qué pasa después

1. **Integridad:** verifico el ZIP sin abrir ninguna máscara. Compruebo bytes, hashes, que sea el
   prerregistro exacto, las 178 llamadas del plan, el congelado y que haya corrido en GPU.
2. **Paquete ciego:** preparo las láminas anónimas `C01…` y te lo doy.
3. **Envío a ChatGPT:** tú se lo mandas **solo, sin carta**.
4. **Mi llave:** juzgo a ciegas y en GitHub publico solo el hash de mis juicios.
5. **Desciegue:** cuando traigas los juicios de ChatGPT, desciego, comparo y escribo el veredicto.
   Si discrepamos, lo resolvemos nosotros con mediciones o con una tercera revisión; tú conservas
   el veto.

Nada derivado de la foto se sube a GitHub (el repositorio es público).
