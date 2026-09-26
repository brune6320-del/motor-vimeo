# Guía · A‑E(−1) v1.4 · un clic, a ciegas

> **Todavía no se ejecuta.** ChatGPT revisa el prerregistro v1.4 antes de la corrida (carta 006).
> Esta guía vale cuando su respuesta diga `GO`. Si pide cambios, el cuaderno se regenera y esta guía
> se actualiza.

El cuaderno v1.4 hace **una sola intervención** sobre la mejor cadena de v1.3: añade el punto H2 en
la franja de pelo entre la cara y el índice. Son 22 llamadas y 24 máscaras, unos segundos de GPU.
**No te enseña ningún resultado**: la auditoría es ciega y a doble llave.

---

## Modo A · Un clic en el navegador (≈ 5 minutos tuyos, cero decisiones)

1. Descarga el cuaderno que te adjunto: `PRAGMA_A-E-menos-1_diagnostico_caso_chica_v1_4.ipynb`.
2. En Colab: **Archivo → Subir cuaderno** → elige ese archivo. El título debe decir **«v1.4 — una
   sola intervención (H2)»**.
3. **Entorno de ejecución → Cambiar tipo de entorno de ejecución → L4** → **Guardar**.
   - **Tiene que ser L4.** La referencia debe salir idéntica bit a bit a v1.3, y eso solo está
     probado en L4.
   - Si no hay L4 disponible, espera o avísame; no uses otra.
4. Abre el panel **Archivos** (icono de carpeta, a la izquierda) y **arrastra `P1070614.JPG`** dentro.
   Espera a que aparezca en la lista.
5. **Entorno de ejecución → Ejecutar todas.** Si Colab avisa de que el cuaderno no es de Google,
   pulsa **Ejecutar de todos modos**.
6. Espera. Instalar SAM 2 y descargar el modelo (unos 900 MB) es lo que más tarda.
7. Al final se descarga `PRAGMA_AEM1v14_…_PENDING_EXTERNAL_AUDIT.zip`.
   - Si la descarga no arranca: panel **Archivos → pragma_run →** clic derecho en el `.zip` →
     **Descargar**.
8. **Adjunta ese ZIP en el chat conmigo** (sesión de Claude Code).

**Tres reglas de la auditoría ciega:**

- **No le mandes el ZIP ni capturas de Colab a ChatGPT.**
- **No le cuentes cómo fue.** Lo único que recibirá es el paquete ciego que te prepararé.
- **No cambies nada del cuaderno.** Si lo cambias, deja de ser el prerregistrado.

**Si aparece algo en rojo:** no intentes arreglarlo. Copia el texto completo del error y pégamelo.

- `FAIL_FREEZE` significa que el commit de SAM 2 o el checkpoint no son los congelados.
- `FAIL_CONFIG` significa que la foto no da la luma registrada.

**`PENDING_EXTERNAL_AUDIT` no es un error.** Significa «terminó bien; falta la auditoría».

---

## Qué pasa después

1. **Integridad:** verifico el ZIP sin abrir ninguna máscara.
2. **Referencia:** compruebo que la referencia salió bit a bit igual a v1.3. Solo miro hashes.
3. **Paquete ciego:** preparo 6 láminas anónimas, `N01…N06`, y te lo doy.
4. **Envío a ChatGPT:** tú se lo mandas **solo, sin carta**.
5. **Mi llave:** juzgo a ciegas y en GitHub publico solo el hash de mis juicios.
6. **Desciegue:** cuando traigas los juicios de ChatGPT, desciego, comparo y escribo el veredicto.
7. **Cierre:** con v1.4, A‑E(−1) termina, pase lo que pase (regla de parada prerregistrada).

Nada derivado de la foto se sube a GitHub (el repositorio es público).
